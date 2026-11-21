# CoreNews

Modular, self-hosted OSINT / intelligence platform focused on free public data sources.

## Vision
Aggregate free and free-tier public sources for entity research, threat intelligence, domain/IP recon, geopolitical monitoring, and situational awareness. Ethical use only. Respect rate limits and terms of service.

## Status
**Integrated review build** with public-source search, case evidence and
reports, in-app monitoring, earthquake mapping, and OFAC organization lookup.
See [review deployment and verification](docs/review-deployment.md).

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
| `GDELT_ENABLED` | Set to `true` after verifying upstream access and metadata policy on the deployment host. The default is disabled. |
| `CISA_KEV_ENABLED` | Set to `true` after verifying access to CISA's public catalog mirror from the deployment host. The default is disabled. |
| `GLEIF_ENABLED` | Set to `true` after verifying access to the public LEI registry from the deployment host. The default is disabled. |
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

### Search across sources

Open a case workspace and choose **Search across sources**. Enter a domain
or URL, organization name or identifier, CVE identifier, earthquake or place,
or news topic. CoreNews routes the query to compatible sources. Use
**Search as** to change the detected category.

| Query | Sources CoreNews checks |
| --- | --- |
| Website or domain | crt.sh and GDELT. A website URL is reduced to its hostname. |
| Organization name | GLEIF, the latest imported OFAC SDN snapshot, and GDELT. |
| SEC ticker or CIK | SEC EDGAR and GDELT. If filings resolve a company name, CoreNews checks GLEIF and OFAC using that name. |
| LEI | GLEIF. If the LEI resolves a legal name, CoreNews checks OFAC and GDELT using that name. |
| CVE identifier | CISA KEV and GDELT. |
| Earthquake query | USGS earthquake events from the past seven days and GDELT coverage. |
| News topic | GDELT. |

**Source coverage** shows which sources responded, the query each received, and
which sources need setup or were unavailable. The workbench displays up to
12 records per source and interleaves results to keep each available source in view.
Filter by source or source date and sort by newest source date. **What stands
out** links to records used to identify the latest filing, multiple LEIs for
one name, screening candidates, or repeated headlines across domains.
Open the underlying evidence before drawing a conclusion. Repeated headlines
may share a publisher or wire report.

