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
Like above but each item has `target_count` and `subject_diversity`.

### `GET /api/briefings/dead-law-dependencies?scope=state&limit=5`
`{ briefing, scope, live_norms_count, live_norms_citing_repealed_count, percentage,
top_ghost_norms: [{ ..., live_citers }] }`

### `GET /api/briefings/ley-30-1992-blast-radius?scope=state`
`{ briefing, scope, target_id, ley_30_1992: {norm}, total_live_direct_citers,
citing_norms: [{ ..., relation_label_raw, relation_detail_raw }] }` — full worklist (not just top 5).

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
