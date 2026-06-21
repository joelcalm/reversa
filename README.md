# BOE Knowledge Graph

> Mapping Spain's consolidated legislation as a graph of amendments, repeals and citations — and
> answering four executive briefings on top of it.

This project ingests the **BOE consolidated-legislation** corpus from the public
[BOE open-data API](https://boe.es/datosabiertos/api/legislacion-consolidada), normalizes the
inter-norm relationships into a **directed knowledge graph**, and serves a web platform that helps a
non-technical audience (e.g. the Council of Ministers) understand:

1. **Unreadable laws** — which norms have become hard to read from too many amendments.
2. **Omnibus laws** — which single acts modified the most other norms.
3. **Dead-law dependencies** — how much of the live statute book still cites repealed law.
4. **Ley 30/1992 blast radius** — which live norms still cite the repealed Ley 30/1992 directly.

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.9+, FastAPI, SQLAlchemy Core |
| Database | SQLite |
| Ingestion | httpx + tenacity (retry/backoff), disk cache, Typer CLIs |
| Frontend | React + Vite + TypeScript |
| Graph viz | Cytoscape.js (+ dagre layout) |
| Spec workflow | OpenSpec (`openspec/`) |
| Repo style | monorepo |

## Repository layout

```
backend/    FastAPI app, ingestion, briefings, tests
frontend/   React/Vite/TS app with Cytoscape graphs
data/        cache/ (raw API responses), processed/ (SQLite + report), samples/
docs/        design doc, data model, relation normalization, api, video script
openspec/    proposal, design, specs and tasks for this MVP
```

See [`docs/data-model.md`](docs/data-model.md) for the schema and graph model and
[`docs/design-doc.md`](docs/design-doc.md) for the one-page design.

## Quick start

Prerequisites: Python 3.9+ (with [`uv`](https://github.com/astral-sh/uv) recommended), Node 18+.

```bash
make setup          # create backend venv + install deps, install frontend deps
make ingest-sample  # ingest a small demo set from the live API (fixture fallback)
make compute        # compute the four briefings into SQLite
make backend        # serve the API at http://127.0.0.1:8000
```

In another terminal:

```bash
make frontend       # serve the UI at http://127.0.0.1:5173
```

Or run both together with `make dev`. Then open <http://127.0.0.1:5173>.

> **Port note:** the frontend dev server proxies `/api` to `http://127.0.0.1:8000`. If the backend
> runs elsewhere, set `BACKEND_URL`, e.g. `BACKEND_URL=http://127.0.0.1:8090 make frontend`, and run
> the backend with `make backend BACKEND_PORT=8090`.

### Without `make`

```bash
# Backend
cd backend
uv venv .venv --python 3.9 && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m scripts.ingest sample
.venv/bin/python -m scripts.compute_briefings --scope state
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

### Offline / fixtures mode

If the BOE API is unreachable, sample ingestion automatically falls back to bundled fixtures under
`backend/tests/fixtures/`. To force fixtures-only ingestion:

```bash
make ingest-sample-offline   # python -m scripts.ingest sample --no-api
```

## Ingestion modes

| Command | What it does |
| --- | --- |
| `make ingest-sample` | Seed norms (incl. Ley 30/1992, Leyes 39/2015 & 40/2015) + recent norms + one hop of neighbours. Fast, demo-ready, fixture fallback. |
| `make ingest-full` | Full corpus via the list endpoint (`limit=-1`) + per-norm analysis. Cached and resumable. Slow. |
| `make compute` | Recompute briefings from the existing SQLite (no API calls). |

Raw API responses are cached under `data/cache/boe/`, so re-running ingestion is fast and resumable
and never hammers the API. The SQLite database is written to `data/processed/boe_graph.db` and a
data-quality report to `data/processed/data_quality_report.json`.

## Tests

```bash
make test     # pytest: lifecycle, normalization, edge direction, briefings, API smoke
make lint     # ruff (backend) + tsc (frontend)
```

The test suite specifically guards against **reversed graph edges** (the most safety-critical part),
using synthetic `anteriores`/`posteriores` payloads that must yield the same non-reversed edge.

## The four briefings (definitions)

All briefings are computed from the SQLite graph — never hard-coded.

1. **Unreadable laws**: rank norms by `COUNT(DISTINCT source)` of incoming `AMENDS` edges.
2. **Omnibus laws**: rank norms by `COUNT(DISTINCT target)` of outgoing `AMENDS` edges.
3. **Dead-law dependencies**: of all live norms in scope, the share that have a `CITES` edge to a
   repealed/annulled/expired norm; plus the top "ghost" norms most cited by live norms.
   (Amendments and repeals are deliberately excluded — citations only.)
4. **Ley 30/1992 blast radius**: every **live** norm with a `CITES` edge to `BOE-A-1992-26318`.

Default scope is **state-level** norms (ámbito "Estatal"); an `all` scope is also supported.

## API

See [`docs/api.md`](docs/api.md). Interactive docs are available at `/docs` when the backend runs.

## Limitations

- We use the structured `analisis/referencias` block only — not NLP over the full `texto`.
- Sample mode ingests a connected subset; absolute briefing numbers reflect that subset. Run
  `make ingest-full` for corpus-wide figures (slower).
- Relation labels not in the mapping are conservatively classified as `OTHER`; raw labels are always
  retained and surfaced in the data-quality report so the mapping is easy to extend.
- "Targets" referenced by a norm that have not themselves been ingested appear as `UNKNOWN` nodes.

## Deployment notes

- Local: `make dev`. Containerized: `docker compose up --build` (populate the DB first via
  `make ingest-sample && make compute`, since the DB lives in the mounted `./data` volume).
- No API key or secrets are required. There is no `.env` with secrets.
- The SQLite DB and raw cache are git-ignored; only small fixtures are committed.

## OpenSpec artifacts

- Change: `openspec/changes/build-boe-knowledge-graph-mvp/` (`proposal.md`, `design.md`,
  `tasks.md`, and capability specs under `specs/`).
- Capabilities specified: `ingestion`, `graph-model`, `briefings`, `api`, `frontend`.
