## MODIFIED Requirements

### Requirement: Briefing Room as primary experience
The frontend SHALL provide a Briefing Room as the default route that integrates an executive
overview and all four briefings on one navigable journey, with hybrid navigation (scroll
anchors and per-briefing focus mode).

#### Scenario: Default landing
- **WHEN** a user opens the application root
- **THEN** they see the Briefing Room overview and can navigate to each briefing without switching to disconnected pages

### Requirement: Unified briefing layout
Each briefing SHALL present on one screen: an executive answer, an interactive graph centred on
the selected item, a recommendation panel, and a ranking or worklist table, with evidence
accessible via a drawer.

#### Scenario: Integrated briefing view
- **WHEN** a user views a briefing section
- **THEN** the graph, recommendation panel, and table are visible together and selection syncs across them

### Requirement: Secondary Explorer and Data Quality
The frontend SHALL expose Explorer and Data Quality as secondary top-level destinations, not as
part of the main four-briefing journey.

#### Scenario: Minimal top navigation
- **WHEN** a user views the top navigation
- **THEN** they see Briefing Room, Explorer, and Data Quality as the primary destinations

## ADDED Requirements

### Requirement: Interactive briefing graph controls
Briefing graphs SHALL support zoom, fit, layout reset, in-graph search, client-side filters,
and a visible legend with lifecycle and relation-type encodings.

#### Scenario: Graph controls
- **WHEN** a user interacts with a briefing graph
- **THEN** they can zoom, search nodes, filter by status/type, and reset the layout
