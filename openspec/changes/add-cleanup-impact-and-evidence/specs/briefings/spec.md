## ADDED Requirements

### Requirement: Ley 30/1992 repeal context
The system SHALL provide a deterministic, auditable repeal-context object for
`BOE-A-1992-26318` that separates (a) the raw BOE repeal-date field, (b) graph-derived
`REPEALS` evidence, and (c) the documented 2015 replacement context (Ley 39/2015 + Ley
40/2015). The helper SHALL NOT overwrite raw BOE data and SHALL NOT use replacement norms to
compute the blast radius.

#### Scenario: Raw repeal date preserved, effective date not inferred
- **WHEN** the repeal-context helper runs and the norm has a raw BOE repeal-date field but no derivable effective date
- **THEN** the result reports the raw BOE repeal-date field and a null effective repeal date

#### Scenario: Repealing and replacement norms surfaced
- **WHEN** the graph contains a `REPEALS` edge into `BOE-A-1992-26318` from Ley 39/2015
- **THEN** the result lists that repealing norm with its raw label/detail, and lists Ley 39/2015 + Ley 40/2015 as labelled replacement context

### Requirement: Ley 30/1992 cleanup-impact simulator
The system SHALL compute, from SQLite, how the dead-law-dependency rate changes if only
direct `CITES` edges to `BOE-A-1992-26318` are removed, returning before/after counts and
percentages, the number of fully-cleaned live norms, and remaining dirty norms. It SHALL NOT
naively subtract the direct-citer count from the before count.

#### Scenario: Mixed citers are not over-counted
- **WHEN** a live norm cites both Ley 30/1992 and another repealed norm
- **THEN** removing Ley 30/1992 does not fully clean that norm, and it remains counted in the after total

#### Scenario: Single-dependency citer is fully cleaned
- **WHEN** a live norm cites only Ley 30/1992 among repealed norms
- **THEN** removing Ley 30/1992 fully cleans it and it is counted in fully-cleaned

### Requirement: Heuristic replacement and priority classification
The system SHALL provide a deterministic, accent/case-insensitive heuristic that suggests a
replacement (Ley 39/2015, Ley 40/2015, or legal review) with a confidence level and matched
keywords for audit, and an explainable priority heuristic with a reason. These SHALL be
clearly labelled as heuristics for legal review, never as final legal conclusions.

#### Scenario: Procedure text suggests Ley 39/2015
- **WHEN** the input text contains administrative-procedure keywords and no public-sector keywords
- **THEN** the suggestion is Ley 39/2015 with the matched keywords reported

#### Scenario: Ambiguous or empty text needs legal review
- **WHEN** the input text matches both or neither keyword set
- **THEN** the suggestion is legal review with low confidence

### Requirement: Omnibus diversity explanation and secondary score
The omnibus briefing SHALL keep ranking norms by the number of distinct norms they amend, and
MAY additionally report `department_diversity` and a secondary `omnibus_score` derived from
`target_count` and `subject_diversity`, labelled as secondary indicators.

#### Scenario: Ranking unchanged
- **WHEN** the omnibus briefing is computed
- **THEN** norms are ordered by distinct amended-norm count, and any score is reported as a secondary indicator only
