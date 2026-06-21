## Why

The BOE consolidated-legislation corpus encodes decades of amendments, repeals and
citations as unstructured relationships scattered across thousands of norms. Decision
makers (e.g. the Council of Ministers) cannot easily see which norms have become
unreadable from over-amendment, which "omnibus" acts caused the most disorder, how
much live law depends on already-dead law, or the blast radius of a landmark repeal
such as Ley 30/1992. We turn that corpus into an explicit, auditable knowledge graph
and surface four executive briefings on top of it.

## What Changes

- Ingest the BOE consolidated-legislation corpus via the public open-data API
  (`metadatos`, `analisis`, especially `analisis/referencias`) with disk caching,
  retry/backoff, polite rate limiting, and resumable sample/full modes.
- Normalize raw Spanish relation labels into a typed directed graph
  (`AMENDS`, `REPEALS`, `CITES`, `OTHER`) while preserving raw labels/detail for audit.
- Compute a simplified lifecycle status (`LIVE`, `REPEALED`, `ANNULLED`, `EXPIRED`)
  from raw BOE status fields.
- Persist norms, relations, subjects, and cached briefing results to SQLite.
- Compute four briefings from the graph (no hard-coded results):
  unreadable laws, omnibus laws, dead-law dependencies, Ley 30/1992 blast radius.
- Expose a FastAPI backend with summary, briefing, norm search, neighborhood, and
  Cytoscape-friendly graph endpoints.
- Deliver a polished React + Vite + TypeScript frontend with a dashboard, the four
  briefing pages, and a general graph explorer using Cytoscape.js.
- Provide tests for lifecycle, relation normalization, edge direction, briefing logic,
  and API smoke; plus docs (design doc, data model, normalization, video script, api).

## Capabilities

### New Capabilities
- `ingestion`: Reproducible, cached, resumable ingestion of the BOE corpus into SQLite.
- `graph-model`: Norm/relation data model, lifecycle status, and relation normalization.
- `briefings`: The four executive briefing computations over the graph.
- `api`: FastAPI HTTP surface for summary, briefings, norms, neighborhoods, and graph.
- `frontend`: React/Vite/TS web app with dashboard, briefing pages, and graph explorer.

### Modified Capabilities
<!-- None: this is a greenfield repository. -->

## Impact

- New monorepo: `backend/` (FastAPI + SQLite + ingestion), `frontend/` (React/Vite/TS),
  `data/` (cache/processed/samples), `docs/`, and `openspec/` artifacts.
- New dependencies: fastapi, uvicorn, httpx, pydantic, sqlalchemy, tenacity, typer,
  pytest (backend); react, vite, typescript, cytoscape (frontend).
- External dependency: BOE open-data API (no API key required).
- Tooling: Makefile, docker-compose, `.gitignore` to exclude caches/venv/node_modules.
