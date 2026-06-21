"""Export a small sample dataset from the live API into bundled fixtures.

This lets sample ingestion (and tests) run fully offline. It writes:
    backend/tests/fixtures/sample_norms.json     -> list of metadata objects
    backend/tests/fixtures/sample_analyses.json  -> {norm_id: analisis payload}

    python -m scripts.export_sample --recent 20
"""
from __future__ import annotations

import json

import typer

from app.core.config import FIXTURES_DIR, SAMPLE_SEED_IDS
from app.services.boe_client import BoeClient

app = typer.Typer(add_completion=False, help="Export sample fixtures from the BOE API.")


@app.command()
def main(recent: int = typer.Option(15, help="Recent norms to include from the list.")) -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    norms: list = []
    analyses: dict = {}
    seen = set()

    def fetch(nid: str):
        if nid in seen:
            return None
        seen.add(nid)
        try:
            meta = client.get_metadata(nid)
            analysis = client.get_analysis(nid)
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"skip {nid}: {exc}")
            return None
        meta_obj = meta[0] if isinstance(meta, list) and meta else meta
        if meta_obj:
            norms.append(meta_obj)
            analyses[nid] = analysis
        return analysis

    with BoeClient() as client:
        listing = client.list_norms(offset=0, limit=max(recent, 1))
        ids = list(SAMPLE_SEED_IDS)
        for item in listing if isinstance(listing, list) else []:
            nid = item.get("identificador")
            if nid and nid not in ids:
                ids.append(nid)

        neighbors: list = []
        for nid in ids:
            fetch(nid)
            # Expand one hop around the seed norms so briefings 3/4 have live citers.
            data = analyses.get(nid)
            if nid in SAMPLE_SEED_IDS and data:
                block = data[0] if isinstance(data, list) and data else data
                ref = block.get("referencias", {}) if isinstance(block, dict) else {}
                for direction, key in (("anteriores", "anterior"), ("posteriores", "posterior")):
                    for grp in ref.get(direction, []) or []:
                        for it in (grp.get(key, []) if isinstance(grp, dict) else []):
                            cand = it.get("id_norma") if isinstance(it, dict) else None
                            if cand and cand.startswith("BOE-A-") and cand not in ids:
                                neighbors.append(cand)

        for nid in neighbors[:80]:
            fetch(nid)

    (FIXTURES_DIR / "sample_norms.json").write_text(
        json.dumps(norms, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (FIXTURES_DIR / "sample_analyses.json").write_text(
        json.dumps(analyses, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    typer.echo(f"Wrote {len(norms)} norms and {len(analyses)} analyses to {FIXTURES_DIR}")


if __name__ == "__main__":
    app()
