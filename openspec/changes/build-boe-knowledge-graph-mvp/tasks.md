## 1. Repository scaffolding

- [x] 1.1 Create monorepo structure (backend/, frontend/, data/, docs/) and `.gitignore`
- [x] 1.2 Add root README, Makefile, and docker-compose.yml

## 2. Backend core

- [x] 2.1 Create `backend/pyproject.toml` with dependencies and pytest config
- [x] 2.2 Implement `app/core/config.py` (paths, scope defaults, settings)
- [x] 2.3 Implement SQLite schema + engine/session in `app/db/` with indexes
- [x] 2.4 Define SQLAlchemy table models in `app/models/`

## 3. BOE client and parsing

- [x] 3.1 Implement httpx BOE client with retry/backoff, polite delay, disk cache, resume
- [x] 3.2 Implement lifecycle status computation in `app/services/`
- [x] 3.3 Implement relation normalizer (raw label -> AMENDS/REPEALS/CITES/OTHER)
- [x] 3.4 Implement metadata + analisis/referencias parsers with correct edge direction

## 4. Ingestion

- [x] 4.1 Implement ingestion service writing norms/relations/subjects to SQLite
- [x] 4.2 Implement sample mode (key norms + recent) with fixture fallback
- [x] 4.3 Implement full mode (`limit=-1`) with caching/resume
- [x] 4.4 Generate data-quality report (raw label/normalized type counts)
- [x] 4.5 Wire `scripts/ingest.py` and `scripts/export_sample.py` (Typer)

## 5. Briefings

- [x] 5.1 Implement briefing 1 (unreadable) and 2 (omnibus) aggregates
- [x] 5.2 Implement briefing 3 (dead-law dependencies) and 4 (Ley 30/1992 blast radius)
- [x] 5.3 Cache briefing results; wire `scripts/compute_briefings.py`

## 6. API

- [x] 6.1 Implement `/health` and `/api/summary`
- [x] 6.2 Implement the four briefing endpoints
- [x] 6.3 Implement norm search, detail, and neighborhood endpoints
- [x] 6.4 Implement `/api/graph/briefing/{briefing_key}` Cytoscape graphs
- [x] 6.5 Assemble FastAPI app with CORS and routers in `app/main.py`

## 7. Backend tests

- [x] 7.1 Add fixtures under `backend/tests/fixtures/`
- [x] 7.2 Test lifecycle status calculation (all branches)
- [x] 7.3 Test relation normalization (all types + unknown)
- [x] 7.4 Test edge direction (anteriores/posteriores produce same non-reversed edge)
- [x] 7.5 Test briefing logic on a synthetic graph
- [x] 7.6 API smoke tests (/health, /api/summary, briefings)

## 8. Frontend

- [x] 8.1 Scaffold Vite React TS app with package.json, vite config, theme CSS variables
- [x] 8.2 Implement API client and TypeScript types
- [x] 8.3 Implement reusable components (cards, tables, states) and Cytoscape graph component
- [x] 8.4 Implement dashboard page
- [x] 8.5 Implement the four briefing pages
- [x] 8.6 Implement graph explorer page and routing

## 9. Docs and tooling

- [x] 9.1 Write docs/design-doc.md, data-model.md, relation-normalization.md, api.md
- [x] 9.2 Write docs/video-script.md (5-minute Council demo)
- [x] 9.3 Finalize root + backend + frontend READMEs and Makefile targets

## 10. Validation

- [x] 10.1 Run backend tests and import checks
- [x] 10.2 Run sample ingestion + compute end-to-end
- [x] 10.3 Backend smoke test and frontend build
