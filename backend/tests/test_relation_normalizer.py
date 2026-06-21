"""Relation normalization tests."""
import pytest

from app.services.relation_normalizer import (
    AMENDS,
    CITES,
    OTHER,
    REPEALS,
    normalize_relation,
)


@pytest.mark.parametrize(
    "label",
    ["MODIFICA", "SE MODIFICA", "AÑADE", "SE AÑADE", "SUPRIME", "SE SUPRIME",
     "REDACTA", "SE REDACTA", "SUSTITUYE", "SE SUSTITUYE"],
)
def test_amends(label):
    assert normalize_relation(label) == AMENDS


@pytest.mark.parametrize(
    "label",
    ["DEROGA", "SE DEROGA", "QUEDA DEROGADA", "QUEDA DEROGADO", "DEROGADO", "DEROGADA",
     "SE DECLARA LA DEROGACIÓN"],
)
def test_repeals(label):
    assert normalize_relation(label) == REPEALS


@pytest.mark.parametrize("label", ["CITA", "SE CITA", "REFERENCIA", "MENCIONA"])
def test_cites(label):
    assert normalize_relation(label) == CITES


@pytest.mark.parametrize("label", ["SE DECLARA", "CORRECCIÓN de errores", "", "FOO BAR", None])
def test_other(label):
    assert normalize_relation(label) == OTHER


def test_derogation_not_classified_as_amends():
    # A label combining derogation must resolve to REPEALS, never AMENDS.
    assert normalize_relation("SE DEROGA y modifica") == REPEALS


def test_accent_insensitive():
    assert normalize_relation("añade") == normalize_relation("ANADE") == AMENDS
