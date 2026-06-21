"""Ingestion: fetch BOE data, normalize it, and write the SQLite graph.

Two modes:
  - sample: a small, fast, demo-ready set (key norms + recent), with fixture fallback.
  - full:   the entire corpus via the list endpoint (limit=-1) + per-norm analysis.

Both modes are resumable: cached raw responses and already-persisted norms are reused.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from sqlalchemy import func, insert, select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.config import (
    FIXTURES_DIR,
    LIST_PAGE_SIZE,
    PROCESSED_DIR,
    SAMPLE_RECENT_COUNT,
    SAMPLE_SEED_IDS,
)
from app.db.session import init_db, session_scope
from app.models.tables import (
    norm_subjects,
    norms,
    raw_relation_labels,
    relations,
    subjects,
)
from app.services.boe_client import BoeClient, list_items
from app.utils.cache import has_cache
from app.services.parsers import (
    ParsedAnalysis,
    ParsedNorm,
    ParsedRelation,
    parse_analysis,
    parse_metadata,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _upsert_norm(conn, norm: ParsedNorm) -> None:
    now = _now()
    values = {
        "id": norm.id,
        "title": norm.title,
        "official_number": norm.official_number,
        "rank_code": norm.rank_code,
        "rank": norm.rank,
        "scope_code": norm.scope_code,
        "scope": norm.scope,
        "department_code": norm.department_code,
        "department": norm.department,
        "disposition_date": norm.disposition_date,
        "publication_date": norm.publication_date,
        "effective_date": norm.effective_date,
        "repeal_date": norm.repeal_date,
        "annulment_date": norm.annulment_date,
        "exhausted_validity": norm.exhausted_validity,
        "estatus_derogacion": norm.estatus_derogacion,
        "estatus_anulacion": norm.estatus_anulacion,
        "vigencia_agotada": norm.vigencia_agotada,
        "consolidation_status_code": norm.consolidation_status_code,
        "consolidation_status": norm.consolidation_status,
        "lifecycle_status": norm.lifecycle_status,
        "is_live": 1 if norm.is_live else 0,
        "is_repealed": 1 if norm.is_repealed else 0,
        "url_eli": norm.url_eli,
        "url_html": norm.url_html,
        "last_updated": norm.last_updated,
        "raw_json": norm.raw_json,
        "created_at": now,
        "updated_at": now,
    }
    stmt = sqlite_insert(norms).values(**values)
    update_cols = {k: stmt.excluded[k] for k in values if k not in ("id", "created_at")}
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
    conn.execute(stmt)


def _insert_relations(conn, rels: Iterable[ParsedRelation]) -> int:
    count = 0
    now = _now()
    for r in rels:
        stmt = (
            sqlite_insert(relations)
            .values(
                source_norm_id=r.source_norm_id,
                target_norm_id=r.target_norm_id,
                relation_type=r.relation_type,
                relation_code=r.relation_code,
                relation_label_raw=r.relation_label_raw,
                relation_detail_raw=r.relation_detail_raw,
                api_direction=r.api_direction,
                current_norm_id=r.current_norm_id,
                target_known=0,
                created_at=now,
            )
            .on_conflict_do_nothing()
        )
        conn.execute(stmt)
        count += 1
    return count


def _insert_subjects(conn, analysis: ParsedAnalysis, norm_id: str) -> None:
    for s in analysis.subjects:
        conn.execute(
            sqlite_insert(subjects)
            .values(code=s.code, label=s.label)
            .on_conflict_do_nothing()
        )
        conn.execute(
            sqlite_insert(norm_subjects)
            .values(norm_id=norm_id, subject_code=s.code)
            .on_conflict_do_nothing()
        )


def _refresh_target_known(conn) -> None:
    """Mark relations whose target norm exists in our norms table."""
    conn.exec_driver_sql(
        "UPDATE relations SET target_known = "
        "(SELECT CASE WHEN EXISTS(SELECT 1 FROM norms WHERE norms.id = relations.target_norm_id) "
        "THEN 1 ELSE 0 END)"
    )


def build_data_quality_report(conn) -> Dict[str, Any]:
    """Rebuild raw_relation_labels and return a data-quality report."""
    conn.exec_driver_sql("DELETE FROM raw_relation_labels")
    rows = conn.execute(
        select(
            relations.c.relation_label_raw,
            relations.c.relation_type,
            func.count().label("cnt"),
        ).group_by(relations.c.relation_label_raw, relations.c.relation_type)
    ).fetchall()

    by_label: Dict[str, Dict[str, Any]] = {}
    by_type: Dict[str, int] = {}
    for label, rtype, cnt in rows:
        label_key = label or "(empty)"
        entry = by_label.setdefault(label_key, {"normalized_type": rtype, "count": 0})
        entry["count"] += cnt
        by_type[rtype] = by_type.get(rtype, 0) + cnt

    for label, entry in by_label.items():
        conn.execute(
            insert(raw_relation_labels).values(
                label=label,
                normalized_type=entry["normalized_type"],
                count=entry["count"],
            )
        )

    total_norms = conn.execute(select(func.count()).select_from(norms)).scalar() or 0
    total_relations = conn.execute(select(func.count()).select_from(relations)).scalar() or 0
    report = {
        "generated_at": _now(),
        "total_norms": total_norms,
        "total_relations": total_relations,
        "relation_counts_by_type": by_type,
        "labels": [
            {"label": k, "normalized_type": v["normalized_type"], "count": v["count"]}
            for k, v in sorted(by_label.items(), key=lambda kv: -kv[1]["count"])
        ],
    }
    return report


def write_data_quality_report(report: Dict[str, Any]) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / "data_quality_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _existing_norm_ids(conn) -> Set[str]:
    rows = conn.execute(select(norms.c.id)).fetchall()
    return {r[0] for r in rows}


def _norm_analysis_done(conn, norm_id: str) -> bool:
    """True if we already parsed this norm's analisis (or it was fetched with no edges)."""
    rel = conn.execute(
        text("SELECT 1 FROM relations WHERE current_norm_id = :id LIMIT 1"),
        {"id": norm_id},
    ).fetchone()
    if rel:
        return True
    subj = conn.execute(
        text("SELECT 1 FROM norm_subjects WHERE norm_id = :id LIMIT 1"),
        {"id": norm_id},
    ).fetchone()
    if subj:
        return True
    # Analisis cached but produced no relations/subjects — don't re-fetch on resume.
    return has_cache(f"{norm_id}/analisis")


