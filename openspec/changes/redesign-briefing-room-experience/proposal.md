## Why

The platform has seven top-nav destinations (Dashboard, Council Briefing, four separate briefing
pages, Explorer). The challenge requires an integrated web platform where the graph and four
briefings are understandable on one journey — a decision tool for the Council, not a technical
dashboard.

## What Changes

- Replace fragmented navigation with **Briefing Room** (default), **Explorer** (advanced), and
  **Data Quality** (audit).
- Unified `BriefingSection` layout per briefing: executive answer + graph + recommendation panel +
  worklist on one screen.
- Hybrid navigation: scroll anchors across overview + four briefings, plus focus mode per briefing.
- `InteractiveGraph` with search, filters, zoom/fit/reset, aligned edge styling.
- Frontend recommendation heuristics for briefings 1–3; reuse API fields for briefing 4.
- `GET /api/data-quality` for the audit page.
- Deprecate Dashboard, Council Briefing slideshow, and standalone briefing routes (redirects).

## Capabilities

### Modified Capabilities
- `frontend`: Briefing Room IA, unified briefing layout, interactive graph, Data Quality page.
- `api`: `GET /api/data-quality` endpoint.

## Impact

- Frontend: major refactor of routing and pages; reuse existing APIs and EvidenceDrawer.
- Backend: one new read-only endpoint; no breaking API changes.
