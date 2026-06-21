"""Ingestion CLI.

Examples:
    python -m scripts.ingest sample            # fast sample (with fixture fallback)
    python -m scripts.ingest sample --no-api   # use bundled fixtures only
    python -m scripts.ingest full              # full corpus (slow)
"""
from __future__ import annotations

import json

import typer

from app.services.ingestion import ingest_full, ingest_sample

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
def full(limit: int = typer.Option(-1, help="List limit; -1 means the full corpus.")) -> None:
    """Ingest the full corpus (can be slow; cached and resumable)."""
    summary = ingest_full(limit=limit)
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
