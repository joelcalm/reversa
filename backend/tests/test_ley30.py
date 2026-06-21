"""Tests for Ley 30/1992 repeal context, cleanup-impact simulator, replacement
classifier, and the priority heuristic."""
from sqlalchemy import text

from app.core.config import LEY_30_1992_ID, LEY_39_2015_ID, LEY_40_2015_ID
from app.services import ley30
from app.services.ley30 import (
    LEGAL_REVIEW,
    LEY_39_2015,
    LEY_40_2015,
    classify_ley30_replacement,
    classify_priority,
)

# --- Repeal context ---------------------------------------------------------


def test_repeal_context_keeps_raw_date_and_no_effective_date(db, insert_norm, insert_relation):
    # Ley 30/1992 with a raw BOE repeal-date field but no derivable effective date.
    insert_norm(LEY_30_1992_ID, title="Ley 30/1992", derog="S")
    # Patch the raw repeal_date directly (the fixture does not set it).
    with db.session_scope() as conn:
        conn.execute(
            text("UPDATE norms SET repeal_date='20210402' WHERE id=:i"),
            {"i": LEY_30_1992_ID},
        )
    insert_norm(LEY_39_2015_ID, title="Ley 39/2015")
    insert_relation(
        LEY_39_2015_ID,
        LEY_30_1992_ID,
        "REPEALS",
        label="DEROGA",
        detail=", en la forma indicada, la Ley 30/1992, de 26 de noviembre",
        direction="anteriores",
    )

    with db.session_scope() as conn:
        ctx = ley30.get_ley30_repeal_context(conn)

    assert ctx["target_id"] == LEY_30_1992_ID
    assert ctx["status"] == "REPEALED"
    assert ctx["boe_raw_repeal_date"] == "2021-04-02"
    assert ctx["effective_repeal_date"] is None
    # Graph repeal evidence surfaces Ley 39/2015, flagged as the full repeal.
    rep_ids = [r["id"] for r in ctx["repealing_norms"]]
    assert LEY_39_2015_ID in rep_ids
    assert ctx["repealing_norms"][0]["id"] == LEY_39_2015_ID
    assert ctx["repealing_norms"][0]["is_full_repeal"] is True
    # Replacement context always lists both 2015 laws.
    repl_ids = [r["id"] for r in ctx["replacement_norms"]]
    assert repl_ids == [LEY_39_2015_ID, LEY_40_2015_ID]


def test_repeal_context_missing_norm(db):
    with db.session_scope() as conn:
        ctx = ley30.get_ley30_repeal_context(conn)
    assert ctx["status"] == "UNKNOWN"
    assert ctx["boe_raw_repeal_date"] is None
    assert len(ctx["replacement_norms"]) == 2


# --- Cleanup-impact simulator -----------------------------------------------


def test_cleanup_impact_does_not_naively_subtract(db, insert_norm, insert_relation):
    insert_norm(LEY_30_1992_ID, title="Ley 30/1992", derog="S")
    insert_norm("DEAD2", derog="S")  # another repealed norm
    # L_only: cites only Ley 30/1992 -> fully cleaned by the cleanup.
    insert_norm("L_ONLY")
    insert_relation("L_ONLY", LEY_30_1992_ID, "CITES")
    # L_both: cites Ley 30/1992 AND another dead norm -> stays dirty after cleanup.
    insert_norm("L_BOTH")
    insert_relation("L_BOTH", LEY_30_1992_ID, "CITES")
    insert_relation("L_BOTH", "DEAD2", "CITES")
    # L_other: cites only another dead norm -> unaffected, still dirty.
    insert_norm("L_OTHER")
    insert_relation("L_OTHER", "DEAD2", "CITES")

    with db.session_scope() as conn:
        res = ley30.compute_ley30_cleanup_impact(conn, scope="state")

    # before: L_ONLY, L_BOTH, L_OTHER all cite some dead norm = 3
    assert res["before"]["live_norms_citing_dead_law"] == 3
    # after removing Ley 30/1992 edges: L_BOTH (DEAD2), L_OTHER (DEAD2) still dirty = 2
    assert res["after_simulated_cleanup"]["live_norms_still_citing_dead_law"] == 2
    # fully cleaned = before - after = 1 (L_ONLY only)
    assert res["after_simulated_cleanup"]["fully_cleaned_norms"] == 1
    # direct citers = L_ONLY, L_BOTH = 2 (NOT subtracted naively)
    assert res["ley_30_1992"]["direct_live_citers"] == 2
    assert res["denominator_live_norms"] == 3  # L_ONLY, L_BOTH, L_OTHER (dead norms excluded)


# --- Replacement classifier -------------------------------------------------


def test_classifier_procedure_text_to_ley_39():
    s = classify_ley30_replacement("notificación al interesado y plazo del procedimiento")
    assert s.suggestion == LEY_39_2015
    assert s.confidence == "high"
    assert s.matched_ley_39_2015


def test_classifier_sector_text_to_ley_40():
    s = classify_ley30_replacement("régimen jurídico del sector público y delegación de competencia")
    assert s.suggestion == LEY_40_2015
    assert s.confidence == "high"


def test_classifier_single_hit_medium():
    s = classify_ley30_replacement("se cita en cuanto al expediente")
    assert s.suggestion == LEY_39_2015
    assert s.confidence == "medium"


def test_classifier_mixed_text_legal_review_low():
    s = classify_ley30_replacement("procedimiento administrativo y régimen jurídico del sector público")
    assert s.suggestion == LEGAL_REVIEW
    assert s.confidence == "low"


def test_classifier_empty_text_legal_review_low():
    s = classify_ley30_replacement("")
    assert s.suggestion == LEGAL_REVIEW
    assert s.confidence == "low"
    assert s.matched_ley_39_2015 == [] and s.matched_ley_40_2015 == []


# --- Priority heuristic -----------------------------------------------------


def test_priority_fully_cleanable_is_high():
    p = classify_priority(
        can_be_fully_cleaned=True, rank="Orden", dead_law_citations_count=1, department="X"
    )
    assert p["priority"] == "High"


def test_priority_high_impact_rank_is_high():
    p = classify_priority(
        can_be_fully_cleaned=False, rank="Ley Orgánica", dead_law_citations_count=3, department="X"
    )
    assert p["priority"] == "High"


def test_priority_multiple_dead_citations_is_medium():
    p = classify_priority(
        can_be_fully_cleaned=False, rank="Orden", dead_law_citations_count=4, department="X"
    )
    assert p["priority"] == "Medium"


def test_priority_low_default():
    p = classify_priority(
        can_be_fully_cleaned=False, rank="Orden", dead_law_citations_count=1, department="X"
    )
    assert p["priority"] == "Low"
