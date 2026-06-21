## ADDED Requirements

### Requirement: Health and summary endpoints
The API SHALL expose `GET /health` returning service status and `GET /api/summary`
returning total norms, total relations, relation counts by type, lifecycle counts,
default scope, and last ingestion timestamp when available.

#### Scenario: Health check
- **WHEN** a client calls `GET /health`
- **THEN** the API responds with a success status payload

#### Scenario: Summary structure
- **WHEN** a client calls `GET /api/summary`
- **THEN** the response includes total_norms, total_relations, relation_counts_by_type, and lifecycle_counts

### Requirement: Briefing endpoints
The API SHALL expose one endpoint per briefing returning the computed briefing payload,
accepting a `scope` parameter and (where applicable) a `limit` parameter.

#### Scenario: Unreadable laws endpoint
- **WHEN** a client calls `GET /api/briefings/unreadable-laws?scope=state&limit=5`
- **THEN** the response contains the ranked top norms with their amending counts

#### Scenario: Dead-law endpoint structure
- **WHEN** a client calls `GET /api/briefings/dead-law-dependencies?scope=state`
- **THEN** the response includes live_norms_count, live_norms_citing_repealed_count, percentage, and top ghost norms

#### Scenario: Blast radius endpoint structure
- **WHEN** a client calls `GET /api/briefings/ley-30-1992-blast-radius?scope=state`
- **THEN** the response includes the target metadata, total live direct citers, and the citing norms list

### Requirement: Norm search and detail endpoints
The API SHALL expose `GET /api/norms` with search/status/rank/scope/limit/offset filters,
`GET /api/norms/{norm_id}` returning details plus basic graph metrics, and
`GET /api/norms/{norm_id}/neighborhood` returning Cytoscape-friendly nodes and edges.

#### Scenario: Search norms
- **WHEN** a client calls `GET /api/norms?search=<term>`
- **THEN** matching norms are returned with pagination metadata

#### Scenario: Norm neighborhood
- **WHEN** a client calls `GET /api/norms/{norm_id}/neighborhood`
- **THEN** the response contains nodes and edges in Cytoscape format around that norm

### Requirement: Graph endpoint for briefings
The API SHALL expose `GET /api/graph/briefing/{briefing_key}` returning a Cytoscape graph
(`nodes` and `edges` with `data` objects) for each of the four briefings, where nodes
carry lifecycle status/rank/url and edges carry normalized type and raw labels.

#### Scenario: Briefing graph shape
- **WHEN** a client calls `GET /api/graph/briefing/unreadable-laws`
- **THEN** the response has `nodes` and `edges` arrays whose items contain a `data` object with the documented fields
