# Backend — BOE Knowledge Graph

FastAPI + SQLite backend that ingests the BOE consolidated-legislation corpus, normalizes it into a
directed knowledge graph, and serves the four executive briefings.

## Layout

```
app/
  api/        FastAPI routers + dependencies
  core/       config (paths, scope defaults, BOE base URL)
  db/         SQLite engine + schema bootstrap
  models/     SQLAlchemy Core table definitions
  schemas/    Pydantic response models (API contract docs)
  services/   boe_client, parsers, lifecycle, relation_normalizer, ingestion, briefings
  utils/      disk cache
scripts/      ingest.py, compute_briefings.py, export_sample.py (Typer CLIs)
tests/        pytest suite + bundled fixtures
```

## Setup

```bash
uv venv .venv --python 3.9
uv pip install --python .venv/bin/python -e ".[dev]"
```

## Common commands

```bash
.venv/bin/python -m scripts.ingest sample          # sample ingestion (fixture fallback)
.venv/bin/python -m scripts.ingest sample --no-api  # fixtures only (offline)
.venv/bin/python -m scripts.ingest full             # full corpus (slow, resumable)
.venv/bin/python -m scripts.compute_briefings --scope state
.venv/bin/python -m scripts.export_sample           # refresh fixtures from live API
.venv/bin/uvicorn app.main:app --reload --port 8000
.venv/bin/python -m pytest
```

## Configuration (environment variables)

| Var | Default | Purpose |
| --- | --- | --- |
| `BOE_DB_PATH` | `data/processed/boe_graph.db` | SQLite path (tests set a temp path) |
| `BOE_API_BASE` | official BOE API | API base URL |
| `BOE_DELAY` | `0.4` | polite delay between live requests (s) |
| `BOE_TIMEOUT` | `30` | request timeout (s) |
| `BOE_MAX_RETRIES` | `4` | tenacity retry attempts |
| `BOE_SAMPLE_RECENT` | `40` | recent norms pulled in sample mode |

No API key is required.
