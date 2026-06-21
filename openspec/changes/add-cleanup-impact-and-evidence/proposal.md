## Why

The MVP delivers four executive briefings, but for a Council-of-Ministers audience the
platform still reads like a data dashboard rather than a decision tool. Three gaps stand
out:

1. Briefing 4 prints `02/04/2021` as the "Repeal date" of Ley 30/1992 with no context.
   That raw BOE field is easy to misread: the challenge frames the 2015 repeal/replacement
   by Leyes 39/2015 and 40/2015. We must distinguish the raw lifecycle field, the graph
   repeal evidence, and the challenge replacement context — without overwriting data.
2. The dead-law-dependency rate (17.72%) is a diagnosis with no "so what". Executives want
   to know how much a concrete cleanup (removing direct Ley 30/1992 references) would move
   the number, and a prioritized, actionable worklist with suggested replacements.
3. Every headline number should be traceable back to the underlying BOE relations
   (auditability), and the whole story should be presentable as a guided narrative.

## What Changes

- Add a deterministic, auditable `get_ley30_repeal_context` helper that separates the raw
  BOE repeal-date field, graph-derived `REPEALS` evidence, and the documented 2015
  replacement context (Ley 39/2015 + Ley 40/2015).
- Add a cleanup-impact simulator endpoint that recomputes the dead-law rate after removing
  only direct `CITES` edges to Ley 30/1992 (never a naive `before - 182`).
- Enhance the Briefing 4 worklist with a deterministic, clearly-labelled heuristic
  replacement classifier (Ley 39/2015 vs Ley 40/2015 vs legal review) and an explainable
  priority heuristic, plus CSV export of all fields including raw evidence.
- Add an evidence endpoint (`/api/briefings/{key}/evidence`) returning the raw BOE relation
  edges behind each briefing number, with pagination.
- Add a frontend Evidence drawer, a Council Briefing (story) mode, omnibus subject/department
  diversity explanation and an optional secondary omnibus score, and graph polish
  (metric-based node sizing, legend, hover highlight, click-to-evidence).
- Update API docs, the design doc, README demo script, and OpenSpec specs.

## Capabilities

### Modified Capabilities
- `briefings`: Ley 30/1992 repeal context, cleanup-impact simulator, enhanced worklist with
  heuristic replacement + priority classification, omnibus diversity explanation/score.
- `api`: New cleanup-impact and evidence endpoints; new worklist fields.
- `frontend`: Evidence drawer, Council Briefing mode, careful repeal-context display, cleanup
  impact card, worklist filters/columns/CSV, graph polish.

## Impact

- Backend: new `app/services/ley30.py` and `app/services/evidence.py`; new routes; small
  additions to `omnibus` computation. Existing briefing shapes remain backward-compatible.
- Frontend: new `EvidenceDrawer`, `CouncilBriefing` components; updates to Briefing 4 and the
  omnibus page; graph component sizing/legend tweaks.
- Docs: `docs/api.md`, `docs/design-doc.md`, README demo section.
- No schema changes, no new heavy dependencies, no Neo4j, no LLM. All classification is
  deterministic and surfaced as a heuristic for legal review.
