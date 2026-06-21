"""Briefing computations over the SQLite graph.

All four briefings are plain SQL aggregates over `relations` joined to `norms`. Results
are never hard-coded. Each briefing also exposes a Cytoscape-friendly subgraph.

Scope:
  - "state": norms whose scope (ambito) is "Estatal" (the default).
  - "all":   the whole corpus.
Missing/inconsistent scope fields never crash a query; they are simply excluded from
the state scope.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import text

from app.core.config import DEFAULT_SCOPE, LEY_30_1992_ID, STATE_SCOPE_LABEL
from app.db.session import session_scope

BRIEFING_KEYS = (
    "unreadable-laws",
    "omnibus-laws",
    "dead-law-dependencies",
    "ley-30-1992-blast-radius",
)

# Viz subgraphs: cap edges per hub so Cytoscape layouts stay readable (tables keep full data).
GRAPH_VIZ_MAX_EDGES_PER_HUB = 30

NORM_FIELDS = [
    "id",
    "title",
    "official_number",
    "rank",
    "rank_code",
    "scope",
    "department",
    "publication_date",
    "disposition_date",
    "effective_date",
    "repeal_date",
    "annulment_date",
    "lifecycle_status",
    "is_live",
    "is_repealed",
    "url_eli",
    "url_html",
]


def _limit_edges_per_hub(
    rows: Sequence[Any],
    hub_fn,
    max_per_hub: int = GRAPH_VIZ_MAX_EDGES_PER_HUB,
) -> List[Any]:
    """Keep at most N edges per hub node so briefing graphs remain legible."""
    buckets: Dict[str, List[Any]] = {}
    for r in rows:
        hub = hub_fn(r)
        buckets.setdefault(hub, []).append(r)
    out: List[Any] = []
    for items in buckets.values():
        out.extend(items[:max_per_hub])
    return out


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scope_clause(alias: str, scope: str) -> str:
    """Return an extra AND clause for the given scope (no user input interpolated)."""
    if scope == "all":
        return ""
    return f" AND {alias}.scope = :scope_label"


def _scope_params(scope: str) -> Dict[str, Any]:
    return {} if scope == "all" else {"scope_label": STATE_SCOPE_LABEL}


def _norm_dict(row: Any) -> Dict[str, Any]:
    d = {k: row._mapping.get(k) for k in NORM_FIELDS if k in row._mapping}
    if "is_live" in d:
        d["is_live"] = bool(d["is_live"])
    if "is_repealed" in d:
        d["is_repealed"] = bool(d["is_repealed"])
    return d


def _fetch_norms_map(conn, ids: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    ids = list({i for i in ids if i})
    if not ids:
        return {}
    placeholders = ",".join(f":id{i}" for i in range(len(ids)))
    params = {f"id{i}": v for i, v in enumerate(ids)}
    rows = conn.execute(
        text(
            f"SELECT {', '.join(NORM_FIELDS)} FROM norms WHERE id IN ({placeholders})"
        ),
        params,
    ).fetchall()
    return {r._mapping["id"]: _norm_dict(r) for r in rows}


def _node(
    norm: Optional[Dict[str, Any]],
    norm_id: str,
    metrics: Optional[dict] = None,
    hub: bool = False,
) -> dict:
    base_metrics = metrics or {}
    if hub:
        base_metrics = {**base_metrics, "is_hub": True}
    if norm:
        data = {
            "id": norm["id"],
            "label": _short_label(norm),
            "title": norm.get("title"),
            "lifecycle_status": norm.get("lifecycle_status"),
            "rank": norm.get("rank"),
            "url_html": norm.get("url_html"),
            "is_live": norm.get("is_live"),
            "is_hub": hub,
            "metrics": base_metrics or {},
        }
    else:
        # Target/source not present in our DB (e.g. partial sample ingestion).
        data = {
            "id": norm_id,
            "label": norm_id,
            "title": None,
            "lifecycle_status": "UNKNOWN",
            "rank": None,
            "url_html": None,
            "is_live": None,
            "is_hub": hub,
            "metrics": base_metrics or {},
        }
    return {"data": data}


def _short_label(norm: Dict[str, Any]) -> str:
    num = norm.get("official_number")
    rank = norm.get("rank") or ""
    if num:
        return f"{rank} {num}".strip()
    title = norm.get("title") or norm["id"]
    return title[:40] + ("…" if len(title) > 40 else "")


def _edge(row: Any) -> dict:
    m = row._mapping
    return {
        "data": {
            "id": f"e{m['id']}",
            "source": m["source_norm_id"],
            "target": m["target_norm_id"],
            "relation_type": m["relation_type"],
            "relation_label_raw": m.get("relation_label_raw"),
            "relation_detail_raw": m.get("relation_detail_raw"),
        }
    }


_RELATION_ROW_FIELDS = (
    "id, source_norm_id, target_norm_id, relation_type, relation_label_raw, "
    "relation_detail_raw, api_direction"
)


def _dedupe_relation_rows(rows: Sequence[Any]) -> tuple[List[Any], int]:
    """Collapse anteriores/posteriores mirror pairs to one row per logical edge."""
    seen: Dict[tuple, Any] = {}
    order: List[tuple] = []
    for r in rows:
        m = r._mapping
        key = (m["source_norm_id"], m["target_norm_id"], m["relation_type"])
        if key in seen:
            prev = seen[key]._mapping
            if prev.get("api_direction") == "posteriores" and m.get("api_direction") == "anteriores":
                seen[key] = r
            continue
        seen[key] = r
        order.append(key)
    deduped = [seen[k] for k in order]
    return deduped, len(rows) - len(deduped)


def build_neighborhood(
    conn,
    norm_id: str,
    *,
    relation_type: Optional[str] = None,
    direction: str = "all",
    limit: int = 120,
) -> Dict[str, Any]:
    """Ego-network around a norm: balanced in/out fetch, mirror-edge dedupe, focus marked as hub."""
    exists = conn.execute(
        text("SELECT 1 FROM norms WHERE id = :id"), {"id": norm_id}
    ).fetchone()
    if not exists:
        return {"error": "not_found"}

    type_clause = ""
    params: Dict[str, Any] = {"id": norm_id}
    if relation_type:
        type_clause = " AND relation_type = :rtype"
        params["rtype"] = relation_type.upper()

    def _count(where_col: str) -> int:
        return (
            conn.execute(
                text(
                    f"SELECT COUNT(*) FROM relations WHERE {where_col} = :id{type_clause}"
                ),
                params,
            ).scalar()
            or 0
        )

    total_in = _count("target_norm_id")
    total_out = _count("source_norm_id")

    half = max(limit // 2, 1)
    fetch_limit = limit
    if direction == "all":
        fetch_limit = half

    def _fetch(where_col: str, lim: int) -> List[Any]:
        return list(
            conn.execute(
                text(
                    f"SELECT {_RELATION_ROW_FIELDS} FROM relations "
                    f"WHERE {where_col} = :id{type_clause} ORDER BY id LIMIT :lim"
                ),
                {**params, "lim": lim},
            ).fetchall()
        )

    raw_rows: List[Any] = []
    truncated = False
    in_rows: List[Any] = []
    out_rows: List[Any] = []
    if direction in ("all", "incoming"):
        in_rows = _fetch("target_norm_id", fetch_limit if direction == "incoming" else half)
        raw_rows.extend(in_rows)
        if direction == "incoming" and len(in_rows) >= fetch_limit and total_in > fetch_limit:
            truncated = True
    if direction in ("all", "outgoing"):
        out_rows = _fetch("source_norm_id", fetch_limit if direction == "outgoing" else half)
        raw_rows.extend(out_rows)
        if direction == "outgoing" and len(out_rows) >= fetch_limit and total_out > fetch_limit:
            truncated = True
    if direction == "all":
        truncated = (total_in > half and len(in_rows) >= half) or (total_out > half and len(out_rows) >= half)

    rows, deduped_count = _dedupe_relation_rows(raw_rows)
    node_ids = {norm_id}
    for r in rows:
        node_ids.add(r._mapping["source_norm_id"])
        node_ids.add(r._mapping["target_norm_id"])

    norms_map = _fetch_norms_map(conn, list(node_ids))
    nodes = [_node(norms_map.get(nid), nid, hub=(nid == norm_id)) for nid in node_ids]
    edges = [_edge(r) for r in rows]

    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "focus_id": norm_id,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "incoming_total": total_in,
            "outgoing_total": total_out,
            "edges_deduplicated": deduped_count,
            "truncated": truncated,
            "direction": direction,
            "limit": limit,
        },
    }


# --- Briefing 1: unreadable laws --------------------------------------------


def compute_unreadable(conn, scope: str = DEFAULT_SCOPE, limit: int = 5) -> Dict[str, Any]:
    sql = text(
        "SELECT n.id AS norm_id, COUNT(DISTINCT r.source_norm_id) AS amending_count "
        "FROM relations r JOIN norms n ON n.id = r.target_norm_id "
        "WHERE r.relation_type = 'AMENDS'" + _scope_clause("n", scope) + " "
        "GROUP BY n.id ORDER BY amending_count DESC, n.id LIMIT :limit"
    )
    params = {"limit": limit, **_scope_params(scope)}
    rows = conn.execute(sql, params).fetchall()
    ids = [r._mapping["norm_id"] for r in rows]
    norms_map = _fetch_norms_map(conn, ids)
    items = []
    for rank, r in enumerate(rows, start=1):
        nid = r._mapping["norm_id"]
        item = dict(norms_map.get(nid, {"id": nid}))
        item["rank_position"] = rank
        item["amending_count"] = r._mapping["amending_count"]
        items.append(item)
    return {"briefing": "unreadable-laws", "scope": scope, "items": items}


# --- Briefing 2: omnibus laws -----------------------------------------------


def compute_omnibus(conn, scope: str = DEFAULT_SCOPE, limit: int = 5) -> Dict[str, Any]:
    sql = text(
        "SELECT n.id AS norm_id, COUNT(DISTINCT r.target_norm_id) AS target_count "
        "FROM relations r JOIN norms n ON n.id = r.source_norm_id "
        "WHERE r.relation_type = 'AMENDS'" + _scope_clause("n", scope) + " "
        "GROUP BY n.id ORDER BY target_count DESC, n.id LIMIT :limit"
    )
    params = {"limit": limit, **_scope_params(scope)}
    rows = conn.execute(sql, params).fetchall()
    ids = [r._mapping["norm_id"] for r in rows]
    norms_map = _fetch_norms_map(conn, ids)
    items = []
    for rank, r in enumerate(rows, start=1):
        nid = r._mapping["norm_id"]
        item = dict(norms_map.get(nid, {"id": nid}))
        item["rank_position"] = rank
        target_count = r._mapping["target_count"]
        subject_diversity = _subject_diversity(conn, nid)
        item["target_count"] = target_count
        item["subject_diversity"] = subject_diversity
        # Secondary indicators (ranking stays by target_count).
        item["department_diversity"] = _department_diversity(conn, nid)
        item["omnibus_score"] = round(target_count * math.log(1 + subject_diversity), 2)
        items.append(item)
    return {"briefing": "omnibus-laws", "scope": scope, "items": items}


def _subject_diversity(conn, norm_id: str) -> int:
    """Optional extra: number of distinct subjects across the norms this one amends."""
    sql = text(
        "SELECT COUNT(DISTINCT ns.subject_code) FROM relations r "
        "JOIN norm_subjects ns ON ns.norm_id = r.target_norm_id "
        "WHERE r.source_norm_id = :sid AND r.relation_type = 'AMENDS'"
    )
    return conn.execute(sql, {"sid": norm_id}).scalar() or 0


def _department_diversity(conn, norm_id: str) -> int:
    """Secondary indicator: distinct departments across the norms this one amends."""
    sql = text(
        "SELECT COUNT(DISTINCT t.department) FROM relations r "
        "JOIN norms t ON t.id = r.target_norm_id "
        "WHERE r.source_norm_id = :sid AND r.relation_type = 'AMENDS' "
        "AND t.department IS NOT NULL AND t.department != ''"
    )
    return conn.execute(sql, {"sid": norm_id}).scalar() or 0


# --- Briefing 3: dead-law dependencies --------------------------------------


def compute_dead_law(conn, scope: str = DEFAULT_SCOPE, limit: int = 5) -> Dict[str, Any]:
    sp = _scope_params(scope)

    denom = conn.execute(
        text(
            "SELECT COUNT(*) FROM norms n WHERE n.is_live = 1" + _scope_clause("n", scope)
        ),
        sp,
    ).scalar() or 0

    numer = conn.execute(
        text(
            "SELECT COUNT(DISTINCT r.source_norm_id) FROM relations r "
            "JOIN norms s ON s.id = r.source_norm_id "
            "JOIN norms t ON t.id = r.target_norm_id "
            "WHERE r.relation_type = 'CITES' AND s.is_live = 1 AND t.is_repealed = 1"
            + _scope_clause("s", scope)
        ),
        sp,
    ).scalar() or 0

    ghosts = conn.execute(
        text(
            "SELECT t.id AS norm_id, COUNT(DISTINCT r.source_norm_id) AS live_citers "
            "FROM relations r "
            "JOIN norms s ON s.id = r.source_norm_id "
            "JOIN norms t ON t.id = r.target_norm_id "
            "WHERE r.relation_type = 'CITES' AND s.is_live = 1 AND t.is_repealed = 1"
            + _scope_clause("s", scope)
            + " GROUP BY t.id ORDER BY live_citers DESC, t.id LIMIT :limit"
        ),
        {"limit": limit, **sp},
    ).fetchall()

    ids = [g._mapping["norm_id"] for g in ghosts]
    norms_map = _fetch_norms_map(conn, ids)
    top_ghost_norms = []
    for rank, g in enumerate(ghosts, start=1):
        nid = g._mapping["norm_id"]
        item = dict(norms_map.get(nid, {"id": nid}))
        item["rank_position"] = rank
        item["live_citers"] = g._mapping["live_citers"]
        top_ghost_norms.append(item)

    pct = round(100.0 * numer / denom, 2) if denom else 0.0
    return {
        "briefing": "dead-law-dependencies",
        "scope": scope,
        "live_norms_count": denom,
        "live_norms_citing_repealed_count": numer,
        "percentage": pct,
        "top_ghost_norms": top_ghost_norms,
    }


# --- Briefing 4: Ley 30/1992 blast radius -----------------------------------


def compute_blast_radius(conn, scope: str = DEFAULT_SCOPE) -> Dict[str, Any]:
    sp = _scope_params(scope)
    target_map = _fetch_norms_map(conn, [LEY_30_1992_ID])
    target = target_map.get(LEY_30_1992_ID)

    rows = conn.execute(
        text(
            "SELECT s.id AS norm_id, MIN(r.relation_label_raw) AS relation_label_raw, "
            "MIN(r.relation_detail_raw) AS relation_detail_raw "
            "FROM relations r JOIN norms s ON s.id = r.source_norm_id "
            "WHERE r.relation_type = 'CITES' AND r.target_norm_id = :target "
            "AND s.is_live = 1" + _scope_clause("s", scope) + " "
            "GROUP BY s.id ORDER BY s.publication_date DESC, s.id"
        ),
        {"target": LEY_30_1992_ID, **sp},
    ).fetchall()

    ids = [r._mapping["norm_id"] for r in rows]
    norms_map = _fetch_norms_map(conn, ids)

    # Worklist intelligence (deterministic heuristics + dead-law counts), imported lazily
    # to avoid a circular import at module load.
    from app.services import ley30

    dead_counts = ley30.dead_law_citation_counts(conn, ids, scope)

    citing = []
    for rank, r in enumerate(rows, start=1):
        nid = r._mapping["norm_id"]
        item = dict(norms_map.get(nid, {"id": nid}))
        item["rank_position"] = rank
        item["relation_label_raw"] = r._mapping["relation_label_raw"]
        item["relation_detail_raw"] = r._mapping["relation_detail_raw"]
        # Each worklist norm cites Ley 30/1992 (a dead norm), so its dead-law count is >= 1.
        ley30.enrich_worklist_item(
            item, dead_law_citations_count=dead_counts.get(nid, 1) or 1
        )
        citing.append(item)

    return {
        "briefing": "ley-30-1992-blast-radius",
        "scope": scope,
        "target_id": LEY_30_1992_ID,
        "ley_30_1992": target,
        "repeal_context": ley30.get_ley30_repeal_context(conn),
        "total_live_direct_citers": len(citing),
        "citing_norms": citing,
    }


# --- Graph builders ---------------------------------------------------------


def _build_graph(
    conn,
    edge_sql: str,
    params: Dict[str, Any],
    *,
    hub_ids: Optional[set] = None,
    limit_hub_fn=None,
    total_rows: Optional[int] = None,
) -> Dict[str, Any]:
    rows = list(conn.execute(text(edge_sql), params).fetchall())
    raw_count = len(rows)
    truncated = False
    if limit_hub_fn is not None:
        limited = _limit_edges_per_hub(rows, limit_hub_fn)
        truncated = len(limited) < raw_count
        rows = limited

    in_deg: Dict[str, int] = {}
    out_deg: Dict[str, int] = {}
    node_ids: set = set()
    for r in rows:
        s = r._mapping["source_norm_id"]
        t = r._mapping["target_norm_id"]
        node_ids.add(s)
        node_ids.add(t)
        out_deg[s] = out_deg.get(s, 0) + 1
        in_deg[t] = in_deg.get(t, 0) + 1

    hubs = hub_ids or set()
    norms_map = _fetch_norms_map(conn, list(node_ids))
    nodes = []
    for nid in node_ids:
        metrics = {
            "in_degree": in_deg.get(nid, 0),
            "out_degree": out_deg.get(nid, 0),
        }
        node = _node(
            norms_map.get(nid),
            nid,
            metrics=metrics,
            hub=nid in hubs,
        )
        # Flat weight drives metric-based node sizing in the frontend stylesheet:
        # incoming for unreadable/dead-law/blast hubs, outgoing for omnibus.
        node["data"]["weight"] = max(in_deg.get(nid, 0), out_deg.get(nid, 0), 1)
        nodes.append(node)
    edges = [_edge(r) for r in rows]
    meta: Dict[str, Any] = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "truncated": truncated,
    }
    if truncated:
        meta["max_edges_per_hub"] = GRAPH_VIZ_MAX_EDGES_PER_HUB
        meta["total_edges_available"] = raw_count
    return {"nodes": nodes, "edges": edges, "meta": meta}


def graph_unreadable(conn, scope: str = DEFAULT_SCOPE, limit: int = 5) -> Dict[str, Any]:
    top = compute_unreadable(conn, scope, limit)
    ids = [i["id"] for i in top["items"]]
    if not ids:
        return {"nodes": [], "edges": []}
    placeholders = ",".join(f":t{i}" for i in range(len(ids)))
    params = {f"t{i}": v for i, v in enumerate(ids)}
    sql = (
        "SELECT id, source_norm_id, target_norm_id, relation_type, relation_label_raw, "
        "relation_detail_raw FROM relations "
        f"WHERE relation_type='AMENDS' AND target_norm_id IN ({placeholders})"
    )
    return _build_graph(
        conn,
        sql,
        params,
        hub_ids=set(ids),
        limit_hub_fn=lambda r: r._mapping["target_norm_id"],
    )


def graph_omnibus(conn, scope: str = DEFAULT_SCOPE, limit: int = 5) -> Dict[str, Any]:
    top = compute_omnibus(conn, scope, limit)
    ids = [i["id"] for i in top["items"]]
    if not ids:
        return {"nodes": [], "edges": []}
    placeholders = ",".join(f":s{i}" for i in range(len(ids)))
    params = {f"s{i}": v for i, v in enumerate(ids)}
    sql = (
        "SELECT id, source_norm_id, target_norm_id, relation_type, relation_label_raw, "
        "relation_detail_raw FROM relations "
        f"WHERE relation_type='AMENDS' AND source_norm_id IN ({placeholders})"
    )
    return _build_graph(
        conn,
        sql,
        params,
        hub_ids=set(ids),
        limit_hub_fn=lambda r: r._mapping["source_norm_id"],
    )


def graph_dead_law(conn, scope: str = DEFAULT_SCOPE, limit: int = 5) -> Dict[str, Any]:
    sp = _scope_params(scope)
    ghosts = compute_dead_law(conn, scope, limit)
    ghost_ids = {g["id"] for g in ghosts.get("top_ghost_norms", [])}
    sql = (
        "SELECT r.id, r.source_norm_id, r.target_norm_id, r.relation_type, "
        "r.relation_label_raw, r.relation_detail_raw "
        "FROM relations r "
        "JOIN norms s ON s.id = r.source_norm_id "
        "JOIN norms t ON t.id = r.target_norm_id "
        "WHERE r.relation_type='CITES' AND s.is_live=1 AND t.is_repealed=1"
        + _scope_clause("s", scope)
        + " AND t.id IN (SELECT t2.id FROM relations r2 "
        "JOIN norms s2 ON s2.id=r2.source_norm_id JOIN norms t2 ON t2.id=r2.target_norm_id "
        "WHERE r2.relation_type='CITES' AND s2.is_live=1 AND t2.is_repealed=1"
        + _scope_clause("s2", scope)
        + " GROUP BY t2.id ORDER BY COUNT(DISTINCT r2.source_norm_id) DESC, t2.id LIMIT :limit)"
    )
    # The same named param (:scope_label) appears in both scope clauses; it binds once.
    params = {"limit": limit, **sp}
    return _build_graph(
        conn,
        sql,
        params,
        hub_ids=ghost_ids,
        limit_hub_fn=lambda r: r._mapping["target_norm_id"],
    )


def graph_blast_radius(conn, scope: str = DEFAULT_SCOPE) -> Dict[str, Any]:
    sp = _scope_params(scope)
    sql = (
        "SELECT r.id, r.source_norm_id, r.target_norm_id, r.relation_type, "
        "r.relation_label_raw, r.relation_detail_raw "
        "FROM relations r JOIN norms s ON s.id = r.source_norm_id "
        "WHERE r.relation_type='CITES' AND r.target_norm_id = :target AND s.is_live=1"
        + _scope_clause("s", scope)
    )
    params = {"target": LEY_30_1992_ID, **sp}
    return _build_graph(
        conn,
        sql,
        params,
        hub_ids={LEY_30_1992_ID},
        limit_hub_fn=lambda r: r._mapping["target_norm_id"],
    )


GRAPH_BUILDERS = {
    "unreadable-laws": graph_unreadable,
    "omnibus-laws": graph_omnibus,
    "dead-law-dependencies": graph_dead_law,
    "ley-30-1992-blast-radius": graph_blast_radius,
}


def build_briefing_graph(conn, briefing_key: str, scope: str = DEFAULT_SCOPE) -> Dict[str, Any]:
    builder = GRAPH_BUILDERS.get(briefing_key)
    if builder is None:
        raise KeyError(briefing_key)
    return builder(conn, scope)


# --- Summary + caching ------------------------------------------------------


def compute_summary(conn) -> Dict[str, Any]:
    total_norms = conn.execute(text("SELECT COUNT(*) FROM norms")).scalar() or 0
    total_relations = conn.execute(text("SELECT COUNT(*) FROM relations")).scalar() or 0
    rel_counts = {
        r._mapping["relation_type"]: r._mapping["cnt"]
        for r in conn.execute(
            text("SELECT relation_type, COUNT(*) AS cnt FROM relations GROUP BY relation_type")
        ).fetchall()
    }
    lifecycle_counts = {
        r._mapping["lifecycle_status"]: r._mapping["cnt"]
        for r in conn.execute(
            text("SELECT lifecycle_status, COUNT(*) AS cnt FROM norms GROUP BY lifecycle_status")
        ).fetchall()
    }
    last_ingestion = conn.execute(text("SELECT MAX(updated_at) FROM norms")).scalar()
    return {
        "total_norms": total_norms,
        "total_relations": total_relations,
        "relation_counts_by_type": rel_counts,
        "lifecycle_counts": lifecycle_counts,
        "default_scope": DEFAULT_SCOPE,
        "scope_label": STATE_SCOPE_LABEL,
        "last_ingestion_at": last_ingestion,
    }


def compute_data_quality(conn, label_limit: int = 50) -> Dict[str, Any]:
    """Engineering audit payload for the Data Quality page."""
    summary = compute_summary(conn)
    unknown_targets = (
        conn.execute(
            text("SELECT COUNT(*) FROM relations WHERE target_known = 0 OR target_known IS NULL")
        ).scalar()
        or 0
    )
    label_rows = conn.execute(
        text(
            "SELECT label, normalized_type, count FROM raw_relation_labels "
            "ORDER BY count DESC LIMIT :lim"
        ),
        {"lim": label_limit},
    ).fetchall()
    labels = [
        {
            "label": r._mapping["label"],
            "normalized_type": r._mapping["normalized_type"],
            "count": r._mapping["count"],
        }
        for r in label_rows
    ]
    other_count = sum(
        r._mapping["count"]
        for r in conn.execute(
            text("SELECT count FROM raw_relation_labels WHERE normalized_type = 'OTHER'")
        ).fetchall()
    )
    total_labels = (
        conn.execute(text("SELECT COUNT(*) FROM raw_relation_labels")).scalar() or 0
    )
    return {
        **summary,
        "unknown_target_relations": unknown_targets,
        "other_label_occurrences": other_count,
        "distinct_raw_labels": total_labels,
        "labels": labels,
        "label_limit": label_limit,
    }


def compute_all_briefings(scope: str = DEFAULT_SCOPE) -> Dict[str, Any]:
    """Recompute all four briefings and cache their payloads in briefing_results."""
    with session_scope() as conn:
        payloads = {
            "unreadable-laws": compute_unreadable(conn, scope),
            "omnibus-laws": compute_omnibus(conn, scope),
            "dead-law-dependencies": compute_dead_law(conn, scope),
            "ley-30-1992-blast-radius": compute_blast_radius(conn, scope),
        }
        now = _now()
        for key, payload in payloads.items():
            conn.execute(
                text("DELETE FROM briefing_results WHERE briefing_key=:k AND scope=:s"),
                {"k": key, "s": scope},
            )
            conn.execute(
                text(
                    "INSERT INTO briefing_results (briefing_key, scope, payload_json, computed_at) "
                    "VALUES (:k, :s, :p, :t)"
                ),
                {"k": key, "s": scope, "p": json.dumps(payload, ensure_ascii=False), "t": now},
            )
    return {"scope": scope, "computed_at": now, "briefings": list(payloads.keys())}


def get_cached_briefing(conn, briefing_key: str, scope: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        text(
            "SELECT payload_json FROM briefing_results WHERE briefing_key=:k AND scope=:s "
            "ORDER BY computed_at DESC LIMIT 1"
        ),
        {"k": briefing_key, "s": scope},
    ).fetchone()
    if not row:
        return None
    return json.loads(row._mapping["payload_json"])