def _ingest_analysis_for_norm(client: BoeClient, conn, norm_id: str) -> int:
    try:
        analysis_payload = client.get_analysis(norm_id)
    except Exception:  # noqa: BLE001
        return 0
    analysis = parse_analysis(norm_id, analysis_payload)
    rel_count = _insert_relations(conn, analysis.relations)
    _insert_subjects(conn, analysis, norm_id)
    return rel_count


def _fetch_all_list_items(client: BoeClient, page_size: int = LIST_PAGE_SIZE) -> List[dict]:
    """Paginate the list endpoint (limit=-1 is API-capped at 10_000)."""
    return client.fetch_all_list_items(page_size=page_size)


def _persist_norm_with_analysis(
    conn, norm: ParsedNorm, analysis: Optional[ParsedAnalysis]
) -> int:
    _upsert_norm(conn, norm)
    rel_count = 0
    if analysis is not None:
        rel_count = _insert_relations(conn, analysis.relations)
        _insert_subjects(conn, analysis, norm.id)
    return rel_count


# --- Fixtures fallback -------------------------------------------------------


def _load_fixture(name: str) -> Optional[Any]:
    path = FIXTURES_DIR / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _ingest_from_fixtures(conn) -> Dict[str, Any]:
    """Fallback demo dataset bundled with the repo (no network)."""
    norms_fixture = _load_fixture("sample_norms.json") or []
    analyses_fixture = _load_fixture("sample_analyses.json") or {}
    ingested = 0
    rel_total = 0
    for meta in norms_fixture:
        norm = parse_metadata(meta)
        if not norm:
            continue
        analysis_payload = analyses_fixture.get(norm.id)
        analysis = parse_analysis(norm.id, analysis_payload) if analysis_payload else None
        rel_total += _persist_norm_with_analysis(conn, norm, analysis)
        ingested += 1
    return {"source": "fixtures", "norms": ingested, "relations": rel_total}


# --- Public ingestion entrypoints -------------------------------------------


def ingest_sample(use_api: bool = True, recent_count: int = SAMPLE_RECENT_COUNT) -> Dict[str, Any]:
    """Ingest a small set: seed norms + N recent. Falls back to fixtures on failure."""
    init_db()
    summary: Dict[str, Any] = {"mode": "sample"}

    if use_api:
        try:
            summary.update(_ingest_sample_via_api(recent_count))
        except Exception as exc:  # noqa: BLE001 - graceful demo fallback
            summary["api_error"] = str(exc)
            with session_scope() as conn:
                fb = _ingest_from_fixtures(conn)
            summary.update(fb)
            summary["fell_back"] = True
    else:
        with session_scope() as conn:
            summary.update(_ingest_from_fixtures(conn))

    _finalize(summary)
    return summary


