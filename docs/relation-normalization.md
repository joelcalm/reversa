# Relation Normalization

Raw BOE relation labels (Spanish, sometimes accented and phrased actively or passively) are mapped
to four normalized edge types. Implementation: `backend/app/services/relation_normalizer.py`.

## Principles

1. **Keep the raw label and raw detail** on every edge (`relation_label_raw`,
   `relation_detail_raw`) — nothing is lost.
2. **REPEALS is evaluated before AMENDS** so an explicit derogation (e.g. "DEROGA",
   "QUEDA DEROGADA") is never miscounted as an amendment.
3. **Unknown labels → `OTHER`** (conservative). They are never silently dropped.
4. **Accent- and case-insensitive** matching (`AÑADE` == `ANADE` == `añade`).
5. **Table-driven**: add a keyword to the appropriate tuple to extend the mapping.

## Classification order

`REPEALS → AMENDS → CITES → OTHER`. The first matching keyword wins.

## Keyword sets

| Type | Keywords (matched as substrings of the accent-stripped, upper-cased label) |
| --- | --- |
| **REPEALS** | `DEROGA`, `DEROGAD` (derogado/-a/-as), `DEROGACION`, `QUEDA DEROGAD`, `DECLARA LA DEROGACION`, `DEJA SIN EFECTO` |
| **AMENDS** | `MODIFICA`, `ANADE` (añade), `SUPRIME`, `REDACTA`, `NUEVA REDACCION`, `SUSTITUYE` |
| **CITES** | `CITA`, `REFERENCIA`, `MENCIONA`, `DE CONFORMIDAD`, `AL AMPARO`, `EN RELACION` |
| **OTHER** | everything else |

These cover the challenge's required labels (and their passive `SE …` forms, which contain the same
root) plus the high-frequency labels actually observed in the corpus.

## Documented judgement calls

- **`SE DICTA DE CONFORMIDAD` / `AL AMPARO` → CITES.** These are derivative legal-basis references
  (a later norm enacted "in accordance with" / "under" an earlier one). Semantically they are
  citations, and they are frequent in the corpus, so we count them as `CITES`. This is a deliberate,
  documented choice; remove `DE CONFORMIDAD`/`AL AMPARO` from `CITE_KEYWORDS` to exclude them.
- **`SE DESARROLLA` → OTHER (not AMENDS).** "Develops/implements" does not edit the norm's text, so
  it is not an amendment.
- **`SE DECLARA …` (e.g. constitutional rulings), `CORRECCIÓN de errores` → OTHER.** Not amend/repeal
  /cite in the graph sense.

## Data-quality report

After each ingestion, `raw_relation_labels` is rebuilt and a report written to
`data/processed/data_quality_report.json` containing:

- `relation_counts_by_type` — totals per normalized type.
- `labels` — every raw label with its normalized type and count, sorted by frequency.

This makes it easy to spot a frequent label currently landing in `OTHER` and promote it by adding a
keyword. Re-run `make compute` after changing the mapping (or re-ingest to re-derive edge types).
