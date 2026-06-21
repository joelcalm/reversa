# Data Model

## Graph model

```
Node:  Norm
Edges: AMENDS | REPEALS | CITES | OTHER   (directed: source --TYPE--> target)
```

A **Norm** is any BOE consolidated norm — law, organic law, royal decree, order, code, etc. (we use
"norm", not "law"). Every edge keeps its original raw relation label and raw detail text.

### Direction

Derived from `analisis/referencias` for the current norm A:

| Block | Meaning | Edge produced |
| --- | --- | --- |
| `anteriores` | A modifies/repeals/cites an earlier norm B | `A --TYPE--> B` |
| `posteriores` | a later norm C modifies/repeals/cites A | `C --TYPE--> A` |

The same logical edge can be discovered from both sides; it dedupes via a UNIQUE constraint.
`api_direction` and `current_norm_id` are stored for audit.

## SQLite tables

### `norms`
`id` (PK), `title`, `official_number`, `rank_code`, `rank`, `scope_code`, `scope`,
`department_code`, `department`, `disposition_date`, `publication_date`, `effective_date`,
`repeal_date`, `annulment_date`, `exhausted_validity`, `estatus_derogacion`, `estatus_anulacion`,
`vigencia_agotada`, `consolidation_status_code`, `consolidation_status`, `lifecycle_status` (NOT
NULL), `is_live` (NOT NULL), `is_repealed` (NOT NULL), `url_eli`, `url_html`, `last_updated`,
`raw_json`, `created_at`, `updated_at`.

### `relations`
`id` (PK), `source_norm_id` (NOT NULL), `target_norm_id` (NOT NULL), `relation_type` (NOT NULL),
`relation_code`, `relation_label_raw`, `relation_detail_raw`, `api_direction`, `current_norm_id`,
`target_known`, `created_at`. UNIQUE `(source_norm_id, target_norm_id, relation_type,
relation_code, relation_detail_raw)`.

### `subjects`
`code` (PK), `label` (NOT NULL).

### `norm_subjects`
`norm_id`, `subject_code`, PRIMARY KEY `(norm_id, subject_code)`.

### `briefing_results`
`id` (PK), `briefing_key` (NOT NULL), `scope` (NOT NULL), `payload_json` (NOT NULL),
`computed_at` (NOT NULL).

### `raw_relation_labels`
`label` (PK), `normalized_type`, `count` (NOT NULL). Rebuilt at the end of each ingestion to power
the data-quality report.

## Indexes

`relations.source_norm_id`, `relations.target_norm_id`, `relations.relation_type`,
`norms.is_live`, `norms.is_repealed`, `norms.scope`, `norms.lifecycle_status`,
and `(briefing_results.briefing_key, scope)`.

## Lifecycle derivation

```
ANNULLED  if estatus_anulacion == "S"
REPEALED  elif estatus_derogacion == "S"
EXPIRED   elif vigencia_agotada == "S"
LIVE      otherwise
is_live      = status == "LIVE"
is_repealed  = status in {REPEALED, ANNULLED, EXPIRED}
```

Implemented as a pure function in `app/services/lifecycle.py` (unit-tested for every branch and for
annulment precedence). Comparison is case/whitespace tolerant (`"S"`, `" s "`).

## Field mapping (BOE → schema)

| BOE field | Schema column |
| --- | --- |
| `identificador` | `id` |
| `titulo` | `title` |
| `numero_oficial` | `official_number` |
| `rango.{codigo,texto}` | `rank_code`, `rank` |
| `ambito.{codigo,texto}` | `scope_code`, `scope` |
| `departamento.{codigo,texto}` | `department_code`, `department` |
| `fecha_disposicion` | `disposition_date` |
| `fecha_publicacion` | `publication_date` |
| `fecha_vigencia` | `effective_date` |
| `fecha_derogacion` | `repeal_date` |
| `fecha_anulacion` | `annulment_date` |
| `vigencia_agotada` | `exhausted_validity` / `vigencia_agotada` |
| `estado_consolidacion.{codigo,texto}` | `consolidation_status_code`, `consolidation_status` |
| `url_eli` | `url_eli` |
| `url_html_consolidada` | `url_html` |
| `fecha_actualizacion` | `last_updated` |

Dates are stored as the raw BOE `YYYYMMDD` strings and formatted in the UI.
