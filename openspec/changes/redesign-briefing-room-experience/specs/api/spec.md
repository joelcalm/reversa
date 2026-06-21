## ADDED Requirements

### Requirement: Data quality endpoint
The API SHALL expose `GET /api/data-quality` returning ingestion summary counts, relation type
breakdown, top raw relation labels with normalized types, OTHER label totals, unknown target
relation count, and last ingestion timestamp.

#### Scenario: Data quality structure
- **WHEN** a client calls `GET /api/data-quality`
- **THEN** the response includes total_norms, total_relations, relation_counts_by_type, labels, and unknown_target_relations
