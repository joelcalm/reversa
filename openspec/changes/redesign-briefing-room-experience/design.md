# Design — Briefing Room UX

## Information architecture

- `/` — Briefing Room (overview + four anchored briefing sections)
- `/briefing/:key` — focus mode (single briefing full-width)
- `/explorer` — advanced neighborhood exploration
- `/data-quality` — engineering audit page

Redirects from legacy `/briefings/*` and `/council` to anchors or focus routes.

## BriefingSection

Shared layout: header (executive Q/A) → graph + recommendation split → table/worklist.
Selection syncs across table rows, graph nodes, and recommendation panel.

## Graph strategy

Use `/api/norms/{id}/neighborhood` centred on the selected ranked item (not aggregate
`/api/graph/briefing/{key}`). Briefing 4 uses incoming CITES on `BOE-A-1992-26318` with
worklist-based node coloring.

## Recommendations

Frontend-only pure functions for briefings 1–3. Briefing 4 uses existing API priority/replacement
fields from `ley30.py`.

## Data Quality

`GET /api/data-quality` reads `raw_relation_labels`, summary stats, and `target_known=0` count
from SQLite.
