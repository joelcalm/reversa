# Design — Cleanup impact, worklist intelligence, and evidence

## Ley 30/1992 repeal context (Part 1)

The DB row for `BOE-A-1992-26318` has `estatus_derogacion = "S"`, `lifecycle_status =
REPEALED`, and `repeal_date = "20210402"` (raw BOE `fecha_derogacion`). The graph also
contains `REPEALS` edges into it, including from `BOE-A-2015-10565` (Ley 39/2015) with raw
label `SE DEROGA` / detail `... por Ley 39/2015, de 1 de octubre`. Ley 40/2015
(`BOE-A-2015-10566`) is present and LIVE but is not itself a `REPEALS` source for this norm.

`get_ley30_repeal_context(conn)` returns three clearly separated layers, none of which
overwrite the raw data:

- `boe_raw_repeal_date`: the raw `repeal_date` field, formatted ISO (`2021-04-02`). This is
  the BOE `fecha_derogacion` and reflects when the deferred-effect provisions of Ley 39/2015
  fully entered into force; we present it as a raw field, not a legal conclusion.
- `effective_repeal_date`: `null` — we deliberately do not infer a precise effective date
  from free-text relation details. The raw field is shown separately.
- `repealing_norms`: distinct `REPEALS` sources from the graph (the formal full-repealer
  Ley 39/2015 first), each with raw label/detail and BOE URL.
- `replacement_norms`: the documented challenge replacement context — Ley 39/2015 (Common
  Administrative Procedure) and Ley 40/2015 (Public Sector Legal Regime). IDs are documented
  constants; titles/URLs come from the DB when present. Used only for explanatory context,
  never for computing the blast radius.
- `display_note`: explains the separation of raw field vs replacement context.

## Cleanup impact simulator (Part 2)

A single set-difference over the live citers, computed from SQLite, never a naive subtraction:

- `live_scope` = live norms in scope (denominator).
- `before` = distinct live norms in scope with a `CITES` edge to any repealed/annulled/expired
  target.
- `after` = same, excluding the target `BOE-A-1992-26318`.
- `fully_cleaned = before - after` (live norms whose only dead-law citation was Ley 30/1992).
- `direct_live_citers` = distinct live norms citing Ley 30/1992 (may exceed `fully_cleaned`,
  because some also cite other dead norms and stay dirty).

## Worklist intelligence (Part 3)

`classify_ley30_replacement(text)` is a pure, accent/case-insensitive keyword matcher with
two keyword sets (procedure → Ley 39/2015; sector/regime → Ley 40/2015). Confidence:
`high` (≥2 hits one side, 0 the other), `medium` (exactly 1 hit one side, 0 the other),
`low` (both match or neither). It returns matched keywords for audit and is always labelled
"suggested replacement for legal review", never a legal conclusion.

`classify_priority(...)` is a small explainable rule: `high` if fully-cleanable or a
high-impact rank; `medium` if multiple dead-law citations or a major department; else `low`.
Each row carries `priority_reason` and `dead_law_citations_count`.

## Evidence endpoint (Part 4)

`GET /api/briefings/{key}/evidence?norm_id=&scope=&limit=&offset=` returns the raw relation
edges behind a briefing item: incoming `AMENDS` (unreadable), outgoing `AMENDS` (omnibus),
incoming `CITES` from live in-scope norms (dead-law, blast-radius). Each item carries full
`source_norm`/`target_norm` metadata and the raw relation fields, with `total/limit/offset`.

## Frontend (Parts 1, 2, 3, 4, 5, 7)

- Briefing 4 shows a careful repeal-context block (status, 2015 replacement context, raw BOE
  field with a "Why this date?" note) plus a compact cleanup-impact card.
- A reusable `EvidenceDrawer` (side drawer) is opened from table rows and graph node clicks.
- A Council Briefing mode walks 6 steps (corpus → diagnosis → root cause → rot → scalpel →
  worklist) reusing existing API calls, with one big number + plain-English interpretation +
  one evidence component per step.
- Graph nodes are sized by the relevant metric; legend and hover highlight remain; node click
  opens the evidence drawer.

## Omnibus diversity (Part 6)

Keep ranking by `target_count`. Add `department_diversity` (distinct departments across
amended targets) and a secondary `omnibus_score = target_count * log(1 + subject_diversity)`,
both clearly labelled as secondary indicators.

## Constraints honoured

SQLite + FastAPI remain the source of truth; no Neo4j, no LLM. Every number is computed from
SQLite and traceable to raw BOE relations. Raw labels/details are always preserved.
