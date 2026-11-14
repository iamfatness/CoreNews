# CoreNews Platform Specification

## Vision
A modular, self-hosted intelligence platform that aggregates free public data sources for research, threat intel, entity investigation, and situational awareness. Focus on ethical, legal use of public data with clear attribution and rate-limit awareness.

## High-Level Architecture

### 1. Data Ingestion Layer
- Connector framework for free APIs, bulk downloads, RSS, and lightweight scrapers.
- Queue-based workers with per-source rate limiting, retries, and caching.
- Keyless sources prioritized where possible.

### 2. Storage & Indexing
- Postgres for structured entities, metadata, and relationships.
- OpenSearch (or Elasticsearch) for full-text search and flexible querying.
- Object storage for raw artifacts (HTML, PDFs, images, etc.).

### 3. Entity Resolution & Graph
- Normalize entities (people, domains, IPs, companies, events, emails, usernames).
- Link analysis capabilities inspired by SpiderFoot / Maltego CE.

### 4. Core Modules
- Unified search across collected data.
- Maps and timelines (Leaflet + free geo feeds).
- Alerts and scheduled digests.
- Case management (pivots, notes, evidence).

### 5. API & UI
- REST / GraphQL API.
- Web UI for search, visualization, and administration.
- Secure vault for user-supplied free-tier API keys.

### 6. Automation
- Integration points for Grok Bots (source health, registration maintenance, ongoing monitoring).

## Non-Functional Requirements
- Respect rate limits and ToS.
- Source attribution and data freshness indicators.
- Modular connectors that can be enabled/disabled independently.
- Easy self-hosting (Docker Compose as the primary deployment method).

## Suggested Initial Tech Stack
- Backend: Python (FastAPI or similar) or Go
- Database: PostgreSQL
- Search: OpenSearch
- Queue: Redis / RQ or Celery
- Frontend: React or lightweight HTMX/Tailwind
- Deployment: Docker Compose

## MVP Scope
1. Core infrastructure (DB, queue, basic API).
2. 4–6 high-value free connectors (GDELT, crt.sh, OpenSanctions bulk, Shodan free tier, VirusTotal free, urlscan).
3. Basic unified search and entity view.
4. Simple web UI.

## Future Considerations
- Graph database option for heavy link analysis.
- Proxy / user-agent rotation for scrapers.
- Multi-tenant support if needed.
- Export formats and integration with existing tools (Maltego, etc.).