The GLEIF lookup accepts a direct LEI or exact-name matches from the first
12 registry results. Save a record to cite its LEI, jurisdiction, source and
last update. **View entity timeline** groups saved registry records by exact
LEI. See the [GLEIF API documentation](https://www.gleif.org/en/lei-data/gleif-api/).

Integrations can call `POST /api/research/workbench` with a workspace
credential and a JSON body containing `query` and optional `intent`. The response
includes source outcomes, original-record references, evidence save proofs,
and insights that reference record IDs.

### Compare custom source queries and browse evidence

Open a workspace and expand **Source catalog** to see configured sources and
their supported inputs. Choose **Compare sources** and enter a domain, a
company ticker or CIK, legal name or LEI, CVE, or a news topic in their respective fields. Failed
sources are identified individually. Use **Filter by source** above the
results to narrow the completed search. GDELT records contain the indexed
headline, the publisher link, and the indexing time where supplied. Follow
the publisher link for the article itself.

**Browse workspace evidence** loads the most recent 500 saved records before
filtering. **View entity timeline** groups that same window by exact domain
or SEC CIK. Each item shows the case it came from and which recorded date is
being displayed. A shared domain provides a navigation link between records
and does not establish common ownership.

The test suite uses SQLite by default. To exercise it against a dedicated test
PostgreSQL server, set `CORENEWS_TEST_DATABASE_URL` and run
`python -m unittest discover -s tests -v` from `backend/`. The evidence tests
create and remove a unique schema per test.

### CISA remediation advisories

After enabling the source, open a workspace and select **Remediation
advisories**. Enter one CVE identifier. A matching record provides CISA's
remediation action when supplied, the catalog version and addition date,
and the deadline for covered federal agencies when supplied. Check the
vendor's advisory for product and version applicability. A saved record
carries its CVE and original source citation into the case report.

The lookup reads only [CISA's public KEV mirror](https://github.com/cisagov/kev-data).
CoreNews caches the successful catalog fetch for five minutes. An empty result
means the CVE is absent from the catalog version retrieved.

### Findings and case reports

If the research tables are already initialized, rerun
`docker compose exec backend python -m app.evidence_store` to add the findings
table. This initialization leaves existing cases and saved evidence in place.
Choose a case and open **Findings and report**. Add a finding or open question
and select evidence saved in that case. An uncited finding remains clearly
marked in the report. If a finding changed since it was opened for editing,
refresh the report and reopen the latest version before saving.

**Download JSON** exports the case, findings, and cited evidence. **Download
evidence CSV** exports source references, timestamps, and integrity status
for records saved to the case. Formula-like titles are prefixed with
`[text]` in CSV for spreadsheet review. **Print or save PDF** opens the browser
print dialog with the report. All three formats work from saved case data,
including when an upstream source is unavailable. A verified metadata hash
checks the saved bytes. OFAC citations also include the source snapshot hash
and list entry ID.

### Case activity

Rerun the evidence store initializer before using **Case activity**. It shows
case creation, first evidence saves, and report entry revisions from the time
the activity table is installed. Entries include the action, timestamp, and
revision where applicable. The workspace key scopes the history to the
selected case. Person-level attribution requires individual sign-in.

### Watches and alerts

After validating source access on the deployment host, set
`RESEARCH_WATCHES_ENABLED=true`, rerun the evidence store initializer to add
the watch tables, and start the optional worker with
`docker compose --profile monitoring up -d watch-worker`. Enable SEC EDGAR
or GDELT separately using the settings above. Use one worker initially and
keep the source settings consistent between the backend and worker.

Select a case, open **Watches and alerts**, and add a watch by SEC CIK or
public news topic. The first successful check records a baseline. Subsequent
checks produce an alert for each previously unseen record in the source's
result window. Open the linked source, save the record to the case, or mark
the alert reviewed. Failed checks retry and appear in the watch status.
Expired leases let the worker recover checks interrupted by a restart.

### Earthquake map

Open a case workspace and choose **Earthquake map** for public USGS events.
Filter by day or week, region, and minimum magnitude. Select an event on the
map or in the adjacent list to open its source page or save it to a case.
**Download GeoJSON** exports the displayed events with longitude first,
source links, and timestamps.

The global overview uses generalized land polygons from
[Natural Earth](https://www.naturalearthdata.com/downloads/110m-physical-vectors/110m-land/).
Epicenters and magnitudes are USGS estimates that can change. A saved event
preserves the values seen when it was collected. If snapshot retention is
approved on your deployment, add `USGS Earthquakes` to
`RESEARCH_SNAPSHOT_SOURCES` to capture and verify its metadata hash.

### OFAC organization screening

Download the standard SDN.XML export from the
[OFAC Sanctions List Service](https://ofac.treasury.gov/sanctions-list-service).
From `backend/` with the deployment's `DATABASE_URL` configured, initialize
the tables and import the downloaded file.

```sh
python -m app.evidence_store
python -m app.ofac_catalog /path/to/SDN.XML
```

Preserve the original file with the displayed SHA-256 for audit. Reimporting
identical bytes reuses that snapshot. Import new versions on your review schedule.
Open **Organization screening** in the research workspace. It defaults to
the most recent imported publication date and accepts a specific historical
snapshot hash. The lookup covers normalized exact matches on organizations'
primary names. Use the source entry to verify identity and consult the
applicable lists when reviewing a candidate. A result or an empty lookup
cannot establish sanctions status. A saved case record cites its snapshot
date, hash, and OFAC list entry.

In **View saved evidence**, open the candidate and choose **Review
organization identity**. Record the decision and supporting references.
The case report includes the decision, rationale, and source snapshot.
Case activity records each revision at workspace level. Rerun the schema
initializer to add the review table to an existing installation.

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
