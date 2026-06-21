"""Ley 30/1992 intelligence: repeal context, cleanup-impact simulation, and the
deterministic (auditable) replacement + priority heuristics used by the worklist.

Everything here is computed from SQLite or from pure, table-driven keyword matching.
Nothing is hard-coded as a legal conclusion: the replacement classifier is explicitly a
*heuristic for legal review* and always returns the matched keywords for audit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import text

from app.core.config import (
    DEFAULT_SCOPE,
    LEY_30_1992_ID,
    LEY_39_2015_ID,
    LEY_40_2015_ID,
)
from app.services.relation_normalizer import _canonical

# --- Repeal context (Part 1) ------------------------------------------------

REPLACEMENT_ROLES = {
    LEY_39_2015_ID: "Common Administrative Procedure (Procedimiento Administrativo Común)",
    LEY_40_2015_ID: "Public Sector Legal Regime (Régimen Jurídico del Sector Público)",
}

DISPLAY_NOTE = (
    "Ley 30/1992 is treated as repealed for the blast-radius analysis. The platform "
    "separates the raw BOE repeal-date field from the 2015 replacement context (Leyes "
    "39/2015 and 40/2015) used in the challenge. Direct live citers are computed only from "
    "CITES edges to Ley 30/1992, never via the replacement norms."
)


def _iso_date(boe_date: Optional[str]) -> Optional[str]:
    """Format a raw BOE YYYYMMDD string as ISO YYYY-MM-DD; pass through anything else."""
    if not boe_date:
        return None
    s = str(boe_date).strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return s


def _is_full_repeal_detail(detail: Optional[str]) -> bool:
    """Heuristic: a *whole-norm* derogation (no specific article/provision mentioned)."""
    canon = _canonical(detail)
    if not canon:
        return False
    partial_markers = ("ART", "APARTAD", "DISPOSICION ADICIONAL", "DISPOSICION TRANSITORIA", "PARRAFO")
    return not any(m in canon for m in partial_markers)


def get_ley30_repeal_context(conn) -> Dict[str, Any]:
    """Auditable repeal context for Ley 30/1992.

    Returns three clearly separated layers: the raw BOE repeal-date field, the graph
    `REPEALS` evidence, and the documented 2015 replacement context. Never overwrites raw
    data and never uses replacement norms to compute the blast radius.
    """
    row = conn.execute(
        text(
            "SELECT id, title, repeal_date, annulment_date, estatus_derogacion, "
            "estatus_anulacion, vigencia_agotada, lifecycle_status, url_html "
            "FROM norms WHERE id = :id"
        ),
        {"id": LEY_30_1992_ID},
    ).fetchone()

    if row is None:
        return {
            "target_id": LEY_30_1992_ID,
            "status": "UNKNOWN",
            "boe_raw_repeal_date": None,
            "effective_repeal_date": None,
            "repealing_norms": [],
            "replacement_norms": _replacement_norms(conn),
            "display_note": DISPLAY_NOTE,
        }

    m = row._mapping
    boe_raw_repeal_date = _iso_date(m.get("repeal_date"))

    # Graph evidence: distinct REPEALS sources targeting Ley 30/1992. Prefer the
    # `anteriores` row (current_norm_id == source) for the cleaner detail text.
    rep_rows = conn.execute(
        text(
            "SELECT source_norm_id, relation_label_raw, relation_detail_raw, api_direction "
            "FROM relations WHERE target_norm_id = :id AND relation_type = 'REPEALS'"
        ),
        {"id": LEY_30_1992_ID},
    ).fetchall()

    best: Dict[str, Any] = {}
    for r in rep_rows:
        rm = r._mapping
        src = rm["source_norm_id"]
        prev = best.get(src)
        if prev is None or (rm.get("api_direction") == "anteriores"):
            best[src] = rm
    rep_ids = list(best.keys())
    rep_norms_map = _fetch_norm_lite(conn, rep_ids)

    repealing_norms: List[Dict[str, Any]] = []
    for src, rm in best.items():
        nm = rep_norms_map.get(src, {})
        repealing_norms.append(
            {
                "id": src,
                "title": nm.get("title"),
                "publication_date": nm.get("publication_date"),
                "relation_label_raw": rm.get("relation_label_raw"),
                "relation_detail_raw": rm.get("relation_detail_raw"),
                "url_html": nm.get("url_html"),
                "is_full_repeal": _is_full_repeal_detail(rm.get("relation_detail_raw")),
            }
        )
    # Surface the formal full-repealer (e.g. Ley 39/2015) first, then by publication date.
    repealing_norms.sort(
        key=lambda x: (not x["is_full_repeal"], x.get("publication_date") or "")
    )

    return {
        "target_id": LEY_30_1992_ID,
        "status": m.get("lifecycle_status") or "UNKNOWN",
        "title": m.get("title"),
        "url_html": m.get("url_html"),
        # Raw BOE lifecycle field (fecha_derogacion). Shown as-is, not a legal conclusion.
        "boe_raw_repeal_date": boe_raw_repeal_date,
        # Deliberately not inferred from free-text relation details.
        "effective_repeal_date": None,
        "repealing_norms": repealing_norms,
        "replacement_norms": _replacement_norms(conn),
        "display_note": DISPLAY_NOTE,
    }


def _replacement_norms(conn) -> List[Dict[str, Any]]:
    ids = [LEY_39_2015_ID, LEY_40_2015_ID]
    lite = _fetch_norm_lite(conn, ids)
    fallback_titles = {
        LEY_39_2015_ID: "Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de las Administraciones Públicas.",
        LEY_40_2015_ID: "Ley 40/2015, de 1 de octubre, de Régimen Jurídico del Sector Público.",
    }
    out: List[Dict[str, Any]] = []
    for nid in ids:
        nm = lite.get(nid, {})
        out.append(
            {
                "id": nid,
                "title": nm.get("title") or fallback_titles[nid],
                "role": REPLACEMENT_ROLES[nid],
                "url_html": nm.get("url_html") or f"https://www.boe.es/buscar/act.php?id={nid}",
                "present_in_graph": nid in lite,
            }
        )
    return out


def _fetch_norm_lite(conn, ids: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    ids = list({i for i in ids if i})
    if not ids:
        return {}
    placeholders = ",".join(f":id{i}" for i in range(len(ids)))
    params = {f"id{i}": v for i, v in enumerate(ids)}
    rows = conn.execute(
        text(
            "SELECT id, title, rank, department, publication_date, lifecycle_status, url_html "
            f"FROM norms WHERE id IN ({placeholders})"
        ),
        params,
    ).fetchall()
    return {r._mapping["id"]: dict(r._mapping) for r in rows}


# --- Cleanup-impact simulator (Part 2) --------------------------------------


def _scope_clause(alias: str, scope: str) -> str:
    if scope == "all":
        return ""
    return f" AND {alias}.scope = :scope_label"


def _scope_params(scope: str) -> Dict[str, Any]:
    from app.core.config import STATE_SCOPE_LABEL

    return {} if scope == "all" else {"scope_label": STATE_SCOPE_LABEL}


def compute_ley30_cleanup_impact(conn, scope: str = DEFAULT_SCOPE) -> Dict[str, Any]:
    """Simulate removing only direct CITES edges to Ley 30/1992 and recompute the
    dead-law-dependency rate. Never naively subtracts the direct-citer count.
    """
    sp = _scope_params(scope)

    denom = conn.execute(
        text("SELECT COUNT(*) FROM norms n WHERE n.is_live = 1" + _scope_clause("n", scope)),
        sp,
    ).scalar() or 0

    before = conn.execute(
        text(
            "SELECT COUNT(DISTINCT r.source_norm_id) FROM relations r "
            "JOIN norms s ON s.id = r.source_norm_id "
            "JOIN norms t ON t.id = r.target_norm_id "
            "WHERE r.relation_type = 'CITES' AND s.is_live = 1 AND t.is_repealed = 1"
            + _scope_clause("s", scope)
        ),
        sp,
    ).scalar() or 0

    # After simulated cleanup: same numerator but ignore the Ley 30/1992 target edge.
    after = conn.execute(
        text(
            "SELECT COUNT(DISTINCT r.source_norm_id) FROM relations r "
            "JOIN norms s ON s.id = r.source_norm_id "
            "JOIN norms t ON t.id = r.target_norm_id "
            "WHERE r.relation_type = 'CITES' AND s.is_live = 1 AND t.is_repealed = 1 "
            "AND t.id != :ley30" + _scope_clause("s", scope)
        ),
        {"ley30": LEY_30_1992_ID, **sp},
    ).scalar() or 0

    direct_live_citers = conn.execute(
        text(
            "SELECT COUNT(DISTINCT r.source_norm_id) FROM relations r "
            "JOIN norms s ON s.id = r.source_norm_id "
            "WHERE r.relation_type = 'CITES' AND r.target_norm_id = :ley30 AND s.is_live = 1"
            + _scope_clause("s", scope)
        ),
        {"ley30": LEY_30_1992_ID, **sp},
    ).scalar() or 0

    fully_cleaned = before - after  # live norms whose only dead-law citation was Ley 30/1992

    def pct(num: int) -> float:
        return round(100.0 * num / denom, 2) if denom else 0.0

    before_pct = pct(before)
    after_pct = pct(after)

    interpretation = (
        f"Cleaning direct Ley 30/1992 references would reduce the dead-law dependency rate "
        f"from {before_pct}% to {after_pct}% and fully clean {fully_cleaned} live norms."
    )

    return {
        "briefing": "ley-30-1992-cleanup-impact",
        "scope": scope,
        "denominator_live_norms": denom,
        "before": {
            "live_norms_citing_dead_law": before,
            "percentage": before_pct,
        },
        "ley_30_1992": {
            "direct_live_citers": direct_live_citers,
            "target_id": LEY_30_1992_ID,
            "repeal_context": get_ley30_repeal_context(conn),
        },
        "after_simulated_cleanup": {
            "live_norms_still_citing_dead_law": after,
            "percentage": after_pct,
            "fully_cleaned_norms": fully_cleaned,
            "remaining_dirty_norms": after,
        },
        "interpretation": interpretation,
    }


# --- Replacement classifier (Part 3) ----------------------------------------

# Keyword sets are matched as substrings of the accent-stripped, upper-cased input text.
LEY_39_2015_KEYWORDS = (
    "PROCEDIMIENTO ADMINISTRATIVO COMUN",
    "PROCEDIMIENTO ADMINISTRATIVO",
    "PROCEDIMIENTO",
    "EXPEDIENTE",
    "NOTIFICACION",
    "REGISTRO",
    "SOLICITUD",
    "RESOLUCION",
    "ACTO ADMINISTRATIVO",
    "INTERESADO",
    "RECURSO ADMINISTRATIVO",
    "SILENCIO ADMINISTRATIVO",
    "PLAZO",
)

LEY_40_2015_KEYWORDS = (
    "REGIMEN JURIDICO",
    "SECTOR PUBLICO",
    "ORGANO",
    "ORGANOS",
    "COMPETENCIA",
    "DELEGACION",
    "ENCOMIENDA",
    "CONVENIO",
    "ADMINISTRACION GENERAL",
    "RESPONSABILIDAD PATRIMONIAL",
    "POTESTAD SANCIONADORA",
    "FUNCIONAMIENTO",
    "ADMINISTRACION PUBLICA",
)

LEY_39_2015 = "LEY_39_2015"
LEY_40_2015 = "LEY_40_2015"
LEGAL_REVIEW = "LEGAL_REVIEW"

_SUGGESTION_LABELS = {
    LEY_39_2015: "Ley 39/2015",
    LEY_40_2015: "Ley 40/2015",
    LEGAL_REVIEW: "Needs legal review",
}


@dataclass
class ReplacementSuggestion:
    suggestion: str
    label: str
    confidence: str  # high | medium | low
    reason: str
    matched_ley_39_2015: List[str] = field(default_factory=list)
    matched_ley_40_2015: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggested_replacement": self.suggestion,
            "suggested_replacement_label": self.label,
            "suggested_replacement_confidence": self.confidence,
            "suggested_replacement_reason": self.reason,
            "matched_keywords": {
                "ley_39_2015": self.matched_ley_39_2015,
                "ley_40_2015": self.matched_ley_40_2015,
            },
        }


def _matches(canon: str, keywords: Sequence[str]) -> List[str]:
    hits: List[str] = []
    for kw in keywords:
        if kw in canon and kw not in hits:
            hits.append(kw)
    return hits


def classify_ley30_replacement(text_input: str) -> ReplacementSuggestion:
    """Deterministic, accent/case-insensitive heuristic suggesting a replacement norm.

    NOT a legal conclusion — always surfaces matched keywords for audit.
    Confidence: high (>=2 hits one side, 0 the other), medium (exactly 1 hit one side,
    0 the other), low (both match or neither matches).
    """
    canon = _canonical(text_input)
    hits_39 = _matches(canon, LEY_39_2015_KEYWORDS)
    hits_40 = _matches(canon, LEY_40_2015_KEYWORDS)
    n39, n40 = len(hits_39), len(hits_40)

    if n39 > 0 and n40 == 0:
        suggestion = LEY_39_2015
        confidence = "high" if n39 >= 2 else "medium"
        reason = (
            f"Matched administrative-procedure keywords ({', '.join(hits_39)}) and no "
            f"public-sector keywords."
        )
    elif n40 > 0 and n39 == 0:
        suggestion = LEY_40_2015
        confidence = "high" if n40 >= 2 else "medium"
        reason = (
            f"Matched public-sector / legal-regime keywords ({', '.join(hits_40)}) and no "
            f"administrative-procedure keywords."
        )
    elif n39 > 0 and n40 > 0:
        suggestion = LEGAL_REVIEW
        confidence = "low"
        reason = (
            "Matched both procedure and public-sector keywords; the split between Ley 39/2015 "
            "and Ley 40/2015 is ambiguous."
        )
    else:
        suggestion = LEGAL_REVIEW
        confidence = "low"
        reason = "No procedure or public-sector keywords matched; insufficient evidence."

    return ReplacementSuggestion(
        suggestion=suggestion,
        label=_SUGGESTION_LABELS[suggestion],
        confidence=confidence,
        reason=reason,
        matched_ley_39_2015=hits_39,
        matched_ley_40_2015=hits_40,
    )


# --- Priority heuristic (Part 3) --------------------------------------------

HIGH_IMPACT_RANKS = {
    "ley",
    "ley organica",
    "ley orgánica",
    "real decreto legislativo",
    "real decreto-ley",
    "real decreto ley",
}

# A small, explainable allow-list of "major" departments (canonicalised, accent-stripped).
_MAJOR_DEPARTMENT_MARKERS = (
    "JEFATURA DEL ESTADO",
    "MINISTERIO DE HACIENDA",
    "MINISTERIO DE LA PRESIDENCIA",
    "MINISTERIO DE JUSTICIA",
    "MINISTERIO DEL INTERIOR",
    "MINISTERIO DE ECONOMIA",
)


def _is_high_impact_rank(rank: Optional[str]) -> bool:
    return (rank or "").strip().lower() in HIGH_IMPACT_RANKS


def _is_major_department(department: Optional[str]) -> bool:
    canon = _canonical(department)
    return any(m in canon for m in _MAJOR_DEPARTMENT_MARKERS)


def classify_priority(
    *,
    can_be_fully_cleaned: bool,
    rank: Optional[str],
    dead_law_citations_count: int,
    department: Optional[str],
) -> Dict[str, str]:
    """Simple, explainable priority: returns {'priority', 'priority_reason'}."""
    if can_be_fully_cleaned:
        return {
            "priority": "High",
            "priority_reason": "Removing Ley 30/1992 would fully clean this norm's dead-law dependency.",
        }
    if _is_high_impact_rank(rank):
        return {
            "priority": "High",
            "priority_reason": f"High-impact rank ({rank}); changes ripple widely across the statute book.",
        }
    if dead_law_citations_count > 1:
        return {
            "priority": "Medium",
            "priority_reason": (
                f"Cites {dead_law_citations_count} dead norms; cleaning Ley 30/1992 alone leaves residual dead-law dependencies."
            ),
        }
    if _is_major_department(department):
        return {
            "priority": "Medium",
            "priority_reason": f"Belongs to a major department ({department}).",
        }
    return {
        "priority": "Low",
        "priority_reason": "Lower-impact rank, single dead-law dependency, no major-department flag.",
    }


# --- Worklist enrichment (Part 3) -------------------------------------------


def dead_law_citation_counts(
    conn, source_ids: Sequence[str], scope: str = DEFAULT_SCOPE
) -> Dict[str, int]:
    """For each given live source norm, the count of distinct repealed targets it CITES."""
    source_ids = list({i for i in source_ids if i})
    if not source_ids:
        return {}
    placeholders = ",".join(f":s{i}" for i in range(len(source_ids)))
    params = {f"s{i}": v for i, v in enumerate(source_ids)}
    rows = conn.execute(
        text(
            "SELECT r.source_norm_id AS sid, COUNT(DISTINCT r.target_norm_id) AS cnt "
            "FROM relations r JOIN norms t ON t.id = r.target_norm_id "
            "WHERE r.relation_type = 'CITES' AND t.is_repealed = 1 "
            f"AND r.source_norm_id IN ({placeholders}) GROUP BY r.source_norm_id"
        ),
        params,
    ).fetchall()
    return {r._mapping["sid"]: r._mapping["cnt"] for r in rows}


def enrich_worklist_item(
    item: Dict[str, Any],
    *,
    dead_law_citations_count: int,
) -> Dict[str, Any]:
    """Add replacement suggestion + priority + cleanup flags to a worklist row in place."""
    can_be_fully_cleaned = dead_law_citations_count <= 1

    classifier_text = " ".join(
        str(x)
        for x in (
            item.get("relation_detail_raw"),
            item.get("relation_label_raw"),
            item.get("title"),
            item.get("rank"),
            item.get("department"),
        )
        if x
    )
    suggestion = classify_ley30_replacement(classifier_text)
    priority = classify_priority(
        can_be_fully_cleaned=can_be_fully_cleaned,
        rank=item.get("rank"),
        dead_law_citations_count=dead_law_citations_count,
        department=item.get("department"),
    )

    item["dead_law_citations_count"] = dead_law_citations_count
    item["can_be_fully_cleaned_by_ley30_cleanup"] = can_be_fully_cleaned
    item.update(suggestion.to_dict())
    item.update(priority)
    return item
