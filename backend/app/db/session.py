"""SQLite engine creation and schema bootstrap."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import Connection

from app.core.config import ensure_directories, get_database_url
from app.models.tables import metadata

_engine: Optional[Engine] = None


def _build_engine() -> Engine:
    ensure_directories()
    # timeout: wait up to 30s if another process (e.g. uvicorn) has the DB locked.
    engine = create_engine(
        get_database_url(),
        future=True,
        connect_args={"timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # DELETE journal: single-file DB, fewer WAL sidecar issues on WSL2 / interrupted runs.
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    return engine


def get_engine() -> Engine:
    """Return a process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def reset_engine() -> None:
    """Dispose the cached engine. Used by tests that switch DB paths."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db() -> None:
    """Create all tables/indexes if they do not exist."""
    metadata.create_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Connection]:
    """Transactional connection scope: commit on success, rollback on error."""
    engine = get_engine()
    with engine.begin() as conn:  # begin() commits/rolls back automatically
        yield conn
