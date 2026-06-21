## ADDED Requirements

### Requirement: Norm node model
The system SHALL model each BOE consolidated norm as a node storing its identifier, title,
rank, scope, department, key dates, raw lifecycle fields, derived lifecycle status, and
BOE URLs, preserving the raw JSON for auditability.

#### Scenario: Norm persisted with raw fields
- **WHEN** a norm's metadata is ingested
- **THEN** the norm row stores both raw BOE status fields and the derived lifecycle status

### Requirement: Lifecycle status derivation
The system SHALL compute a simplified lifecycle status from raw BOE fields using this
precedence: `ANNULLED` when `estatus_anulacion == "S"`, else `REPEALED` when
`estatus_derogacion == "S"`, else `EXPIRED` when `vigencia_agotada == "S"`, else `LIVE`.
It SHALL set `is_live` true only for `LIVE` and `is_repealed` true for
`REPEALED`/`ANNULLED`/`EXPIRED`.

#### Scenario: Repealed norm
- **WHEN** a norm has `estatus_derogacion == "S"` and no annulment
- **THEN** its lifecycle status is `REPEALED`, `is_live` is false, `is_repealed` is true

#### Scenario: Annulled takes precedence
- **WHEN** a norm has both `estatus_anulacion == "S"` and `estatus_derogacion == "S"`
- **THEN** its lifecycle status is `ANNULLED`

#### Scenario: Expired validity
- **WHEN** a norm has `vigencia_agotada == "S"` and no annulment or derogation
- **THEN** its lifecycle status is `EXPIRED`

#### Scenario: Live norm
- **WHEN** a norm has none of the negative status flags set
- **THEN** its lifecycle status is `LIVE` and `is_live` is true

### Requirement: Relation normalization
The system SHALL normalize raw Spanish relation labels into one of `AMENDS`, `REPEALS`,
`CITES`, or `OTHER`, classifying explicit derogations as `REPEALS` (not `AMENDS`),
classifying unknown labels as `OTHER`, and always preserving the raw label and raw detail.

#### Scenario: Modify labels map to AMENDS
- **WHEN** a raw label is a modification term such as `MODIFICA` or `SE MODIFICA`
- **THEN** the normalized relation type is `AMENDS`

#### Scenario: Derogation labels map to REPEALS
- **WHEN** a raw label is a derogation term such as `DEROGA` or `QUEDA DEROGADA`
- **THEN** the normalized relation type is `REPEALS`

#### Scenario: Citation labels map to CITES
- **WHEN** a raw label is a citation term such as `CITA` or `REFERENCIA`
- **THEN** the normalized relation type is `CITES`

#### Scenario: Unknown labels map to OTHER
- **WHEN** a raw label does not match any known mapping
- **THEN** the normalized relation type is `OTHER` and the raw label is retained

### Requirement: Edge direction from references
The system SHALL derive directed edges from `analisis/referencias`: for current norm A,
relations under `anteriores` produce `A --TYPE--> B` and relations under `posteriores`
produce `C --TYPE--> A`, recording `api_direction` and `current_norm_id`, and deduplicating
equivalent edges.

#### Scenario: Anterior relation direction
- **WHEN** current norm A has an `anteriores` relation `MODIFICA` targeting B
- **THEN** the system records the edge `A --AMENDS--> B`

#### Scenario: Posterior relation direction
- **WHEN** current norm B has a `posteriores` relation `SE MODIFICA` from A
- **THEN** the system records the edge `A --AMENDS--> B`

#### Scenario: Duplicate edges deduplicated
- **WHEN** the same `A --AMENDS--> B` edge is derived from both directions
- **THEN** only one edge is persisted
