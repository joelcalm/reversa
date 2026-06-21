"""Ingestion CLI.

Examples:
    python -m scripts.ingest sample            # fast sample (with fixture fallback)
    python -m scripts.ingest sample --no-api   # use bundled fixtures only
    python -m scripts.ingest full              # full corpus via pagination (~12k+ norms)
    python -m scripts.ingest missing           # only norms not yet in the DB
"""
from __future__ import annotations

import json

import typer

from app.core.config import LIST_PAGE_SIZE
from app.services.ingestion import ingest_full, ingest_missing, ingest_sample

app = typer.Typer(add_completion=False, help="Ingest the BOE corpus into SQLite.")


@app.command()
def sample(
    api: bool = typer.Option(True, help="Use the live BOE API (falls back to fixtures)."),
    recent: int = typer.Option(40, help="Number of recent norms to pull from the list."),
) -> None:
    """Ingest a small, demo-ready sample."""
    summary = ingest_sample(use_api=api, recent_count=recent)
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))


@app.command()
def full(
    page_size: int = typer.Option(LIST_PAGE_SIZE, help="List page size for pagination."),
    resume: bool = typer.Option(
        True,
        help="Skip analisis fetch for norms already parsed in the DB.",
    ),
) -> None:
    """Ingest the full corpus (paginated; limit=-1 alone caps at 10_000)."""
    summary = ingest_full(page_size=page_size, resume=resume)
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))


@app.command()
def missing(
    page_size: int = typer.Option(LIST_PAGE_SIZE, help="List page size for pagination."),
) -> None:
    """Ingest only norms missing from the DB (e.g. after a capped 10k full run)."""
    summary = ingest_missing(page_size=page_size)
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