def _ingest_sample_via_api(
    recent_count: int, neighbor_cap: int = 200
) -> Dict[str, Any]:
    seed_ids: List[str] = list(SAMPLE_SEED_IDS)
    with BoeClient() as client:
        listing = client.list_norms(offset=0, limit=max(recent_count, 1))
        for item in list_items(listing):
            norm_id = item.get("identificador") if isinstance(item, dict) else None
            if norm_id and norm_id not in seed_ids:
                seed_ids.append(norm_id)

        ingested = 0
        rel_total = 0
        neighbor_ids: List[str] = []
        with session_scope() as conn:
            # Wave 1: seeds + recent norms.
            for norm_id in seed_ids:
                norm, analysis = _fetch_norm(client, norm_id)
                if not norm:
                    continue
                rel_total += _persist_norm_with_analysis(conn, norm, analysis)
                ingested += 1
                # For the explicit seed norms, collect one hop of neighbours so the
                # citation/dependency briefings have connected, live data to show.
                if norm_id in SAMPLE_SEED_IDS and analysis is not None:
                    for rel in analysis.relations:
                        for cand in (rel.source_norm_id, rel.target_norm_id):
                            if (
                                cand
                                and cand != norm_id
                                and cand not in seed_ids
                                and cand not in neighbor_ids
                                and cand.startswith("BOE-A-")
                            ):
                                neighbor_ids.append(cand)

            # Wave 2: bounded neighbour expansion (metadata only is enough, but we
            # also pull their analysis so their own relations are present).
            for norm_id in neighbor_ids[:neighbor_cap]:
                norm, analysis = _fetch_norm(client, norm_id)
                if not norm:
                    continue
                rel_total += _persist_norm_with_analysis(conn, norm, analysis)
                ingested += 1
    return {
        "source": "api",
        "norms": ingested,
        "relations": rel_total,
        "seed_requested": len(seed_ids),
        "neighbors_requested": min(len(neighbor_ids), neighbor_cap),
    }


def ingest_full(
    page_size: int = LIST_PAGE_SIZE,
    resume: bool = True,
) -> Dict[str, Any]:
    """Ingest the full corpus via paginated list + per-norm analysis.

    The BOE API caps ``limit=-1`` at 10_000 items; we paginate to fetch all ~12k+ norms.
    With ``resume=True`` (default), norms whose analisis is already in the DB are skipped.
    """
    init_db()
    summary: Dict[str, Any] = {"mode": "full", "resume": resume, "page_size": page_size}
    ingested = 0
    rel_total = 0
    rel_skipped = 0
    list_total = 0

    with BoeClient() as client:
        items = _fetch_all_list_items(client, page_size=page_size)
        list_total = len(items)
        summary["list_total"] = list_total

        # Pass 1: metadata from list pages (upsert — idempotent).
        with session_scope() as conn:
            for item in items:
                norm = parse_metadata(item)
                if norm:
                    _upsert_norm(conn, norm)
                    ingested += 1

        # Pass 2: analisis per norm (cached/resumable; skip if already parsed).
        for item in items:
            norm_id = item.get("identificador") if isinstance(item, dict) else None
            if not norm_id:
                continue
            with session_scope() as conn:
                if resume and _norm_analysis_done(conn, norm_id):
                    rel_skipped += 1
                    continue
                rel_total += _ingest_analysis_for_norm(client, conn, norm_id)

    summary.update(
        {
            "source": "api",
            "norms": ingested,
            "relations": rel_total,
            "analysis_skipped": rel_skipped,
        }
    )
    _finalize(summary)
    return summary


def ingest_missing(page_size: int = LIST_PAGE_SIZE) -> Dict[str, Any]:
    """Ingest only norms present in the API list but missing from the DB.

    Use after a capped ``limit=-1`` run to add the remaining ~2k norms without re-fetching
    analisis for the 10_000 already ingested.
    """
    init_db()
    summary: Dict[str, Any] = {"mode": "missing", "page_size": page_size}
    added = 0
    rel_total = 0

    with BoeClient() as client:
        items = _fetch_all_list_items(client, page_size=page_size)
        summary["list_total"] = len(items)

        with session_scope() as conn:
            existing = _existing_norm_ids(conn)

        missing_items = [
            item
            for item in items
            if isinstance(item, dict)
            and item.get("identificador")
            and item["identificador"] not in existing
        ]
        summary["missing_count"] = len(missing_items)

        for item in missing_items:
            norm_id = item["identificador"]
            norm = parse_metadata(item)
            if not norm:
                continue
            with session_scope() as conn:
                _upsert_norm(conn, norm)
                rel_total += _ingest_analysis_for_norm(client, conn, norm_id)
                added += 1

    summary.update({"source": "api", "norms_added": added, "relations": rel_total})
    _finalize(summary)
    return summary


def _fetch_norm(client: BoeClient, norm_id: str):
    try:
        meta = client.get_metadata(norm_id)
    except Exception:  # noqa: BLE001
        return None, None
    norm = parse_metadata(meta)
    if not norm:
        return None, None
    try:
        analysis_payload = client.get_analysis(norm_id)
        analysis = parse_analysis(norm_id, analysis_payload)
    except Exception:  # noqa: BLE001
        analysis = None
    return norm, analysis


def _finalize(summary: Dict[str, Any]) -> None:
    with session_scope() as conn:
        _refresh_target_known(conn)
        report = build_data_quality_report(conn)
    path = write_data_quality_report(report)
    summary["data_quality_report"] = str(path)
    summary["relation_counts_by_type"] = report["relation_counts_by_type"]
