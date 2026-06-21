# API Reference

Base URL: `http://127.0.0.1:8088` (local dev default). Interactive docs at `/docs` (Swagger) and `/redoc`.

All briefing endpoints accept `scope` (`state` default, or `all`). Unknown scope values default to
`state`. Endpoints never crash on missing/inconsistent scope fields.

## `GET /health`
Liveness check. `{ "status": "ok", "service": "boe-knowledge-graph", "version": "..." }`

## `GET /api/summary`
```json
{
  "total_norms": 84,
  "total_relations": 2744,
  "relation_counts_by_type": { "AMENDS": 1469, "CITES": 473, "REPEALS": 421, "OTHER": 381 },
  "lifecycle_counts": { "LIVE": 70, "REPEALED": 14 },
  "default_scope": "state",
  "scope_label": "Estatal",
  "last_ingestion_at": "2026-06-21T07:40:33+00:00"
}
```

## Briefings

### `GET /api/briefings/unreadable-laws?scope=state&limit=5`
`{ briefing, scope, items: [{ id, title, rank, department, publication_date, lifecycle_status,
rank_position, amending_count, url_html, ... }] }`

### `GET /api/briefings/omnibus-laws?scope=state&limit=5`
Like above but each item has `target_count` (the ranking criterion), `subject_diversity`, and
the secondary indicators `department_diversity` (distinct departments across amended norms) and
`omnibus_score = target_count × log(1 + subject_diversity)`. Ranking stays by `target_count`.

### `GET /api/briefings/dead-law-dependencies?scope=state&limit=5`
`{ briefing, scope, live_norms_count, live_norms_citing_repealed_count, percentage,
top_ghost_norms: [{ ..., live_citers }] }`

### `GET /api/briefings/ley-30-1992-blast-radius?scope=state`
`{ briefing, scope, target_id, ley_30_1992: {norm}, repeal_context: {...}, total_live_direct_citers,
citing_norms: [{...}] }` — full worklist (not just top 5).

Each `citing_norms` item carries the existing identity + `relation_label_raw` /
`relation_detail_raw`, plus the worklist-intelligence fields:

- `dead_law_citations_count` — distinct repealed norms this live norm cites.
- `can_be_fully_cleaned_by_ley30_cleanup` — true when Ley 30/1992 is its only dead-law citation.
- `suggested_replacement` (`LEY_39_2015` | `LEY_40_2015` | `LEGAL_REVIEW`),
  `suggested_replacement_label`, `suggested_replacement_confidence` (`high|medium|low`),
  `suggested_replacement_reason`, `matched_keywords: { ley_39_2015[], ley_40_2015[] }` — a
  **deterministic keyword heuristic for legal review**, never a legal conclusion.
- `priority` (`High|Medium|Low`) and `priority_reason` — an explainable triage heuristic.

`repeal_context` is the auditable Ley 30/1992 repeal context (see below).

### `GET /api/briefings/ley-30-1992-cleanup-impact?scope=state`
Simulates removing only direct `CITES` edges to Ley 30/1992 and recomputes the dead-law rate
(never a naive `before − direct_citers`).
```json
{
  "briefing": "ley-30-1992-cleanup-impact",
  "scope": "state",
  "denominator_live_norms": 6759,
  "before": { "live_norms_citing_dead_law": 1198, "percentage": 17.72 },
  "ley_30_1992": { "direct_live_citers": 182, "target_id": "BOE-A-1992-26318", "repeal_context": { } },
  "after_simulated_cleanup": {
    "live_norms_still_citing_dead_law": 1102, "percentage": 16.30,
    "fully_cleaned_norms": 96, "remaining_dirty_norms": 1102
  },
  "interpretation": "..."
}
```
`repeal_context` separates three layers and never overwrites raw data:
```json
{
  "target_id": "BOE-A-1992-26318", "status": "REPEALED",
  "boe_raw_repeal_date": "2021-04-02", "effective_repeal_date": null,
  "repealing_norms": [{ "id": "BOE-A-2015-10565", "relation_label_raw": "DEROGA", "is_full_repeal": true, "..." : "..." }],
  "replacement_norms": [
    { "id": "BOE-A-2015-10565", "role": "Common Administrative Procedure", "..." : "..." },
    { "id": "BOE-A-2015-10566", "role": "Public Sector Legal Regime", "..." : "..." }
  ],
  "display_note": "..."
}
```

### `GET /api/briefings/{briefing_key}/evidence?norm_id=<id>&scope=state&limit=50&offset=0`
Audit trail behind a briefing number. `briefing_key ∈ { unreadable-laws, omnibus-laws,
dead-law-dependencies, ley-30-1992-blast-radius }` (404 otherwise). Returns one row per logical
edge so `total` matches the briefing headline (distinct source/target), not raw mirror/event
duplicates. `norm_id` is required for unreadable/omnibus/dead-law; for blast-radius it defaults
to `BOE-A-1992-26318`.
```json
{
  "briefing": "unreadable-laws", "scope": "state", "norm_id": "...",
  "total": 134, "limit": 50, "offset": 0,
  "items": [{
    "source_norm": { "id", "title", "rank", "department", "publication_date", "lifecycle_status", "url_html" },
    "target_norm": { "..." },
    "relation": { "relation_type", "relation_code", "relation_label_raw", "relation_detail_raw", "api_direction", "current_norm_id" }
  }]
}
```

## Norms

### `GET /api/norms?search=&status=&rank=&scope=&limit=50&offset=0`
`{ total, limit, offset, items: [{norm}] }`. `status` is `LIVE|REPEALED|ANNULLED|EXPIRED`.

### `GET /api/norms/{norm_id}`
A norm plus `metrics: { amended_by_count, amends_count, cites_count, cited_by_count }`. 404 if absent.

### `GET /api/norms/{norm_id}/neighborhood?depth=1&relation_type=&limit=200`
Cytoscape graph around the norm.

## Graph

### `GET /api/graph/briefing/{briefing_key}?scope=state`
`briefing_key ∈ { unreadable-laws, omnibus-laws, dead-law-dependencies, ley-30-1992-blast-radius }`.
404 for unknown keys.

### Graph response shape
```json
{
  "nodes": [
    { "data": { "id": "...", "label": "...", "title": "...",
      "lifecycle_status": "LIVE|REPEALED|ANNULLED|EXPIRED|UNKNOWN",
      "rank": "...", "url_html": "...", "is_live": true, "metrics": {} } }
  ],
  "edges": [
    { "data": { "id": "...", "source": "...", "target": "...",
      "relation_type": "AMENDS|REPEALS|CITES|OTHER",
      "relation_label_raw": "...", "relation_detail_raw": "..." } }
  ]
}
```
