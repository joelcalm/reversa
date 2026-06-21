"""Derive a simplified lifecycle status from raw BOE status fields.

Precedence (most severe first):
    ANNULLED  if estatus_anulacion == "S"
    REPEALED  if estatus_derogacion == "S"
    EXPIRED   if vigencia_agotada == "S"
    LIVE      otherwise

This is a pure function so it is trivially unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

LIVE = "LIVE"
REPEALED = "REPEALED"
ANNULLED = "ANNULLED"
EXPIRED = "EXPIRED"

DEAD_STATUSES = frozenset({REPEALED, ANNULLED, EXPIRED})


def _is_yes(value: Optional[str]) -> bool:
    """BOE encodes booleans as the string "S" (sí). Be tolerant of casing/whitespace."""
    if value is None:
        return False
    return str(value).strip().upper() == "S"


@dataclass(frozen=True)
class LifecycleResult:
    status: str
    is_live: bool
    is_repealed: bool


def compute_lifecycle(
    estatus_derogacion: Optional[str] = None,
    estatus_anulacion: Optional[str] = None,
    vigencia_agotada: Optional[str] = None,
) -> LifecycleResult:
    if _is_yes(estatus_anulacion):
        status = ANNULLED
    elif _is_yes(estatus_derogacion):
        status = REPEALED
    elif _is_yes(vigencia_agotada):
        status = EXPIRED
    else:
        status = LIVE

    return LifecycleResult(
        status=status,
        is_live=status == LIVE,
        is_repealed=status in DEAD_STATUSES,
    )
