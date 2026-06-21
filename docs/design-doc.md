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

## Bonus: cleanup impact simulator

`GET /api/briefings/ley-30-1992-cleanup-impact` answers the executive "so what": if we remove
all direct `CITES` references to Ley 30/1992, how far does the dead-law rate fall? It is a
**set difference over the graph**, never a naive subtraction: `before` = live in-scope norms
citing any dead norm; `after` = the same excluding the Ley 30/1992 target; `fully_cleaned =
before − after`. Norms that also cite other dead norms stay counted in `after`, so the 182
direct citers do not all become "clean" (96 of them do, in the full corpus).

## Evidence and auditability

Every headline number is traceable to raw BOE relations via
`GET /api/briefings/{key}/evidence`. It returns the underlying directed edges (source/target
norm metadata + raw label/detail/`api_direction`/`current_norm_id`), one row per logical edge so
the `total` equals the briefing headline. A frontend **evidence drawer** opens from every table
row and graph node click, with copyable BOE IDs and BOE links. The Ley 30/1992 worklist also
carries a **deterministic keyword heuristic** suggesting Ley 39/2015 vs Ley 40/2015 (or "needs
legal review"), with matched keywords and an explainable priority — clearly labelled as a
heuristic for legal review, not a legal conclusion (no LLM, fully auditable).

## Ley 30/1992 repeal context

The app distinguishes three layers and never overwrites raw data:

- **Raw BOE lifecycle fields**: `estatus_derogacion = "S"`, `lifecycle_status = REPEALED`, and
  the raw `repeal_date = 20210402` (BOE `fecha_derogacion`). This date is shown as a raw field
  with a "Why this date?" note: it reflects when the deferred provisions of the 2015 reform
  fully took effect, *used as repeal/replacement context for this challenge* — not a claim of
  legal certainty. `effective_repeal_date` is left `null` (not inferred from free-text).
- **Graph evidence**: `REPEALS` edges into the norm, e.g. `SE DEROGA … por Ley 39/2015`, which
  surfaces Ley 39/2015 as the formal full repealer.
- **Challenge replacement context**: Ley 39/2015 (Common Administrative Procedure) + Ley 40/2015
  (Public Sector Legal Regime), used for explanation only. The blast radius is always computed
  from `CITES` edges to `BOE-A-1992-26318`, never via the replacement norms.

## Information architecture

The primary product surface is the **Briefing Room** (`/`): an executive overview plus four anchored briefing sections on one scrollable page. Each section combines an executive answer, an interactive neighbourhood graph (centred on the selected ranked item), a recommendation panel, and a sortable worklist. **Focus mode** (`/briefing/:slug`) shows a single briefing full-width. Secondary tools are **Explorer** (`/explorer`) and **Data Quality** (`/data-quality`). Legacy routes (`/council`, `/briefings/*`) redirect to the new IA.

## Council Briefing tour

The **Start Council Briefing** button on the overview smooth-scrolls through overview → Briefings 1–4 (replacing the old slideshow). Numbers always come from live APIs at runtime.

## Tradeoffs / limitations

- Structured references only (no NLP over `texto`).
- Sample mode ingests a connected subset → numbers reflect that subset; full mode is slow but
  cached/resumable.
- "DE CONFORMIDAD"/"AL AMPARO" are treated as citation-style references (documented choice); easy to
  re-map. Unknown labels are conservatively `OTHER` and surfaced in the data-quality report.
- Referenced-but-not-ingested norms appear as `UNKNOWN` nodes in subgraphs.
