## ADDED Requirements

### Requirement: Dashboard
The frontend SHALL provide a landing dashboard titled "BOE Knowledge Graph" that displays
summary KPI cards, four briefing entry cards, a clearly stated default scope note, and
data freshness/ingestion stats.

#### Scenario: Dashboard renders summary
- **WHEN** the dashboard loads with summary data available
- **THEN** it shows KPI cards, the four briefing cards, and the default scope note

### Requirement: Briefing pages
The frontend SHALL provide a dedicated page for each of the four briefings, each with a
plain-language explanation, the relevant table/KPIs, and a graph view sourced from the
backend graph endpoints.

#### Scenario: Briefing page with table and graph
- **WHEN** a user opens a briefing page
- **THEN** the page shows the explanation, the result table or KPI, and the subgraph

#### Scenario: Blast radius worklist and CSV
- **WHEN** a user opens the Ley 30/1992 briefing page
- **THEN** the full worklist table is shown with per-norm BOE links and a CSV download

### Requirement: Graph explorer
The frontend SHALL provide a general graph explorer where users can search a norm by text
or BOE id, open its neighborhood, filter by relation type, and click a node to view a side
panel of details.

#### Scenario: Explore a neighborhood
- **WHEN** a user searches a norm and opens its neighborhood
- **THEN** the subgraph renders and clicking a node shows its details panel

### Requirement: Graph styling and states
Cytoscape graphs SHALL style nodes by lifecycle status (live vs repealed/annulled/expired)
and edges by normalized relation type, using CSS variables and an institutional white/green
theme, and all data views SHALL handle loading, error, and empty states.

#### Scenario: Status-based styling
- **WHEN** a graph contains both live and repealed norms
- **THEN** live and dead norms are visually distinguished and edge types are color-coded

#### Scenario: Loading and error states
- **WHEN** data is loading or a request fails
- **THEN** the UI shows an appropriate loading indicator or error message rather than crashing
