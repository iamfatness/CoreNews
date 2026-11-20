# CoreNews

Modular, self-hosted OSINT / intelligence platform focused on free public data sources.

## Vision
Aggregate free and free-tier public sources for entity research, threat intelligence, domain/IP recon, geopolitical monitoring, and situational awareness. Ethical use only. Respect rate limits and terms of service.

## Status
**v0.1.0 skeleton** — FastAPI backend with modular connectors. First keyless connector (crt.sh) is live. Free-tier API keys collected by OpenIntel bot.

## Quick Links
- [Documentation index](docs/README.md)
- [System specification](docs/spec/SYSTEM_SPEC.md)
- [Build roadmap](docs/roadmap/ROADMAP.md)
- [Platform Specification](docs/SPEC.md)
- [Free Sources Inventory](docs/SOURCES.md)

## Getting Started

### Prerequisites
- Docker & Docker Compose

### Run
```bash
# Copy and fill API keys if desired (keyless sources work without them)
cp backend/.env.example .env
# Or use the .env prepared by the OpenIntel bot on the shared computer

docker compose up --build
```

API will be available at http://localhost:8000
- Research workspace: http://localhost:8000/research/
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Example search: http://localhost:8000/search/crtsh?q=example.com

### Search public certificate records

Open the Research workspace, enter a domain such as `example.org`, and select a
record to inspect its issuer, timestamps, and original crt.sh page. CoreNews
shows up to 50 distinct certificate records per search. The result count
distinguishes the records displayed from the number of rows reported by crt.sh.
A certificate log alone cannot establish who operates a domain or whether the
certificate is in use.

The workspace uses `GET /search/records?q=example.org` for normalized records.
The existing `/search/crtsh` endpoint returns source records in their original
format. The backend needs outbound access to crt.sh for either endpoint.

## Architecture Overview
- Ingestion layer with modular connectors (`backend/app/connectors/`)
- Storage: Postgres (OpenSearch planned)
- Queue: Redis
- Search, visualization, and alerting (in progress)
- Grok Bot integration for ongoing automation and source maintenance

## Next Steps
- Additional connectors (GDELT, Shodan, VirusTotal, etc.)
- Database models and persistence
- Entity resolution
- Extend the Research workspace to additional public sources
