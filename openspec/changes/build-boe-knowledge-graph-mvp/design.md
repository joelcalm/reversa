## Context

The BOE publishes a consolidated-legislation open-data API (no API key) exposing each
norm's `metadatos`, `analisis` (subjects, notes, references), `metadata-eli`, and `texto`.
The `analisis/referencias` block holds the inter-norm relationships (amends, repeals,
cites) split into `anteriores` (this norm acting on earlier norms) and `posteriores`
(later norms acting on this norm). We must turn this into a typed, directed knowledge
graph and answer four executive briefings for a non-technical audience, with correctness
and auditability as first-class concerns. Constraints: Python 3.9+, FastAPI, SQLite,
React/Vite/TS, Cytoscape.js, monorepo, reproducible and demo-ready.

## Goals / Non-Goals

**Goals:**
- Correct, directed graph (no reversed edges) with transparent relation normalization.
- Reproducible, cached, resumable ingestion (sample + full).
- The four briefings computed from the SQLite graph, never hard-coded.
- Clean institutional frontend that tells the story to a minister.
- Tests covering lifecycle, normalization, edge direction, briefing logic, and API.

**Non-Goals:**
- Full-text search/NLP over `texto`; we use structured `analisis` references only.
- Real-time sync with BOE; ingestion is a batch/cron-style job.
- Authentication, multi-user, or production-grade horizontal scaling.

## Decisions

- **SQLAlchemy Core + raw SQLite over an ORM-heavy approach.** The data model is small and
  read-mostly; SQLAlchemy gives us schema/indexes and safe queries while keeping briefing
  SQL explicit and auditable. Alternative (SQLModel/ORM relationships) added indirection
  without benefit for aggregate graph queries.
- **Relation normalization as a pure, table-driven function.** A keyword map produces
  `AMENDS|REPEALS|CITES|OTHER`. Derogation is checked before modification so "DEROGA" never
  collapses into AMENDS. Raw label + detail are always stored. This is easy to test and to
  extend, and it powers the data-quality report.
- **Direction handled at parse time.** `anteriores` → current is source; `posteriores` →
  current is target. We store `api_direction` and `current_norm_id` for audit, and a UNIQUE
  constraint deduplicates equivalent edges discovered from both endpoints. This is the most
  error-prone part, so it has dedicated tests asserting non-reversed edges.
- **Briefings as SQL aggregates over `relations` + `norms`.** Incoming/outgoing AMENDS
  counts, CITES-to-repealed joins, and the Ley 30/1992 worklist are plain GROUP BY / JOIN
  queries, cached as JSON in `briefing_results`. Recompute is decoupled from ingestion.
- **httpx client with tenacity retry, disk cache, polite delay.** Cache key = endpoint +
  id, stored under `data/cache/boe/`. Presence of a cache file short-circuits the network,
  enabling resume and avoiding API hammering during development. Sample mode falls back to
  bundled fixtures if the API is unreachable so the demo always works.
- **Typer CLI scripts** (`ingest.py`, `compute_briefings.py`, `export_sample.py`) wrapped by
  a Makefile for the required `make` targets.
- **Cytoscape subgraphs only.** The frontend never loads the whole graph; it requests
  backend-built subgraphs (briefing graphs, neighborhoods) to stay responsive.

## Risks / Trade-offs

- [BOE API shape may differ from assumptions / be partially undocumented] → Parsers are
  defensive (tolerate missing keys, varied field names), keep raw JSON, and classify unknown
  labels as OTHER; a data-quality report surfaces unmapped labels for quick mapping updates.
- [Full ingestion is large and slow] → Sample mode is the primary demo path and is fully
  end-to-end; full mode is cached/resumable so it can run incrementally.
- [Scope/status fields missing or inconsistent] → Lifecycle defaults to LIVE only when no
  negative flag is set; scope filtering tolerates nulls and never crashes.
- [Reversed edges would silently corrupt every briefing] → Direction has explicit unit tests
  using synthetic `anteriores`/`posteriores` fixtures that must yield identical, non-reversed
  edges.
- [API rate limits / transient errors] → tenacity backoff + polite delay + caching.

## Migration Plan

Greenfield; no migration. Deploy = run `make setup`, then `make ingest-sample` (or
`ingest-full`), `make compute`, `make backend`, and `make frontend`. SQLite file lives under
`data/processed/` and is disposable/regenerable; rollback is deleting and re-ingesting.

## Open Questions

- Exact JSON field names for some `analisis` sub-structures may need adjustment after first
  live fetch; handled defensively and documented in `docs/relation-normalization.md`.
