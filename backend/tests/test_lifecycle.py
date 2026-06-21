"""Lifecycle status derivation tests (all branches + precedence)."""
from app.services.lifecycle import (
    ANNULLED,
    EXPIRED,
    LIVE,
    REPEALED,
    compute_lifecycle,
)


def test_repealed():
    r = compute_lifecycle(estatus_derogacion="S", estatus_anulacion="N", vigencia_agotada="N")
    assert r.status == REPEALED
    assert r.is_live is False
    assert r.is_repealed is True


def test_annulled():
    r = compute_lifecycle(estatus_derogacion="N", estatus_anulacion="S", vigencia_agotada="N")
    assert r.status == ANNULLED
    assert r.is_repealed is True


def test_expired():
    r = compute_lifecycle(estatus_derogacion="N", estatus_anulacion="N", vigencia_agotada="S")
    assert r.status == EXPIRED
    assert r.is_repealed is True


def test_live():
    r = compute_lifecycle(estatus_derogacion="N", estatus_anulacion="N", vigencia_agotada="N")
    assert r.status == LIVE
    assert r.is_live is True
    assert r.is_repealed is False


def test_annulment_takes_precedence_over_derogation():
    r = compute_lifecycle(estatus_derogacion="S", estatus_anulacion="S", vigencia_agotada="S")
    assert r.status == ANNULLED


def test_missing_fields_default_live():
    r = compute_lifecycle()
    assert r.status == LIVE


def test_case_and_whitespace_tolerant():
    r = compute_lifecycle(estatus_derogacion=" s ")
    assert r.status == REPEALED
