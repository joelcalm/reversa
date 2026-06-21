# 5-Minute Demo Script — Addressed to the Council of Ministers

> Tone: serious, institutional, plain language. Screen-share the web app throughout.

## 0:00 — The problem (40s)
"Spain's body of consolidated legislation has grown for decades. Laws are amended again and again,
repealed and replaced, and cross-referenced thousands of times. The relationships exist in the BOE's
open data — but they are scattered across each norm's analysis block, invisible as a whole. Today no
one can answer, at a glance, simple governance questions: which laws have become unreadable? Who
caused the most disruption? How much of our live law still leans on dead law?"

## 0:40 — What we built (40s)
*(Dashboard)* "We converted the BOE consolidated-legislation corpus into a knowledge graph. Every
norm is a node; every relationship — amendment, repeal, citation — is a directed, typed edge, with
the original BOE wording preserved for audit. On top of that graph we built four executive briefings.
Everything you'll see is computed live from the data, not hand-picked. Our default scope is
state-level norms — the Council's remit."

## 1:20 — Briefing 1: Unreadable laws (40s)
*(Open Briefing 1)* "First: which laws have become unreadable from too many amendments? We rank
norms by how many distinct later norms have amended them. At the top you'll typically find
foundational acts amended dozens of times. The graph shows the incoming amendments converging on each
norm — a visual measure of accumulated complexity. Each row links straight to the official BOE text."

## 2:00 — Briefing 2: Omnibus laws (40s)
*(Open Briefing 2)* "Second: who made the mess? Omnibus norms are single acts that quietly modified
many other norms at once. We rank by the number of distinct norms each act amends. The outgoing
fan-out in the graph makes the 'blast' visible. We also show subject diversity — how many different
policy areas a single act reached into."

## 2:40 — Briefing 3: Dead-law dependencies (50s)
*(Open Briefing 3)* "Third, and most concerning for legal certainty: how much of the live statute
book rests on dead law? We count live norms that still cite an already-repealed norm — citations
only, never amendments or repeals. The headline figure is a percentage with its exact numerator and
denominator, so it's auditable. Below it, the 'ghost' norms: repealed laws still being cited by the
most live norms. The graph shows live norms in green still tethered to red, repealed ghosts."

## 3:30 — Briefing 4: Ley 30/1992 blast radius (50s)
*(Open Briefing 4)* "Fourth, a concrete case. In 2015, Ley 30/1992 was repealed and replaced by
Leyes 39/2015 and 40/2015. The repeal is on the books — but is it finished in practice? Here is the
full worklist of live norms that still cite Ley 30/1992 directly. Not a top-five — every one of them,
with department, date and a link to BOE, downloadable as CSV for the teams that must fix them. The
graph centers on Ley 30/1992 with every live citation pointing in."

## 4:20 — Graph explorer (30s)
*(Open Graph explorer)* "For analysts, a general explorer: search any norm by title or BOE ID, open
its neighborhood, filter by relationship type, and click any node for its details and graph metrics.
The full graph is never rendered at once — every view is a focused subgraph built on the server."

## 4:50 — Design choices and next steps (10s)
"Everything is reproducible from the public API, with transparent relation normalization and tests
that guard the graph's direction. Next: full-corpus ingestion at scale, time-sliced views, and
alerts when a new norm cites dead law. Thank you."
