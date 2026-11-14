# CoreNews

Modular, self-hosted OSINT / intelligence platform focused on free public data sources.

## Vision
Aggregate free and free-tier public sources for entity research, threat intelligence, domain/IP recon, geopolitical monitoring, and situational awareness. Ethical use only. Respect rate limits and terms of service.

## Status
**v0.1.0 skeleton** — FastAPI backend with modular connectors. First keyless connector (crt.sh) is live. Free-tier API keys collected by OpenIntel bot.

## Quick Links
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
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Example search: http://localhost:8000/search/crtsh?q=example.com

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
- Simple web UI
