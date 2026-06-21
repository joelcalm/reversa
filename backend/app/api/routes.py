"""HTTP routes for summary, briefings, norms, neighborhoods and graphs."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.api.deps import get_conn, normalize_scope
from app.core.config import DEFAULT_SCOPE
from app.services import briefings as bf
from app.services import evidence as ev
from app.services import ley30

router = APIRouter()


@router.get("/summary")
def get_summary(conn: Connection = Depends(get_conn)) -> Dict[str, Any]:
    return bf.compute_summary(conn)


@router.get("/data-quality")
def get_data_quality(
    label_limit: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    return bf.compute_data_quality(conn, label_limit)


# --- Briefings ---------------------------------------------------------------


@router.get("/briefings/unreadable-laws")
def briefing_unreadable(
    scope: str = Query(DEFAULT_SCOPE),
    limit: int = Query(5, ge=1, le=100),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    return bf.compute_unreadable(conn, normalize_scope(scope), limit)


@router.get("/briefings/omnibus-laws")
def briefing_omnibus(
    scope: str = Query(DEFAULT_SCOPE),
    limit: int = Query(5, ge=1, le=100),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    return bf.compute_omnibus(conn, normalize_scope(scope), limit)


@router.get("/briefings/dead-law-dependencies")
def briefing_dead_law(
    scope: str = Query(DEFAULT_SCOPE),
    limit: int = Query(5, ge=1, le=100),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    return bf.compute_dead_law(conn, normalize_scope(scope), limit)


@router.get("/briefings/ley-30-1992-blast-radius")
def briefing_blast_radius(
    scope: str = Query(DEFAULT_SCOPE),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    return bf.compute_blast_radius(conn, normalize_scope(scope))


@router.get("/briefings/ley-30-1992-cleanup-impact")
def briefing_cleanup_impact(
    scope: str = Query(DEFAULT_SCOPE),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    return ley30.compute_ley30_cleanup_impact(conn, normalize_scope(scope))


@router.get("/briefings/{briefing_key}/evidence")
def briefing_evidence(
    briefing_key: str,
    norm_id: Optional[str] = Query(None),
    scope: str = Query(DEFAULT_SCOPE),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    try:
        return ev.get_evidence(
            conn,
            briefing_key,
            norm_id=norm_id,
            scope=normalize_scope(scope),
            limit=limit,
            offset=offset,
        )
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown briefing key '{briefing_key}'. Valid: {list(ev.EVIDENCE_KEYS)}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# --- Norms -------------------------------------------------------------------


@router.get("/norms")
def list_norms(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="LIVE|REPEALED|ANNULLED|EXPIRED"),
    rank: Optional[str] = Query(None),
    scope: Optional[str] = Query(None, description="state|all"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    where: List[str] = []
    params: Dict[str, Any] = {}
    if search:
        where.append("(title LIKE :q OR id LIKE :q OR official_number LIKE :q)")
        params["q"] = f"%{search}%"
    if status:
        where.append("lifecycle_status = :status")
        params["status"] = status.upper()
    if rank:
        where.append("rank = :rank")
        params["rank"] = rank
    if scope and normalize_scope(scope) == "state":
        where.append("scope = :scope_label")
        params["scope_label"] = "Estatal"
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    total = conn.execute(
        text(f"SELECT COUNT(*) FROM norms{clause}"), params
    ).scalar() or 0
    rows = conn.execute(
        text(
            f"SELECT {', '.join(bf.NORM_FIELDS)} FROM norms{clause} "
            "ORDER BY publication_date DESC, id LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": limit, "offset": offset},
    ).fetchall()
    items = [bf._norm_dict(r) for r in rows]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/norms/{norm_id}")
def get_norm(norm_id: str, conn: Connection = Depends(get_conn)) -> Dict[str, Any]:
    row = conn.execute(
        text(f"SELECT {', '.join(bf.NORM_FIELDS)} FROM norms WHERE id = :id"),
        {"id": norm_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Norm {norm_id} not found")
    norm = bf._norm_dict(row)

    metrics = {
        "amended_by_count": conn.execute(
            text(
                "SELECT COUNT(DISTINCT source_norm_id) FROM relations "
                "WHERE target_norm_id=:id AND relation_type='AMENDS'"
            ),
            {"id": norm_id},
        ).scalar() or 0,
        "amends_count": conn.execute(
            text(
                "SELECT COUNT(DISTINCT target_norm_id) FROM relations "
                "WHERE source_norm_id=:id AND relation_type='AMENDS'"
            ),
            {"id": norm_id},
        ).scalar() or 0,
        "cites_count": conn.execute(
            text(
                "SELECT COUNT(DISTINCT target_norm_id) FROM relations "
                "WHERE source_norm_id=:id AND relation_type='CITES'"
            ),
            {"id": norm_id},
        ).scalar() or 0,
        "cited_by_count": conn.execute(
            text(
                "SELECT COUNT(DISTINCT source_norm_id) FROM relations "
                "WHERE target_norm_id=:id AND relation_type='CITES'"
            ),
            {"id": norm_id},
        ).scalar() or 0,
    }
    norm["metrics"] = metrics
    return norm


@router.get("/norms/{norm_id}/neighborhood")
def norm_neighborhood(
    norm_id: str,
    depth: int = Query(1, ge=1, le=2),
    relation_type: Optional[str] = Query(None),
    direction: str = Query("all"),
    limit: int = Query(80, ge=1, le=400),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    if direction not in ("all", "incoming", "outgoing"):
        raise HTTPException(status_code=422, detail="direction must be all, incoming, or outgoing")
    result = bf.build_neighborhood(
        conn,
        norm_id,
        relation_type=relation_type,
        direction=direction,
        limit=limit,
    )
    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"Norm {norm_id} not found")
    return result


# --- Graph -------------------------------------------------------------------


@router.get("/graph/briefing/{briefing_key}")
def graph_briefing(
    briefing_key: str,
    scope: str = Query(DEFAULT_SCOPE),
    conn: Connection = Depends(get_conn),
) -> Dict[str, Any]:
    try:
        return bf.build_briefing_graph(conn, briefing_key, normalize_scope(scope))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown briefing key '{briefing_key}'. Valid: {list(bf.BRIEFING_KEYS)}",
        )
