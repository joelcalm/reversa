## 1. Ley 30/1992 repeal-context audit (Part 1)

- [x] 1.1 Audit the SQLite row + `REPEALS` relations for `BOE-A-1992-26318`
- [x] 1.2 Implement `get_ley30_repeal_context(conn)` in `app/services/ley30.py`
- [x] 1.3 Unit-test the helper (raw date present, effective date null, repealing/replacement norms)
- [x] 1.4 Frontend: careful repeal-context display in Briefing 4 with "Why this date?" note
- [x] 1.5 Docs: explain raw field vs graph evidence vs replacement context

## 2. Cleanup impact simulator (Part 2)

- [x] 2.1 Implement `compute_ley30_cleanup_impact(conn, scope)` (before/after/fully-cleaned, no naive subtraction)
- [x] 2.2 Add `GET /api/briefings/ley-30-1992-cleanup-impact` route
- [x] 2.3 Tests with a fixture: only-Ley30 citer, Ley30+other-dead citer, other-dead-only citer
- [x] 2.4 Frontend: cleanup-impact card in Briefing 4

## 3. Intelligent cleanup worklist (Part 3)

- [x] 3.1 Implement `classify_ley30_replacement(text)` deterministic heuristic + confidence
- [x] 3.2 Implement `classify_priority(...)` explainable heuristic with reason
- [x] 3.3 Enhance the blast-radius worklist with new per-norm fields
- [x] 3.4 Unit-test classifier (procedure/sector/mixed/empty) and priority heuristic
- [x] 3.5 Frontend: worklist columns, filters, CSV export of all fields

## 4. Evidence drawer (Part 4)

- [x] 4.1 Implement `get_evidence(conn, key, norm_id, scope, limit, offset)` for all four modes
- [x] 4.2 Add `GET /api/briefings/{briefing_key}/evidence` route
- [x] 4.3 Backend tests for each evidence mode + pagination
- [x] 4.4 Frontend: `EvidenceDrawer` component + "View evidence" buttons on all briefings

## 5. Council Briefing / story mode (Part 5)

- [x] 5.1 Add a Dashboard/Council Briefing toggle and routing
- [x] 5.2 Implement the 6-step guided narrative reusing existing API calls

## 6. Omnibus subject-diversity explanation + optional score (Part 6)

- [x] 6.1 Add `department_diversity` and secondary `omnibus_score`; keep ranking by `target_count`
- [x] 6.2 Frontend: subject-diversity tooltip, department diversity, secondary score label
- [x] 6.3 Tests: subject diversity correct, ranking still by distinct amended count

## 7. Graph polish (Part 7)

- [x] 7.1 Size nodes by the relevant metric per briefing; keep legend + hover highlight
- [x] 7.2 Click-to-open evidence drawer from briefing graphs

## 8. Docs (Part 8)

- [x] 8.1 Update `docs/api.md` (cleanup-impact endpoint, evidence endpoint, worklist fields)
- [x] 8.2 Update `docs/design-doc.md` (cleanup simulator, evidence/auditability, repeal context)
- [x] 8.3 Update README demo script; update OpenSpec specs

## 9. Testing and validation (Part 9)

- [x] 9.1 Run backend tests (existing + new) green
- [x] 9.2 Frontend build + TypeScript checks green
- [x] 9.3 Verify existing four briefings + shapes unchanged; new endpoints work for state/all
