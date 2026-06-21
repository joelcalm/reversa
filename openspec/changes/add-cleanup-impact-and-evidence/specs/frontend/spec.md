## ADDED Requirements

### Requirement: Careful Ley 30/1992 repeal-context display
The frontend SHALL present Ley 30/1992 status, the 2015 replacement context (Ley 39/2015 +
Ley 40/2015), and the raw BOE repeal-date field as distinct pieces of information, with a
short "Why this date?" note, instead of labelling the raw date simply as "Repeal date".

#### Scenario: Repeal context shown carefully
- **WHEN** a user views Briefing 4
- **THEN** they see the REPEALED status, the 2015 replacement context, and the raw BOE repeal-date field with an explanatory note

### Requirement: Cleanup-impact card
The frontend SHALL show a cleanup-impact card in Briefing 4 with the before rate, the
simulated after rate, the fully-cleaned count, and the number of direct references removed,
plus a note that it is a graph simulation removing only direct Ley 30/1992 citations.

#### Scenario: Cleanup-impact visible
- **WHEN** a user views Briefing 4
- **THEN** they see before vs after rates and the fully-cleaned count with an explanation

### Requirement: Evidence drawer
The frontend SHALL provide a side drawer, openable from briefing table rows and graph node
clicks, that shows the raw BOE relation edges behind a number with pagination, raw
labels/details, source/target BOE links, and copyable BOE IDs.

#### Scenario: View evidence
- **WHEN** a user clicks "View evidence" on a briefing row
- **THEN** a side drawer opens listing the underlying BOE relations with raw labels and BOE links

### Requirement: Council Briefing mode
The frontend SHALL offer a Council Briefing (story) mode with a guided sequence of steps
(corpus overview, diagnosis, root cause, dead-law rot, Ley 30/1992 scalpel, worklist), each
with one headline number, a plain-English interpretation, and one evidence component, with
Next/Previous navigation.

#### Scenario: Guided narrative
- **WHEN** a user enters Council Briefing mode
- **THEN** they can step through the executive narrative with Next/Previous controls
