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
make backend        # serve the API at http://127.0.0.1:8088
```

In another terminal:

```bash
make frontend       # serve the UI at http://127.0.0.1:5173
```

Or run both together with `make dev`. Then open <http://127.0.0.1:5173>.

> **Port:** the backend defaults to **8088** (not 8000) so it won't clash with other local
> containers (e.g. Docker services on `:8000`). Override with `make backend BACKEND_PORT=9000` and
> `BACKEND_URL=http://127.0.0.1:9000 make frontend` if needed.

### Without `make`

```bash
# Backend
cd backend
uv venv .venv --python 3.9 && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m scripts.ingest sample
.venv/bin/python -m scripts.compute_briefings --scope state
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8088

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
| `make ingest-full` | Full corpus via **paginated** list endpoint (~12,317 norms) + per-norm analysis. Cached and resumable (`resume=True` skips already-parsed analisis). |
| `make ingest-missing` | Only norms in the API list but **not yet in the DB** — use after a capped 10k run to add the rest without re-fetching analisis for existing norms. |
| `make compute` | Recompute briefings from the existing SQLite (no API calls). |

### Do I need to delete the DB or cache before full ingestion?

**No.** Full ingestion is designed to **add to and refresh** what you already have:

- **Cache (`data/cache/boe/`)** — kept. Already-fetched API responses are reused, so re-runs are fast and polite to the BOE API. Delete only if you want to force a full re-download.
- **SQLite (`data/processed/boe_graph.db`)** — kept. Norms are **upserted** (updated if they already exist). New relations are **inserted**; duplicates are skipped via a unique constraint. Your sample data stays; full ingestion layers the rest of the corpus on top.
- **Briefings** — run `make compute` after full ingestion to refresh cached briefing results.

For a **completely fresh** database (e.g. sample-only experiment you want to discard):

```bash
make clean          # removes DB + API cache
make ingest-full
make compute
```

**Before `make ingest-full`:** stop the backend (`make backend` / `uvicorn`) so nothing else is
writing to the SQLite file. If you see `disk I/O error`, the DB may be corrupted — run `make clean`
and re-ingest (your API cache is kept unless you also delete `data/cache/boe/`).

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

See [`docs/api.md`](docs/api.md). Interactive docs are available at `/docs` when the backend runs (default `http://127.0.0.1:8088/docs`).

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
