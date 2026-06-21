# Design Doc — BOE Knowledge Graph (one page)

## Goal

Turn the BOE consolidated-legislation corpus into a directed, typed **knowledge graph** and answer
four executive briefings for a non-technical audience, with **correctness** and **auditability** as
first-class concerns. Deliverable must be reproducible and demo-ready.

## Data source

Public BOE open-data API (no key): `https://boe.es/datosabiertos/api/legislacion-consolidada`.

- List endpoint (`?limit=-1`) returns full metadata per norm.
- Per-norm `/{id}/analisis` returns `materias` (subjects), `notas`, and `referencias`.
- `referencias` splits into `anteriores` (this norm acts on earlier norms) and `posteriores` (later
  norms act on this norm). Each item has `id_norma`, `relacion: {codigo, texto}`, and a free-text
  `texto` detail.

## Schema (SQLite)

`norms` (one row per norm: identity, rank, scope, department, dates, raw lifecycle fields, derived
`lifecycle_status` / `is_live` / `is_repealed`, URLs, raw JSON), `relations` (directed edges with
`relation_type` + raw label/detail + `api_direction` + `current_norm_id`, with a UNIQUE identity for
dedupe), `subjects` / `norm_subjects`, `briefing_results` (cached payloads), and
`raw_relation_labels` (data-quality counts). Indexes on relation endpoints/type and norm
scope/lifecycle. Full detail in [`data-model.md`](data-model.md).

## Relation normalization

Raw Spanish labels → `AMENDS | REPEALS | CITES | OTHER` via a table-driven, accent-insensitive
keyword matcher. **REPEALS is checked before AMENDS** so "DEROGA" is never miscounted as an
amendment. Raw label and detail are always stored; unknowns become `OTHER`. See
[`relation-normalization.md`](relation-normalization.md).

## Live vs repealed

Derived from raw BOE fields with this precedence: `ANNULLED` (`estatus_anulacion=S`) →
`REPEALED` (`estatus_derogacion=S`) → `EXPIRED` (`vigencia_agotada=S`) → else `LIVE`.
`is_live = status == LIVE`; `is_repealed = status ∈ {REPEALED, ANNULLED, EXPIRED}`.

## Direction rules (critical)

For current norm A: `anteriores` items produce `A --TYPE--> B`; `posteriores` items produce
`C --TYPE--> A`. The same logical edge discovered from either side dedupes via the UNIQUE constraint.
Dedicated tests assert non-reversed edges.

## Four query definitions

1. **Unreadable**: `target`, `COUNT(DISTINCT source)` where `relation_type='AMENDS'`, top 5.
2. **Omnibus**: `source`, `COUNT(DISTINCT target)` where `relation_type='AMENDS'`, top 5.
3. **Dead-law**: numerator = live norms with a `CITES` edge to a repealed norm; denominator = live
   norms in scope; percentage + top ghost (repealed) norms by live citers. Citations only.
4. **Ley 30/1992**: all **live** norms with a `CITES` edge to `BOE-A-1992-26318` (full worklist).

Default scope = state-level (ámbito "Estatal"); `all` scope supported. Results cached in
`briefing_results`.

## Tradeoffs / limitations

- Structured references only (no NLP over `texto`).
- Sample mode ingests a connected subset → numbers reflect that subset; full mode is slow but
  cached/resumable.
- "DE CONFORMIDAD"/"AL AMPARO" are treated as citation-style references (documented choice); easy to
  re-map. Unknown labels are conservatively `OTHER` and surfaced in the data-quality report.
- Referenced-but-not-ingested norms appear as `UNKNOWN` nodes in subgraphs.
