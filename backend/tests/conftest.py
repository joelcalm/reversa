"""Pytest fixtures: an isolated temp SQLite DB and synthetic-graph helpers."""
from __future__ import annotations

from typing import Callable, Optional

import pytest

from app.services.lifecycle import compute_lifecycle


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """Provide a fresh, isolated SQLite database for each test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("BOE_DB_PATH", str(db_path))

    # Import after env is set; reset the cached engine so it picks up the temp path.
    from app.db import session as session_mod

    session_mod.reset_engine()
    session_mod.init_db()
    yield session_mod
    session_mod.reset_engine()


@pytest.fixture()
def insert_norm(db) -> Callable:
    from app.services.ingestion import _upsert_norm
    from app.services.parsers import ParsedNorm

    def _factory(
        norm_id: str,
        title: Optional[str] = None,
        scope: str = "Estatal",
        derog: str = "N",
        anul: str = "N",
        expired: str = "N",
        rank: str = "Ley",
        department: str = "Test Dept",
        publication_date: str = "20200101",
    ) -> None:
        life = compute_lifecycle(derog, anul, expired)
        norm = ParsedNorm(
            id=norm_id,
            title=title or f"Norm {norm_id}",
            scope=scope,
            rank=rank,
            department=department,
            publication_date=publication_date,
            estatus_derogacion=derog,
            estatus_anulacion=anul,
            vigencia_agotada=expired,
            lifecycle_status=life.status,
            is_live=life.is_live,
            is_repealed=life.is_repealed,
            url_html=f"https://www.boe.es/buscar/act.php?id={norm_id}",
        )
        with db.session_scope() as conn:
            _upsert_norm(conn, norm)

    return _factory


@pytest.fixture()
def insert_relation(db) -> Callable:
    from app.services.ingestion import _insert_relations
    from app.services.parsers import ParsedRelation

    def _factory(
        source: str,
        target: str,
        relation_type: str,
        label: str = "TEST",
        code: str = "000",
        detail: str = "",
        direction: str = "anteriores",
    ) -> None:
        rel = ParsedRelation(
            source_norm_id=source,
            target_norm_id=target,
            relation_type=relation_type,
            relation_code=code,
            relation_label_raw=label,
            relation_detail_raw=detail,
            api_direction=direction,
            current_norm_id=source,
        )
        with db.session_scope() as conn:
            _insert_relations(conn, [rel])

    return _factory
