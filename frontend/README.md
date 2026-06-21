# Frontend — BOE Knowledge Graph

React + Vite + TypeScript app with Cytoscape.js graph visualizations. Institutional white/green
"Council briefing" theme.

## Setup & run

```bash
npm install
npm run dev      # http://127.0.0.1:5173 (proxies /api to the backend)
npm run build    # type-check + production build to dist/
npm run lint     # tsc --noEmit
```

The dev server proxies `/api` and `/health` to `http://127.0.0.1:8088` by default. Override the target:

```bash
BACKEND_URL=http://127.0.0.1:8090 FRONTEND_PORT=5180 npm run dev
```

## Structure

```
src/
  api/         typed fetch client
  components/   shared UI: states, tables, KPI cards, briefing graph wrapper, hooks
  graph/        Cytoscape GraphView + stylesheet
  pages/        Dashboard, four briefing pages, Graph explorer
  types/        TypeScript types matching the API contract
  styles/       theme.css (CSS variables)
  utils/        CSV export
```

## Pages

- **Dashboard** — KPI cards, four briefing cards, default-scope note, data freshness.
- **Briefing 1–4** — explanation + table/KPIs + Cytoscape subgraph.
- **Graph explorer** — search a norm, open its neighborhood, filter by relation type, inspect nodes.

Graph styling: live norms are green, dead norms (repealed/annulled/expired) are red, unknown nodes
are gray; AMENDS edges are orange, CITES blue, REPEALS red.
