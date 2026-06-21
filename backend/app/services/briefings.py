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
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import text

from app.core.config import DEFAULT_SCOPE, LEY_30_1992_ID, STATE_SCOPE_LABEL
from app.db.session import session_scope

BRIEFING_KEYS = (
    "unreadable-laws",
    "omnibus-laws",
    "dead-law-dependencies",
    "ley-30-1992-blast-radius",
)

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


def _node(norm: Optional[Dict[str, Any]], norm_id: str, metrics: Optional[dict] = None) -> dict:
    if norm:
        data = {
            "id": norm["id"],
            "label": _short_label(norm),
            "title": norm.get("title"),
            "lifecycle_status": norm.get("lifecycle_status"),
            "rank": norm.get("rank"),
            "url_html": norm.get("url_html"),
            "is_live": norm.get("is_live"),
            "metrics": metrics or {},
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
            "metrics": metrics or {},
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
        item["target_count"] = r._mapping["target_count"]
        item["subject_diversity"] = _subject_diversity(conn, nid)
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
    citing = []
    for rank, r in enumerate(rows, start=1):
        nid = r._mapping["norm_id"]
        item = dict(norms_map.get(nid, {"id": nid}))
        item["rank_position"] = rank
        item["relation_label_raw"] = r._mapping["relation_label_raw"]
        item["relation_detail_raw"] = r._mapping["relation_detail_raw"]
        citing.append(item)

    return {
        "briefing": "ley-30-1992-blast-radius",
        "scope": scope,
        "target_id": LEY_30_1992_ID,
        "ley_30_1992": target,
        "total_live_direct_citers": len(citing),
        "citing_norms": citing,
    }


# --- Graph builders ---------------------------------------------------------


def _build_graph(conn, edge_sql: str, params: Dict[str, Any]) -> Dict[str, Any]:
    rows = conn.execute(text(edge_sql), params).fetchall()
    node_ids = set()
    for r in rows:
        node_ids.add(r._mapping["source_norm_id"])
        node_ids.add(r._mapping["target_norm_id"])
    norms_map = _fetch_norms_map(conn, list(node_ids))
    nodes = [_node(norms_map.get(nid), nid) for nid in node_ids]
    edges = [_edge(r) for r in rows]
    return {"nodes": nodes, "edges": edges}


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
    return _build_graph(conn, sql, params)


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
    return _build_graph(conn, sql, params)


def graph_dead_law(conn, scope: str = DEFAULT_SCOPE, limit: int = 5) -> Dict[str, Any]:
    sp = _scope_params(scope)
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
    return _build_graph(conn, sql, params)


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
    return _build_graph(conn, sql, params)


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
