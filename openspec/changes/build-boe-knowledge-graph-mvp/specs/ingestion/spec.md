## ADDED Requirements

### Requirement: BOE API client
The system SHALL provide an HTTP client for the BOE consolidated-legislation open-data
API that supports both list and per-norm endpoints, sends appropriate `Accept` headers,
applies retry with exponential backoff on transient failures, and enforces a polite
delay between requests. The client SHALL require no API key.

#### Scenario: List consolidated norms
- **WHEN** the client requests the list endpoint with `limit` and `offset`
- **THEN** it returns the parsed list of norm identifiers and summary metadata

#### Scenario: Transient failure retry
- **WHEN** a request fails with a transient error (timeout or 5xx)
- **THEN** the client retries with exponential backoff up to a configured maximum before raising

#### Scenario: Polite rate limiting
- **WHEN** multiple requests are issued in sequence
- **THEN** the client waits a configured minimum delay between requests

### Requirement: Response caching and resume
The system SHALL cache every raw API response to disk under `data/cache/boe/` keyed by
endpoint and norm id, and SHALL reuse the cache instead of re-fetching when present, so
that ingestion can be stopped and resumed without re-hitting the API.

#### Scenario: Cache hit avoids network
- **WHEN** a raw response for a norm endpoint is already cached on disk
- **THEN** the client returns the cached payload without making a network call

#### Scenario: Resume after interruption
- **WHEN** ingestion is restarted after being interrupted
- **THEN** already-cached and already-persisted norms are skipped and ingestion continues

### Requirement: Sample and full ingestion modes
The system SHALL provide a sample ingestion mode that ingests a small, fast set of norms
(including `BOE-A-1992-26318`, `BOE-A-2015-10565`, `BOE-A-2015-10566`, plus recent norms
from the list endpoint) and a full ingestion mode that fetches the entire list with
`limit=-1` and the metadata/analysis for each norm.

#### Scenario: Sample ingestion completes quickly
- **WHEN** sample ingestion is run
- **THEN** a bounded number of norms and their relations are written to SQLite end-to-end

#### Scenario: Sample fallback to fixtures
- **WHEN** the BOE API is unreachable during sample ingestion
- **THEN** the system falls back to bundled fixtures so a demo dataset is still produced

### Requirement: Data-quality report
Ingestion SHALL produce a data-quality report that includes counts of raw relation labels
grouped by raw label and by normalized type, persisted to the database and written to disk.

#### Scenario: Report generated after ingestion
- **WHEN** ingestion finishes
- **THEN** a report listing each raw relation label, its normalized type, and its count is available
