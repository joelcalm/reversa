# Project: BOE Knowledge Graph

## Mission
Convert the BOE consolidated-legislation corpus into a directed knowledge graph and serve a web
platform that answers four executive briefings for a non-technical (Council of Ministers) audience.

## Tech stack
- Backend: Python 3.9+, FastAPI, SQLAlchemy Core, SQLite
- Ingestion: httpx + tenacity, disk cache, Typer CLIs
- Frontend: React + Vite + TypeScript, Cytoscape.js
- Monorepo: `backend/`, `frontend/`, `data/`, `docs/`, `openspec/`

## Conventions
- "Norm" (not "law") for all BOE entities.
- Directed graph edges: `AMENDS | REPEALS | CITES | OTHER`; raw labels always preserved.
- Lifecycle precedence: ANNULLED → REPEALED → EXPIRED → LIVE.
- Default briefing scope: state-level norms (ámbito "Estatal").
- Briefings computed from SQLite — never hard-coded. Auditability first.
- No secrets / no API key.

## Capabilities (see openspec/specs/)
`ingestion`, `graph-model`, `briefings`, `api`, `frontend`.

## Active change
`openspec/changes/build-boe-knowledge-graph-mvp/` — the MVP build.
