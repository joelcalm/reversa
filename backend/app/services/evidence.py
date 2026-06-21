"""Evidence endpoints: trace every executive number back to raw BOE relation edges.

For each briefing, we return the underlying directed `relations` rows (with full source/
target norm metadata and the raw relation label/detail), paginated. Nothing is summarised:
this is the audit trail behind the rankings and percentages.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.core.config import DEFAULT_SCOPE, LEY_30_1992_ID, STATE_SCOPE_LABEL

EVIDENCE_KEYS = (
    "unreadable-laws",
    "omnibus-laws",
    "dead-law-dependencies",
    "ley-30-1992-blast-radius",
)

_EVIDENCE_NORM_FIELDS = (
    "id",
    "title",
    "rank",
    "department",
    "publication_date",
    "lifecycle_status",
    "url_html",
)


def _scope_clause(alias: str, scope: str) -> str:
    if scope == "all":
        return ""
    return f" AND {alias}.scope = :scope_label"


def _scope_params(scope: str) -> Dict[str, Any]:
    return {} if scope == "all" else {"scope_label": STATE_SCOPE_LABEL}


def _norm_lite(conn, ids: List[str]) -> Dict[str, Dict[str, Any]]:
    ids = list({i for i in ids if i})
    if not ids:
        return {}
    placeholders = ",".join(f":id{i}" for i in range(len(ids)))
    params = {f"id{i}": v for i, v in enumerate(ids)}
    rows = conn.execute(
        text(
            f"SELECT {', '.join(_EVIDENCE_NORM_FIELDS)} FROM norms WHERE id IN ({placeholders})"
        ),
        params,
    ).fetchall()
    return {r._mapping["id"]: dict(r._mapping) for r in rows}


def _norm_payload(norm_id: str, lite: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    nm = lite.get(norm_id)
    if nm:
        return {k: nm.get(k) for k in _EVIDENCE_NORM_FIELDS}
    return {k: (norm_id if k == "id" else None) for k in _EVIDENCE_NORM_FIELDS}


def _build_query(briefing_key: str, norm_id: Optional[str], scope: str):
    """Return (where_sql, params, default_norm_id) for the requested evidence mode."""
    sp = _scope_params(scope)

    if briefing_key == "unreadable-laws":
        # Incoming AMENDS to the selected target norm.
        if not norm_id:
            raise ValueError("norm_id is required for unreadable-laws evidence")
        where = "r.relation_type = 'AMENDS' AND r.target_norm_id = :nid"
        return where, {"nid": norm_id, **sp}, norm_id

    if briefing_key == "omnibus-laws":
        # Outgoing AMENDS from the selected source norm.
        if not norm_id:
            raise ValueError("norm_id is required for omnibus-laws evidence")
        where = "r.relation_type = 'AMENDS' AND r.source_norm_id = :nid"
        return where, {"nid": norm_id, **sp}, norm_id

    if briefing_key == "dead-law-dependencies":
        # Incoming CITES from live in-scope norms to the selected ghost (dead) norm.
        if not norm_id:
            raise ValueError("norm_id is required for dead-law-dependencies evidence")
        where = (
            "r.relation_type = 'CITES' AND r.target_norm_id = :nid AND s.is_live = 1"
            + _scope_clause("s", scope)
        )
        return where, {"nid": norm_id, **sp}, norm_id

    if briefing_key == "ley-30-1992-blast-radius":
        # Incoming CITES from live in-scope norms to Ley 30/1992 (default target).
        target = LEY_30_1992_ID
        params: Dict[str, Any] = {"target": target, **sp}
        where = (
            "r.relation_type = 'CITES' AND r.target_norm_id = :target AND s.is_live = 1"
            + _scope_clause("s", scope)
        )
        if norm_id and norm_id != target:
            # Optional filter to a specific citing (source) norm.
            where += " AND r.source_norm_id = :nid"
            params["nid"] = norm_id
        return where, params, target

    raise KeyError(briefing_key)


def get_evidence(
    conn,
    briefing_key: str,
    *,
    norm_id: Optional[str] = None,
    scope: str = DEFAULT_SCOPE,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    where, params, resolved_norm_id = _build_query(briefing_key, norm_id, scope)

    # LEFT JOIN so referenced-but-not-ingested norms still appear (with null metadata);
    # any `s.is_live = 1` filter in `where` still restricts to ingested live sources.
    join = (
        "LEFT JOIN norms s ON s.id = r.source_norm_id "
        "LEFT JOIN norms t ON t.id = r.target_norm_id"
    )
    # One row per logical edge (source, target, type) so totals match the briefing headline
    # (which counts distinct source/target), not raw mirror/event duplicates.
    group_by = "GROUP BY r.source_norm_id, r.target_norm_id, r.relation_type"

    total = conn.execute(
        text(
            f"SELECT COUNT(*) FROM (SELECT 1 FROM relations r {join} WHERE {where} {group_by})"
        ),
        params,
    ).scalar() or 0

    rows = conn.execute(
        text(
            "SELECT MIN(r.id) AS id, r.source_norm_id, r.target_norm_id, r.relation_type, "
            "MIN(r.relation_code) AS relation_code, MIN(r.relation_label_raw) AS relation_label_raw, "
            "MIN(r.relation_detail_raw) AS relation_detail_raw, "
            "MIN(r.api_direction) AS api_direction, MIN(r.current_norm_id) AS current_norm_id "
            f"FROM relations r {join} WHERE {where} {group_by} "
            "ORDER BY MIN(r.id) LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": limit, "offset": offset},
    ).fetchall()

    ids: List[str] = []
    for r in rows:
        ids.append(r._mapping["source_norm_id"])
        ids.append(r._mapping["target_norm_id"])
    lite = _norm_lite(conn, ids)

    items: List[Dict[str, Any]] = []
    for r in rows:
        m = r._mapping
        items.append(
            {
                "source_norm": _norm_payload(m["source_norm_id"], lite),
                "target_norm": _norm_payload(m["target_norm_id"], lite),
                "relation": {
                    "relation_type": m["relation_type"],
                    "relation_code": m.get("relation_code"),
                    "relation_label_raw": m.get("relation_label_raw"),
                    "relation_detail_raw": m.get("relation_detail_raw"),
                    "api_direction": m.get("api_direction"),
                    "current_norm_id": m.get("current_norm_id"),
                },
            }
        )

    return {
        "briefing": briefing_key,
        "scope": scope,
        "norm_id": resolved_norm_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }
