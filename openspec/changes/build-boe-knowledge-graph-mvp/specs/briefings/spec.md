## ADDED Requirements

### Requirement: Briefing 1 - Unreadable laws
The system SHALL rank norms by the number of distinct norms that amend them (incoming
`AMENDS` edges) and return the top N, with each norm's BOE id, title, rank, department,
publication date, lifecycle status, distinct amending-norm count, and BOE URL.

#### Scenario: Rank by incoming AMENDS
- **WHEN** norm X is amended by distinct norms A, B, C
- **THEN** X's amending count is 3 and X is ranked accordingly among the top results

### Requirement: Briefing 2 - Omnibus laws
The system SHALL rank norms by the number of distinct norms they amend (outgoing `AMENDS`
edges) and return the top N, with each norm's BOE id, title, rank, department, publication
date, lifecycle status, distinct target count, and BOE URL.

#### Scenario: Rank by outgoing AMENDS
- **WHEN** norm O amends distinct norms T1, T2, T3
- **THEN** O's target count is 3 and O is ranked accordingly among the top results

### Requirement: Briefing 3 - Dead-law dependencies
The system SHALL compute the percentage of live norms that cite at least one repealed
norm using `CITES`-type edges only (never `AMENDS` or `REPEALS`), returning the numerator
(live norms citing a repealed norm), denominator (total live norms in scope), percentage,
and the top N "ghost" repealed norms most cited by live norms.

#### Scenario: Dead dependency percentage
- **WHEN** live L1 cites repealed R1 and live L2 cites R1 within a scope of total live norms
- **THEN** the numerator counts L1 and L2, the denominator is the total live norms, and R1 leads the ghost ranking

#### Scenario: Only citation edges count
- **WHEN** a live norm only amends or repeals a repealed norm but does not cite it
- **THEN** it is not counted as resting on dead law

### Requirement: Briefing 4 - Ley 30/1992 blast radius
The system SHALL list every live norm that directly cites `BOE-A-1992-26318`, returning
the target norm metadata, the total count, and the full worklist (not just top N) with
each citing norm's id, title, rank, department, publication date, lifecycle status, raw
relation text when available, and BOE URL.

#### Scenario: Blast radius worklist
- **WHEN** live norm L3 directly cites `BOE-A-1992-26318`
- **THEN** L3 appears in the full worklist and the total live direct citers count includes it

### Requirement: Scope filtering and result caching
Briefings SHALL default to state-level scope (norms whose scope is "Estatal") while
allowing an all-corpus scope, SHALL not crash on missing/inconsistent scope fields, and
SHALL cache computed results keyed by briefing and scope for fast retrieval.

#### Scenario: Default state scope
- **WHEN** a briefing is requested without an explicit scope
- **THEN** results are computed over state-level norms and the active scope is reported

#### Scenario: Cached recompute
- **WHEN** the compute step is run against an existing database
- **THEN** briefing results are recomputed and stored without re-ingesting from the API
