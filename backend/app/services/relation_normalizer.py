"""Normalize raw Spanish BOE relation labels into typed graph edges.

Design goals (auditability first):
- Always keep the raw label and raw detail (callers persist them).
- Classify explicit derogations as REPEALS, never AMENDS.
- Classify unknown labels as OTHER (conservative).
- Keep the mapping table-driven and easy to extend.

Classification order matters: REPEALS is checked before AMENDS so that a label like
"DEROGA" is never swallowed by a broad modification match.
"""
from __future__ import annotations

import unicodedata

AMENDS = "AMENDS"
REPEALS = "REPEALS"
CITES = "CITES"
OTHER = "OTHER"

# Keyword sets are matched against the accent-stripped, upper-cased label.
# Order of evaluation is REPEALS -> AMENDS -> CITES -> OTHER.
REPEAL_KEYWORDS = (
    "DEROGA",
    "DEROGAD",  # derogado / derogada / derogadas
    "DEROGACION",
    "QUEDA DEROGAD",
    "DECLARA LA DEROGACION",
    "DEJA SIN EFECTO",
)

# Aligned with the challenge's AMENDS list (MODIFICA / AÑADE / SUPRIME / REDACTA /
# SUSTITUYE) plus close, unambiguous synonyms. We deliberately exclude "DESARROLLA"
# and "DICTA DE CONFORMIDAD" from AMENDS because those are derivative/citation-style
# references, not edits to the norm's text.
AMEND_KEYWORDS = (
    "MODIFICA",
    "ANADE",  # añade -> anade after accent strip
    "SUPRIME",
    "REDACTA",
    "NUEVA REDACCION",
    "SUSTITUYE",
)

CITE_KEYWORDS = (
    "CITA",
    "REFERENCIA",
    "MENCIONA",
    # Derivative legal-basis references behave like citations in the corpus.
    "DE CONFORMIDAD",
    "AL AMPARO",
    "EN RELACION",
)


def _canonical(label: str) -> str:
    """Upper-case and strip accents for robust keyword matching."""
    if label is None:
        return ""
    text = unicodedata.normalize("NFKD", str(label))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.strip().upper()


def normalize_relation(label: str) -> str:
    """Map a raw relation label to AMENDS | REPEALS | CITES | OTHER."""
    canon = _canonical(label)
    if not canon:
        return OTHER

    # REPEALS first so "DEROGA" / "QUEDA DEROGADA" never fall through to AMENDS.
    for kw in REPEAL_KEYWORDS:
        if kw in canon:
            return REPEALS
    for kw in AMEND_KEYWORDS:
        if kw in canon:
            return AMENDS
    for kw in CITE_KEYWORDS:
        if kw in canon:
            return CITES
    return OTHER
