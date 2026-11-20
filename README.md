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

### Research cases and company filings

The Research screen also supports SEC EDGAR by ticker or CIK, saving records to
cases, copying citations, and verifying saved metadata. For a controlled review
environment, configure these server settings before starting the app:

| Setting | Value |
| --- | --- |
| `EDGAR_USER_AGENT` | Your application or organization name and contact email. Follow the SEC's [EDGAR access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data). |
| `RESEARCH_WORKSPACE_TOKEN_HASHES` | JSON object mapping workspace names to unique, lowercase SHA-256 digests. Generate an independent random key for each workspace and give the raw key only to the appropriate tester. |
| `RESEARCH_SIGNING_KEY` | An independent random server secret of at least 32 bytes. |
| `RESEARCH_SNAPSHOT_SOURCES` | Optional JSON array of source labels whose normalized metadata may be kept as a verifiable snapshot. Use the labels `crt.sh` and `SEC EDGAR`. The default enables no snapshot hashes. |

Generate a workspace key using `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Compute its SHA-256 digest locally before putting the digest in the configuration.
Use a separate random value for the signing key. Keep these values outside Git.

Initialize tables once using `docker compose exec backend python -m app.evidence_store`,
or run `python -m app.evidence_store` from `backend/` with `DATABASE_URL` set.
For local testing, a file-backed SQLite URL works too (for example,
`sqlite:///./research-local.sqlite`). Use PostgreSQL for the Compose deployment.
Open `/research/`, enter a workspace key, create a case, and search a source.
Repeat searches made before opening a workspace to make those results eligible
for saving. Saved evidence can be reopened and cited without source access.

The workspace key is scoped to one workspace and held in browser memory until
reload or close. Use HTTPS for hosted review, with a single backend process
for the initial EDGAR request limit. Production sign-in and a shared quota
manager are separate follow-on work. Verification checks the saved normalized
metadata against its SHA-256 digest. The source link provides access to the
original publication.

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
