## ADDED Requirements

### Requirement: Cleanup-impact endpoint
The API SHALL expose `GET /api/briefings/ley-30-1992-cleanup-impact` accepting a `scope`
parameter and returning the denominator of live norms, the before counts/percentage, the
Ley 30/1992 direct-citer count and repeal context, and the after-simulated-cleanup
counts/percentage including fully-cleaned and remaining-dirty norms.

#### Scenario: Cleanup-impact structure
- **WHEN** a client calls `GET /api/briefings/ley-30-1992-cleanup-impact?scope=state`
- **THEN** the response includes `denominator_live_norms`, `before`, `ley_30_1992`, and `after_simulated_cleanup` with numbers and percentages

### Requirement: Evidence endpoint
The API SHALL expose `GET /api/briefings/{briefing_key}/evidence` for the four briefing keys,
accepting `norm_id`, `scope`, `limit`, and `offset`, and returning the raw BOE relation edges
behind the briefing (source/target norm metadata and raw relation fields) with `total`,
`limit`, and `offset` for pagination. Unknown briefing keys SHALL return 404.

#### Scenario: Unreadable evidence
- **WHEN** a client calls `GET /api/briefings/unreadable-laws/evidence?norm_id=<target>`
- **THEN** the response lists incoming `AMENDS` edges to that target with raw relation labels/details

#### Scenario: Pagination
- **WHEN** a client calls the evidence endpoint with `limit` and `offset`
- **THEN** the response returns at most `limit` items starting at `offset`, with the full `total`

### Requirement: Worklist replacement and priority fields
The Ley 30/1992 blast-radius worklist SHALL include, per citing norm, the heuristic suggested
replacement with confidence and reason, the dead-law citation count, whether the norm can be
fully cleaned by the Ley 30/1992 cleanup, and an explainable priority with its reason, in
addition to the existing identity/raw-relation fields.

#### Scenario: Worklist row fields
- **WHEN** a client calls `GET /api/briefings/ley-30-1992-blast-radius?scope=state`
- **THEN** each citing norm carries `suggested_replacement`, `suggested_replacement_confidence`, `dead_law_citations_count`, `can_be_fully_cleaned_by_ley30_cleanup`, and `priority`
