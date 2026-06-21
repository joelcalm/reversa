"""Recompute and cache the four briefings from the existing SQLite database.

    python -m scripts.compute_briefings            # state scope
    python -m scripts.compute_briefings --scope all
"""
from __future__ import annotations

import json

import typer

from app.db.session import init_db
from app.services.briefings import compute_all_briefings

app = typer.Typer(add_completion=False, help="Compute briefings from SQLite.")


@app.command()
def main(scope: str = typer.Option("state", help="state | all")) -> None:
    init_db()
    result = compute_all_briefings(scope=scope)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
