"""FastAPI dependencies: a short-lived read connection per request."""
from __future__ import annotations

from typing import Iterator

from sqlalchemy.engine import Connection

from app.db.session import get_engine


def get_conn() -> Iterator[Connection]:
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


def normalize_scope(scope: str) -> str:
    """Accept friendly aliases; default unknown values to the state scope."""
    if not scope:
        return "state"
    s = scope.strip().lower()
    if s in ("all", "corpus", "all-corpus", "full"):
        return "all"
    return "state"
