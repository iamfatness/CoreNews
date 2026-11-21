# CoreNews Best-in-Class Benchmark

What ‘best in class’ looks like for a news-centric, public-source OSINT platform. Official product and documentation pages were reviewed on 20 November 2026 (America/New_York). This complements the Competitive Gap Analysis and the CoreNews system spec; it does not repeat the data-coverage gaps. Pricing is quoted only when a vendor published it. Unverified cells are marked.

**Sources recorded on this page**

- Dataminr First Alert product page and 26 August 2026 First Alert Advanced press release; Pulse geovisualization page
- Recorded Future Intelligence Graph, AI, pricing, integrations, STIX/TAXII docs, and mobile support article
- Flashpoint Echosec and Physical Security Intelligence pages; Flashpoint pricing page
- Maltego pricing page (capabilities as of January 2026)
- Babel Street platform page
- Dow Jones Factiva developer docs: news datasets and supported languages
- Meltwater real-time alerting, integrations/API, and official pricing blog (9 July 2026)
- Ground News rating-system page, Premium checkout, and subscription help article (edited 10 November 2026)
- AllSides media-bias landing and rating-methods pages, including CC BY-NC licensing note
- Feedly Threat Intelligence pricing page; clustering and OpenCTI integration docs
- Liveuamap site and official API pricing page
- Bellingcat Online Investigation Toolkit
- OSINT Industries homepage and pricing page
- SpiderFoot GitHub README (MIT, 200+ modules). HX commercial status unverified
- Filigran OpenCTI product page
- GDELT Project homepage and Terms of Use on the About page
- Wikimedia Analytics / Pageviews API documentation
- Schema.org ClaimReview and Google Fact Check structured-data documentation
- CoreNews SYSTEM_SPEC.md and ROADMAP.md on iamfatness/CoreNews (main), and the Competitive Gap Analysis Page

## Contents

- [Executive recommendations](#recs)
- [How to read this](#method)
- [Feature benchmark](#matrix)
- [Published pricing anchors](#pricing)
- [Where CoreNews can win](#win)
- [Trust, quality, and compliance](#trust)
- [UX and product-quality bar](#ux)
- [Go-to-market](#gtm)
- [Roadmap checklist](#checklist)
- [Sources](#sources)

> **Research only.** Another agent is writing application code. This Page does not change the repo. It benchmarks news-intelligence and OSINT leaders, then maps a best-in-class bar onto the existing P0–P3 roadmap, calling out items the spec does not yet include.

| Value | Label | Detail |
| --- | --- | --- |
| 15 | Products reviewed | Official pages, 20 Nov 2026 |
| 13 | Feature rows | 13 have at least one clear Yes |
| 13 | Checklist items not in the roadmap | of 24 best-in-class items |
| 5 | Priority recommendations | See the next section |

<a id="recs"></a>

## Executive recommendations

*The five moves most likely to make CoreNews feel best-in-class without trying to out-collect Dataminr, Babel Street, or Flashpoint.*

1. Put a news-event map and story clusters on the home screen. GEO-1 already maps fires, quakes, aircraft, and ships. It does not map where news is happening. GDELT's official terms allow commercial use without a fee (still cite the project and re-read current terms). Pair that with Feedly-style clustering and Ground News-style outlet comparison.
2. Make every claim inspectable: hashed provenance (already P0), Admiralty codes (already P1), and a new cross-outlet claim tracker. Use Schema.org ClaimReview and licensed fact-check feeds. Cite-or-drop AI (already P2) should be non-negotiable.
3. Add an early-signal layer: GDELT 15-minute volume spikes, Wikimedia pageview spikes on relevant articles, and the sensor watches already planned. That is how a public-source product can feel timely without a social firehose.
4. Build a daily, cited briefing and serious alert-noise controls. Meltwater advertises 2–5 minute delivery and noise reduction as the job-to-be-done. CoreNews already plans digests in P2; it does not plan a briefing product. Pull first-pass noise tuning forward from P3 if possible.
5. Treat trust as the sales pitch. Keep the license gate, ethics policy, audit log, and GDPR/CCPA handling. Add a misinformation workflow, WCAG 2.2 AA, and an earlier SOC 2 control map. Do not reuse AllSides or similar ratings in a paid product without a commercial license (AllSides is CC BY-NC 4.0).

<a id="method"></a>

## How to read this

Cells reflect what official product, pricing, or documentation pages advertised on 20 November 2026 (America/New_York), not a hands-on trial of every platform. Yes means the vendor clearly advertises the capability. Partial means a related or limited version. No means it was not advertised and is not a reasonable inference. N/A is for the Bellingcat toolkit, which is a directory rather than a hosted platform. Unverified means the public pages reviewed were insufficient. Vendor marketing claims (for example Meltwater's “up to 90% fewer irrelevant alerts,” or OSINT Industries' “zero false positives”) are labeled as claims. No list price in this Page was invented; quote-only vendors stay quote-only.

Related documents: the Competitive Gap Analysis (data coverage and product-capability gaps as of 18 November 2026), the OSINT Source Catalog, and the merged spec and roadmap in iamfatness/CoreNews.

- [Competitive Gap Analysis](./COMPETITIVE_GAP_ANALYSIS.md)
- [OSINT Source Catalog](./SOURCE_CATALOG.md)
- [System specification](../spec/SYSTEM_SPEC.md) — github.com
- [Build roadmap](../roadmap/ROADMAP.md) — github.com

<a id="matrix"></a>

## Feature benchmark

*Filter by product group so the table stays readable. Select a feature for per-vendor notes and the CoreNews plan.*

Every product group is included. Each rating table lists the products in that group. Profiles and official-page notes below include every reviewed product and every feature.

### Event and geo

| Feature | Dataminr | Flashpoint | Babel Street | Liveuamap | CoreNews |
| --- | --- | --- | --- | --- | --- |
| Real-time alerting | Yes | Yes | Yes | Partial | Planned · P2 / P3 |
| Story clustering / dedup | Unverified | Unverified | Unverified | Partial | Not in roadmap |
| Source credibility / bias ratings | No | No | No | No | Partial in roadmap |
| Multilingual + translation | Yes | Yes | Yes | Partial | Planned late · P3 |
| Entity extraction and graph | Partial | Partial | Yes | No | Planned · P1 / P2 |
| Map | Yes | Yes | Unverified | Yes | Partial in roadmap |
| AI summaries with citations | Partial | Partial | Yes | No | Planned · P2 |
| Verification / fact-check tools | Partial | Unverified | Partial | Partial | Not in roadmap |
| Collaboration / cases | Partial | Partial | Partial | No | Planned · P2 |
| API | Yes | Partial | Yes | Yes | Planned · P2 |
| Integrations (STIX/TAXII, Slack, SIEM) | Partial | Partial | Partial | Partial | Planned · P2 / P3 |
| Mobile | Yes | Unverified | Unverified | Yes | Not in roadmap |
| Pricing model | Unverified | Unverified | Unverified | Yes | Planned late · P3 |

### News and media

| Feature | Factiva | Meltwater | Ground News | Feedly TI | AllSides | CoreNews |
| --- | --- | --- | --- | --- | --- | --- |
| Real-time alerting | Partial | Yes | Partial | Partial | No | Planned · P2 / P3 |
| Story clustering / dedup | Unverified | Unverified | Yes | Yes | Partial | Not in roadmap |
| Source credibility / bias ratings | No | No | Yes | No | Yes | Partial in roadmap |
| Multilingual + translation | Yes | Partial | Unverified | Unverified | Partial | Planned late · P3 |
| Entity extraction and graph | Partial | No | No | Partial | No | Planned · P1 / P2 |
| Map | No | Unverified | Unverified | No | No | Partial in roadmap |
| AI summaries with citations | Yes | Yes | Unverified | Partial | No | Planned · P2 |
| Verification / fact-check tools | No | No | Partial | No | Partial | Not in roadmap |
| Collaboration / cases | Partial | Partial | No | Partial | No | Planned · P2 |
| API | Yes | Yes | Unverified | Yes | Partial | Planned · P2 |
| Integrations (STIX/TAXII, Slack, SIEM) | Partial | Partial | No | Yes | No | Planned · P2 / P3 |
| Mobile | Unverified | Yes | Yes | Unverified | Unverified | Not in roadmap |
| Pricing model | Unverified | Partial | Yes | Partial | Partial | Planned late · P3 |

### Investigation

| Feature | Maltego | Bellingcat toolkit | OSINT Industries | SpiderFoot | CoreNews |
| --- | --- | --- | --- | --- | --- |
| Real-time alerting | Partial | N/A | No | No | Planned · P2 / P3 |
| Story clustering / dedup | No | N/A | No | No | Not in roadmap |
| Source credibility / bias ratings | No | N/A | No | No | Partial in roadmap |
| Multilingual + translation | Unverified | N/A | Unverified | No | Planned late · P3 |
| Entity extraction and graph | Yes | N/A | Partial | Partial | Planned · P1 / P2 |
| Map | Yes | Partial | Yes | Unverified | Partial in roadmap |
| AI summaries with citations | Partial | N/A | Unverified | No | Planned · P2 |
| Verification / fact-check tools | Partial | Yes | Partial | No | Not in roadmap |
| Collaboration / cases | Yes | N/A | Partial | No | Planned · P2 |
| API | Partial | N/A | Yes | Partial | Planned · P2 |
| Integrations (STIX/TAXII, Slack, SIEM) | Partial | N/A | No | Partial | Planned · P2 / P3 |
| Mobile | Unverified | N/A | Unverified | No | Not in roadmap |
| Pricing model | Yes | Yes | Yes | Yes | Planned late · P3 |

### CTI platforms

| Feature | Recorded Future | Maltego | Feedly TI | OpenCTI | CoreNews |
| --- | --- | --- | --- | --- | --- |
| Real-time alerting | Yes | Partial | Partial | Partial | Planned · P2 / P3 |
| Story clustering / dedup | Unverified | No | Yes | No | Not in roadmap |
| Source credibility / bias ratings | Partial | No | No | Partial | Partial in roadmap |
| Multilingual + translation | Partial | Unverified | Unverified | Unverified | Planned late · P3 |
| Entity extraction and graph | Yes | Yes | Partial | Yes | Planned · P1 / P2 |
| Map | Unverified | Yes | No | Unverified | Partial in roadmap |
| AI summaries with citations | Yes | Partial | Partial | Yes | Planned · P2 |
| Verification / fact-check tools | Partial | Partial | No | Partial | Not in roadmap |
| Collaboration / cases | Partial | Yes | Partial | Yes | Planned · P2 |
| API | Yes | Partial | Yes | Yes | Planned · P2 |
| Integrations (STIX/TAXII, Slack, SIEM) | Yes | Partial | Yes | Yes | Planned · P2 / P3 |
| Mobile | Yes | Unverified | Unverified | Unverified | Not in roadmap |
| Pricing model | Unverified | Yes | Partial | Partial | Planned late · P3 |

### Short profiles

| Product | Groups | Type | Official snapshot | Pricing (published only) |
| --- | --- | --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Event and geo | Real-time event intel | First Alert and Pulse detect events from 1M+ public sources. Official pages state Multi-Modal Fusion AI over text in 150 languages plus image, video, audio, and sensor signals (First Alert also cites 43TB/day). First Alert Advanced adds agentic corroboration, ReGenAI live briefs, and delivery on web, mobile, email, and APIs. Pulse adds geovisualization and an Esri/ArcGIS integration. No public list price. | Quote only. No public list price on pages reviewed. A 26 August 2026 Dataminr press release announced a $318 million U.S. Department of War contract; that is a government award, not a unit price. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | CTI platforms | Threat intelligence platform | The Intelligence Graph indexes 1M+ sources (open web, dark web, technical feeds, telemetry, Insikt research). Official AI pages advertise grounded sessions, referenced reports, a mobile app, APIs, MCP, and TAXII 1.x / 2.1. Packages are Core, Professional, and Elite; list prices are not published. | Quote-based. Official pricing page: package, organization-size tier (usually unique workforce credentials), add-ons, and capacity such as API calls. Default daily API call limit is 5,000 unless an order form says otherwise. Named-user licensing is available for smaller deployments. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Event and geo | Geospatial and underground OSINT | Echosec, in the Physical Security Intelligence package, is a geospatial OSINT tool for places, people, topics, and events. Official pages: search or translate in 100+ languages, geofenced monitoring, alerts (including webhooks and AI summaries), natural-language search, and coverage from mainstream, fringe, and chat sources. Broader Ignite also covers underground collections. Pricing is by request. | Official pricing page is request-based. Physical Security Intelligence is listed as a commercial package that includes Echosec. No list price on pages reviewed. |
| [Maltego](https://www.maltego.com/pricing/) | Investigation, CTI platforms | Investigation workbench | Graph-first investigations, plus Search, Cases, Data Pass, and (on higher plans) Monitor, Evidence, and Hunchly. Browser Graph includes map and histogram views and an AI Assistant. The pricing page states capabilities as of January 2026 and ISO 27001:2022 certification. STIX/TAXII was not advertised on the pages reviewed. | Published: Basic €0/year (Community Graph, 200 monthly Credits; official government or organizational email may qualify for free Basic+ with 1,000 Credits and Maltego One). Entry Standard €3,000/year. Professional Standard €7,500/year, up to 5 users billed per seat. Enterprise is quote-based. |
| [Babel Street](https://www.babelstreet.com/platform) | Event and geo | Multilingual risk intelligence | Agentic Risk Intelligence platform with Insights Investigator and rights-cleared Data Advantage. Official pages: 200+ languages with native linguistic context, identity and relationship mapping, source-backed findings with citations and auditability, Visual Intelligence, OSINT Streams, and an API-first design. No public list price. | Not published on pages reviewed. Enterprise / quote. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | News and media | Licensed news archive | Dow Jones official developer docs: more than 33,000 global sources, 33 content languages, 200+ countries, plus Wall Street Journal, Newswires, Barron's, and MarketWatch. APIs and feeds support analytics, a real-time AI News Feed, Retrieval for RAG and summarization, and Factiva Select for current-awareness portals. Generative use needs an appropriate GenAI license. Usage rights vary by content and product. | Not published on pages reviewed. Licensed enterprise news; generative and statistical uses are licensed separately in developer documentation. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | News and media | Media intelligence | Media monitoring for PR and communications. Official alerting page: notifications typically in 2–5 minutes via Slack, Teams, email, mobile, and SMS; AI anomaly and sentiment-spike detection; a vendor claim of up to 90% fewer irrelevant alerts. API Foundations is included in most packages. An MCP integration cites sources in answers. This is a media-intelligence product, not an investigative OSINT workbench. | No fixed public price list. Meltwater's official pricing blog (9 July 2026) gives indicative USD ranges for typical US configurations: Starter from $10,000/year, Pro from $25,000/year, Enterprise from $130,000/year. Final quotes vary; preferential public-sector pricing is mentioned. |
| [Ground News](https://ground.news/rating-system) | News and media | News comparison and bias | Clusters coverage of the same story across outlets and shows publication-level bias, factuality, and ownership. Bias ratings average AllSides, Ad Fontes Media, and Media Bias Fact Check and are explicitly not article-level. Blindspot highlights stories covered unevenly across the spectrum. Strong consumer news product; not an OSINT workbench or analyst API platform (no public intelligence API was found on pages reviewed). | Official checkout reviewed 20 November 2026: Premium $39.99/year (also shown as $3.33/month billed annually), including unlimited comparison, Blindspot, My Feed, and factuality distribution. Vantage is the higher official tier (My News Bias, ownership data, all newsletters); a stable public list price for Vantage was not confirmed in this review because checkout offers vary by channel. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | News and media, CTI platforms | Threat-intel newsreader | AI models extract CVEs, threat actors, malware, TTPs, and IoCs from open-source reporting. Official docs describe clustering of differently written articles about the same event under “Also in,” rather than deleting duplicates. Standard includes AI feeds and Ask AI. Advanced adds Intel Agents and no-code OpenCTI, Cortex XSOAR, and MISP integrations. OpenCTI import is STIX 2.1 and requires the Advanced plan. | Official pricing page lists Standard and Advanced feature packages and “whole team access,” but no dollar amount. Third-party directories quote figures; those are not used here. |
| [Liveuamap](https://liveuamap.com/promo/api) | Event and geo | News event map | A live map of breaking events (conflict, protests, disasters, security incidents) with source links, regional maps, history, and notifications. The public map states events and areas of control are geolocated approximately. Official API: GeoJSON, regional coverage, and published request caps. Closest analogue to a “where news is happening” product. | Official API page: $150/month for 200 requests/day, all regions, GeoJSON, and email support; starting at $1,000/month for 1,500 requests/day, areas of interest, local languages, additional social sources, and priority support. 99.9% uptime is claimed for both. Multi-license discounts are offered. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | Investigation | Tool directory, not a platform | A regularly updated directory and review of mostly free open-source investigation tools (geolocation, maps and satellites, photo and video verification, web archiving, and more). Inclusion is not an endorsement. It is a workflow reference, not a hosted product, so most platform-feature cells are N/A. | Free to use as a directory. Individual listed tools have their own terms. |
| [OSINT Industries](https://www.osint.industries/pricing) | Investigation | Identifier search | Real-time search of email, phone, username, name, and crypto wallets across 1,500+ sources, with maps, activity timelines, breach flags via Have I Been Pwned, case storage, and exports (PDF, DOC, Excel, JSON). API access starts on the mid paid plan. The site claims “zero false positives”; treat that as a vendor claim, not a measured guarantee. This is people-and-account search, not news intelligence. | Published: £19/month (30 credits), £49/month (100 credits, API access), £99/month (300 credits, API). Annual billing is advertised with savings. Custom enterprise adds a support manager, shared credit pool, team seats, and SSO. Extra credits can be bought; the site says credits do not expire at month-end. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | Investigation | Open-source enrichment | MIT-licensed OSINT automation with 200+ modules, a web UI or CLI, a YAML correlation engine, and CSV/JSON/GEXF export. The GitHub README still advertises hosted SpiderFoot HX (monitoring, Slack, multi-user, REST API). HX's current commercial availability was not confirmed on a live official product page in this review, so only the open-source feature set is treated as verified. | Open source is free (MIT). HX pricing and current availability: unverified. |
| [OpenCTI](https://filigran.io/products/opencti) | CTI platforms | Open-source TIP | Filigran's STIX 2.1 knowledge-graph platform: investigations, ATT&CK mapping, dashboards, case management, TAXII 2.1, live streams, and 400+ connectors to SIEM, SOAR, and EDR tools. Community Edition is free (Apache 2.0). Enterprise Edition adds AI summaries, playbooks, PIRs, advanced RBAC, SSO, audit trails, and optional Filigran SaaS or air-gapped deploy. | Community Edition free. Enterprise Edition and Filigran SaaS are quote-based; no list price on pages reviewed. A 30-day Enterprise trial is advertised. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | News and media | Media-bias ratings | AllSides Media Bias Ratings and Chart rate outlets Left through Right using multipartisan editorial reviews and Blind Bias Surveys. Ratings are generally for written online content, not individual articles. Ground News incorporates these ratings as one of three inputs. Important: AllSides states the ratings are licensed CC BY-NC 4.0 for research or noncommercial use with attribution; commercial use requires a license agreement. | Consumer site plus a commercial data license (terms not priced publicly on pages reviewed). Do not ship AllSides ratings in a paid CoreNews product without that license. |

### Official-page notes by feature

#### Real-time alerting

Real-time alerting. Continuous detection and push of new events or mentions, with some control over noise. CoreNews: Planned (P2 / P3). MON-1 to MON-4 in P2 (watchlists, change alerts, Slack, dedupe, digests). Noise-tuning feedback is P3 (MON-5). Current triggers are infra, sanctions, vulns, and geo sensors — not news-velocity alerts.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Yes | Core product: real-time alerts from 1M+ public sources. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Yes | Platform alerts and an Alert API; playbook alerts. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Yes | Monitor dashboard, geofenced and keyword alerts, webhooks. |
| [Maltego](https://www.maltego.com/pricing/) | Partial | Maltego Monitor is real-time social and news monitoring, Enterprise-optional. |
| [Babel Street](https://www.babelstreet.com/platform) | Yes | OSINT Streams are described as always-on, enriched monitoring. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Partial | Select current-awareness feeds and a real-time AI News Feed; not a crisis-alert firehose. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Yes | Official typical delivery in 2–5 minutes; spike and sentiment alerts. |
| [Ground News](https://ground.news/rating-system) | Partial | Follow topics, places, and people; not Dataminr-style event alerting. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Partial | AI feeds and newsletters; not a breaking-event firehose. |
| [Liveuamap](https://liveuamap.com/promo/api) | Partial | App notifications and an event API; not a full watchlist platform. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Directory of tools, not a hosted alerting product. |
| [OSINT Industries](https://www.osint.industries/pricing) | No | On-demand search is the advertised model; continuous alerting was not found. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | OSS is scan-based. HX monitoring claims are unverified. |
| [OpenCTI](https://filigran.io/products/opencti) | Partial | Threat monitoring, playbooks (EE), and streams; not news breaking-alerts. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | No | Bias ratings and a balanced newsfeed, not real-time alerting. |

#### Story clustering / dedup

Story clustering / dedup. Group differently written articles about the same event, rather than only dropping exact duplicates. CoreNews: Not in roadmap (Add). The spec covers identifier dedup and statement models, not clustering of news stories across outlets.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Unverified | Agentic corroboration relates events; classic story clusters were not documented. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Unverified | Graph and reports connect events; news-story clustering was not documented. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Unverified | AI summarizes result sets; story-level clustering was not documented. |
| [Maltego](https://www.maltego.com/pricing/) | No | Not a news-cluster product. |
| [Babel Street](https://www.babelstreet.com/platform) | Unverified | Event and relationship mapping; story clustering was not documented. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Unverified | Analytics extract entities and topics. Current story-cluster UI was not confirmed. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Unverified | Mention and campaign monitoring; story clusters were not documented. |
| [Ground News](https://ground.news/rating-system) | Yes | Core: compare coverage of the same story across outlets. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Yes | Official docs: “Also in” groups differently written articles on the same event. |
| [Liveuamap](https://liveuamap.com/promo/api) | Partial | Events are placed on a map; not multi-outlet story clusters. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Not a hosting platform. |
| [OSINT Industries](https://www.osint.industries/pricing) | No | Identifier search, not news clustering. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | Correlation rules are for OSINT findings, not news stories. |
| [OpenCTI](https://filigran.io/products/opencti) | No | STIX correlation is not news-story clustering. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | Partial | Side-by-side left / center / right stories, not full event dedup. |

#### Source credibility / bias ratings

Source credibility / bias ratings. Publication-level bias, factuality, or reliability scores shown beside coverage. CoreNews: Partial in roadmap (P1). ENT-5 already plans Admiralty-style A–F / 1–6 scoring on every fact. Publication-level media bias and factuality ratings are not in the 71 requirements. AllSides data is CC BY-NC unless licensed.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | No | Corroboration and urgency, not media-bias ratings. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Partial | Risk Scores on entities and IOCs, not outlet bias or factuality. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | No | Sentiment is offered; publication bias ratings were not advertised. |
| [Maltego](https://www.maltego.com/pricing/) | No | Not advertised. |
| [Babel Street](https://www.babelstreet.com/platform) | No | Source-backed findings, not political-bias scores. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | No | Licensed news quality, not bias meters. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | No | Sentiment and relevance, not outlet bias ratings. |
| [Ground News](https://ground.news/rating-system) | Yes | Bias, factuality, and ownership at publication level; not article-level bias. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | No | Not advertised. |
| [Liveuamap](https://liveuamap.com/promo/api) | No | Source links only. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Not a ratings product. |
| [OSINT Industries](https://www.osint.industries/pricing) | No | Not advertised. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | Not advertised. |
| [OpenCTI](https://filigran.io/products/opencti) | Partial | Source and confidence on STIX objects, not media-bias charts. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | Yes | This is the product. Ratings are outlet-level; commercial reuse needs a license. |

#### Multilingual + translation

Multilingual + translation. Ingest or search in many languages, with translation back to the analyst's language. CoreNews: Planned late (P3). AI-6 translates documents in P3 and keeps the original beside the translation. Broad local-language news ingest is not specified.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Yes | Official: text in 150 languages, plus other modalities. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Partial | Official graph page says indexing across multiple languages; a count was not published there. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Yes | Search or translate in 100+ languages; results can be returned in English. |
| [Maltego](https://www.maltego.com/pricing/) | Unverified | Not emphasized on the pricing and product pages reviewed. |
| [Babel Street](https://www.babelstreet.com/platform) | Yes | Official: 200+ languages, including slang and coded language beyond literal translation. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Yes | Official: 33 content languages and 10 interface languages. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Partial | Global, multilingual monitoring is advertised; a language count was not confirmed. |
| [Ground News](https://ground.news/rating-system) | Unverified | US-political ratings context is explicit; global language coverage was not confirmed. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Unverified | Not documented on the pages reviewed. |
| [Liveuamap](https://liveuamap.com/promo/api) | Partial | Higher API tier lists local languages; the public site is largely English. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Depends on the listed tool. |
| [OSINT Industries](https://www.osint.industries/pricing) | Unverified | Not documented on the pages reviewed. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | Not a translation platform. |
| [OpenCTI](https://filigran.io/products/opencti) | Unverified | Not documented as a translation product on pages reviewed. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | Partial | Methodology is framed around the US political spectrum. |

#### Entity extraction and graph

Entity extraction and graph. Extract people, orgs, and indicators and let an analyst pivot on a graph. CoreNews: Planned (P1 / P2). Entity model in P0/P1, graph canvas and transforms in P1, layouts and path-finding in P2, extraction assist in P2.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Partial | Events, assets, and geovisualization; not a Maltego-style investigation graph. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Yes | Intelligence Graph with ontology and event graphs; entity extraction is core. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Partial | Author and actor profiles, location pivots; not a full link-analysis workbench. |
| [Maltego](https://www.maltego.com/pricing/) | Yes | Flagship graph, transforms, and entity pivots. |
| [Babel Street](https://www.babelstreet.com/platform) | Yes | Identity resolution and entity and relationship mapping. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Partial | Analytics extract entities for models; not an investigator graph UI. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | No | Media analytics, not an entity-investigation graph. |
| [Ground News](https://ground.news/rating-system) | No | Story and outlet comparison, not an entity graph. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Partial | Extracted CTI entities; the graph lives in OpenCTI after export. |
| [Liveuamap](https://liveuamap.com/promo/api) | No | Event pins, not an entity graph. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Directory only. |
| [OSINT Industries](https://www.osint.industries/pricing) | Partial | Linked accounts, maps, and timelines; not a general graph canvas. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | Partial | Visualisations and GEXF export from recursive modules. |
| [OpenCTI](https://filigran.io/products/opencti) | Yes | Native STIX 2.1 knowledge hypergraph, investigations, and pivoting. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | No | Not an investigation graph. |

#### Map

Map. Plot events, assets, or subject activity on a map, including geofences or time sliders. CoreNews: Partial in roadmap (P2). GEO-1/2 map FIRMS, USGS, OpenSky, AIS, and approximate IP — not a news-event layer like Liveuamap or GDELT.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Yes | Pulse geovisualization, geofences, custom views, Esri ArcGIS integration. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Unverified | Not confirmed as a first-class news or event map on pages reviewed. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Yes | Geospatial search, bounding boxes, inferred locations, Location Protection. |
| [Maltego](https://www.maltego.com/pricing/) | Yes | Browser Graph advertises map and histogram views. |
| [Babel Street](https://www.babelstreet.com/platform) | Unverified | Global collection is advertised; a map workspace was not confirmed here. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | No | Not advertised as a mapping product. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Unverified | Not confirmed on pages reviewed. |
| [Ground News](https://ground.news/rating-system) | Unverified | Users can follow places; a live event map was not confirmed. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | No | Not advertised. |
| [Liveuamap](https://liveuamap.com/promo/api) | Yes | The product is a live news-and-conflict map with a GeoJSON API. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | Partial | Toolkit categories cover maps, satellites, and geolocation tools. |
| [OSINT Industries](https://www.osint.industries/pricing) | Yes | Official: map a subject's activity and routes. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | Unverified | Some modules are geo-related; a news map is not the product. |
| [OpenCTI](https://filigran.io/products/opencti) | Unverified | Location STIX objects exist; a live news map was not advertised. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | No | Not a mapping product. |

#### AI summaries with citations

AI summaries with citations. Generated briefs that a user can trace to underlying sources or records. CoreNews: Planned (P2). AI-2 drops uncited sentences and links each remaining sentence to statement or evidence IDs. This can exceed many vendors' “AI summary” claims if it ships as specified.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Partial | ReGenAI tailored live briefs and a Real-Time Brief Builder. Sentence-level citations were not documented. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Yes | Official: AI reports are fully referenced and attributable; sessions are grounded in the graph. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Partial | AI result summaries and sentiment. Citation-level grounding was not documented. |
| [Maltego](https://www.maltego.com/pricing/) | Partial | Graph AI Assistant and Monitor AI analysis; citation enforcement was not documented. |
| [Babel Street](https://www.babelstreet.com/platform) | Yes | Official: source-backed findings, citations, and auditability under analyst control. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Yes | Retrieval API and AI News Feed are licensed for summarization, RAG, and generative use. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Yes | Official MCP answers are grounded in coverage and cite sources. |
| [Ground News](https://ground.news/rating-system) | Unverified | Not documented on pages reviewed. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Partial | Ask AI is a CTI-optimized LLM; citation enforcement was not documented. |
| [Liveuamap](https://liveuamap.com/promo/api) | No | Not advertised. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Not a hosted AI product. |
| [OSINT Industries](https://www.osint.industries/pricing) | Unverified | Not documented on pages reviewed. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | Not advertised in OSS. |
| [OpenCTI](https://filigran.io/products/opencti) | Yes | Enterprise Edition: AI imports, insights, summaries, and finished reports. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | No | Ratings are human-method, not generative summaries. |

#### Verification / fact-check tools

Verification / fact-check tools. Corroboration, media forensics, factuality, or fact-check markup — not just a credibility badge. CoreNews: Not in roadmap (Add). InVID / WeVerify was in the gap analysis as Next, then did not land in the 71-requirement spec. ClaimReview / fact-check ingest is also absent. Evidence capture (CAS-3/4) is planned in P2.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Partial | Agentic Corroboration searches official sources and imagery as events unfold. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Partial | Risk rules, Insikt research, and referenced AI — not a media-forensics bench. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Unverified | Threat-type detection is advertised; verification tooling was not documented. |
| [Maltego](https://www.maltego.com/pricing/) | Partial | Hunchly capture and Evidence preservation; not a fact-check engine. |
| [Babel Street](https://www.babelstreet.com/platform) | Partial | Visual Intelligence and source-linked findings; not a public fact-check corpus. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | No | Licensed journalism, not a verification workbench. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | No | Not a fact-checking tool. |
| [Ground News](https://ground.news/rating-system) | Partial | Publication factuality and Blindspots; not article-level fact checks or forensics. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | No | Not advertised. |
| [Liveuamap](https://liveuamap.com/promo/api) | Partial | Source links plus an approximate-geolocation disclaimer. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | Yes | Guides for photo and video verification, geolocation, and archiving. |
| [OSINT Industries](https://www.osint.industries/pricing) | Partial | Breach flags and a “zero false positives” claim; not media verification. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | Recon and enrichment, not verification. |
| [OpenCTI](https://filigran.io/products/opencti) | Partial | Source-linked intelligence objects; not news fact-checking. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | Partial | Bias transparency, not factual verification of claims. |

#### Collaboration / cases

Collaboration / cases. Shared cases, evidence, notes, and team workflows. CoreNews: Planned (P2). Cases, hashed web capture, custody chain, and cited report claims are P2.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Partial | Custom views, briefings, and collaboration around alerts; not a full case file. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Partial | Analyst notes and reports; Hunchly-style evidence cases were not confirmed. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Partial | Finished intelligence reports and analyst requests. |
| [Maltego](https://www.maltego.com/pricing/) | Yes | Maltego Cases, plus Hunchly and optional Evidence. |
| [Babel Street](https://www.babelstreet.com/platform) | Partial | Evidence-grade reports are advertised; a full case product was not detailed here. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Partial | Intranet and portal delivery via Select, not investigative cases. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Partial | Team sharing in Slack, Teams, and briefs; not OSINT case management. |
| [Ground News](https://ground.news/rating-system) | No | Consumer reading, not cases. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Partial | Team access, boards, folders, and newsletters. |
| [Liveuamap](https://liveuamap.com/promo/api) | No | Not advertised. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Not a collaboration platform. |
| [OSINT Industries](https://www.osint.industries/pricing) | Partial | Cloud cases and storage quotas by plan. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | OSS is single-operator. Multi-user was an HX claim (unverified). |
| [OpenCTI](https://filigran.io/products/opencti) | Yes | Centralized case management and real-time collaboration. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | No | Not a case product. |

#### API

API. A documented programmatic interface for search, alerts, or export. CoreNews: Planned (P2). Public REST API, keys, webhooks, and OpenAPI in P2 (PLT-6).

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Yes | Pulse and First Alert Advanced APIs; third-party connectors exist (e.g. Elastic). |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Yes | Broad API surface, MCP, and TAXII. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Partial | Webhooks are documented for Echosec alerts; a full public API catalog was not reviewed in depth. |
| [Maltego](https://www.maltego.com/pricing/) | Partial | Official: bring your own data via API and SDK into Graph; not a general intel query API. |
| [Babel Street](https://www.babelstreet.com/platform) | Yes | Official API-first platform for data and analytics. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Yes | A suite of developer APIs and feeds. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Yes | API Foundations included in most packages; streams and higher tiers available. |
| [Ground News](https://ground.news/rating-system) | Unverified | No public intelligence API was found on pages reviewed. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Yes | Documented REST API with bearer tokens. |
| [Liveuamap](https://liveuamap.com/promo/api) | Yes | Official paid API with GeoJSON and published quotas. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Not a platform API. A CSV export of the toolkit exists. |
| [OSINT Industries](https://www.osint.industries/pricing) | Yes | API access on the £49/month plan and above. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | Partial | Local/OSS automation; a hosted REST API was an HX claim (unverified). |
| [OpenCTI](https://filigran.io/products/opencti) | Yes | GraphQL/API platform with connectors and TAXII. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | Partial | CSV or JSON ratings are available under license; contact required. |

#### Integrations (STIX/TAXII, Slack, SIEM)

Integrations (STIX/TAXII, Slack, SIEM). Threat-intel standards and/or delivery into chat and security tools. CoreNews: Planned (P2 / P3). Slack in P2 alerts; STIX 2.1 and MISP export in P2; TAXII 2.1 and an OpenCTI connector in P3. Direct SIEM connectors are not named beyond those standards.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Partial | APIs, Esri, and SIEM connectors (e.g. Elastic). STIX/TAXII was not confirmed. Slack was not confirmed on pages reviewed. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Yes | TAXII 1.x (STIX 1.1.1) and TAXII 2.1 (STIX 2.1), SIEM/SOAR integrations, MCP. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Partial | Webhooks. STIX/TAXII and Slack were not confirmed on the Echosec pages reviewed. |
| [Maltego](https://www.maltego.com/pricing/) | Partial | Transforms and Connector Builder. STIX/TAXII and Slack were not advertised on pages reviewed. |
| [Babel Street](https://www.babelstreet.com/platform) | Partial | API-first into existing systems. STIX/TAXII was not confirmed on pages reviewed. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Partial | APIs, feeds, Salesforce app announced historically. Not a STIX/SIEM product. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Partial | Slack, Teams, Zapier, BI, CRM, warehouses, MCP. Not STIX or SIEM. |
| [Ground News](https://ground.news/rating-system) | No | Not advertised. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Yes | Advanced: OpenCTI (STIX 2.1), MISP, and Cortex XSOAR. |
| [Liveuamap](https://liveuamap.com/promo/api) | Partial | GeoJSON API. Not STIX, Slack, or SIEM. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Not a platform. |
| [OSINT Industries](https://www.osint.industries/pricing) | No | Exports and an API; STIX, Slack, and SIEM were not advertised. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | Partial | GEXF/CSV/JSON. HX claimed Splunk and Elasticsearch (unverified). No STIX in OSS. |
| [OpenCTI](https://filigran.io/products/opencti) | Yes | Native STIX 2.1, TAXII 2.1, 400+ SIEM/SOAR/EDR connectors. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | No | Ratings licensing, not security-tool integrations. |

#### Mobile

Mobile. An official mobile app or a clearly advertised mobile experience for alerts and review. CoreNews: Not in roadmap (Add). The spec is a web app. Leaders in alerting (Dataminr, Meltwater, Recorded Future, Liveuamap, Ground News) ship mobile. A high-quality PWA may be enough for v1.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Yes | Official: browser, mobile, email, and API delivery. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Yes | Official support documents an iOS and Android app, including Recorded Future AI. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Unverified | Not confirmed on the Echosec pages reviewed. |
| [Maltego](https://www.maltego.com/pricing/) | Unverified | Desktop and browser are the advertised clients. |
| [Babel Street](https://www.babelstreet.com/platform) | Unverified | Not confirmed on pages reviewed. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Unverified | A dedicated official mobile app was not confirmed in this review. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Yes | Official mobile app and push alerts; community docs cover Meltwater Mobile. |
| [Ground News](https://ground.news/rating-system) | Yes | Official iOS/Android apps; Vantage was still rolling out on mobile per the help center. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Unverified | Consumer Feedly has apps; a TI-specific mobile experience was not confirmed. |
| [Liveuamap](https://liveuamap.com/promo/api) | Yes | Official Liveuamap app is listed on the Apple App Store. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | N/A | Not a product app. |
| [OSINT Industries](https://www.osint.industries/pricing) | Unverified | Not confirmed on pages reviewed. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | No | Web UI or CLI. |
| [OpenCTI](https://filigran.io/products/opencti) | Unverified | Browser platform; a mobile app was not advertised. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | Unverified | Not confirmed in this review. |

#### Pricing model

Pricing model. How the vendor sells: published seats or credits, indicative ranges, or quote-only. CoreNews: Planned late (P3). P3 includes plans and billing. No CoreNews price is set. The market has clear published anchors and a large quote-only enterprise band.

| Product | Rating | What official pages say |
| --- | --- | --- |
| [Dataminr](https://www.dataminr.com/products/first-alert/) | Unverified | Quote only; no list price. |
| [Recorded Future](https://www.recordedfuture.com/platform/intelligence-graph) | Unverified | Quote only; structure is published, prices are not. |
| [Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) | Unverified | Request pricing; no list price. |
| [Maltego](https://www.maltego.com/pricing/) | Yes | Published euros-per-year seats, plus Enterprise quote. |
| [Babel Street](https://www.babelstreet.com/platform) | Unverified | No list price. |
| [Factiva](https://developer.dowjones.com/datasets/datasets-details-news) | Unverified | Licensed enterprise; no list price on pages reviewed. |
| [Meltwater](https://www.meltwater.com/en/products/real-time-alerting) | Partial | Official indicative USD ranges; not a fixed price list. |
| [Ground News](https://ground.news/rating-system) | Yes | Premium $39.99/year on official checkout. |
| [Feedly TI](https://feedly.com/threat-intelligence/pricing) | Partial | Named plans, no official dollar amount on the pricing page. |
| [Liveuamap](https://liveuamap.com/promo/api) | Yes | Published API tiers at $150 and from $1,000 per month. |
| [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) | Yes | Free directory. |
| [OSINT Industries](https://www.osint.industries/pricing) | Yes | Published pound-sterling monthly credit plans. |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | Yes | OSS free (MIT). |
| [OpenCTI](https://filigran.io/products/opencti) | Partial | CE free; EE and SaaS are quote-based. |
| [AllSides](https://www.allsides.com/media-bias/media-bias-rating-methods) | Partial | Free to read ratings; commercial data needs a paid license (unpublished). |

<a id="pricing"></a>

## Published pricing anchors

*Only figures a vendor published on an official page or official blog. Everything else is described, not guessed.*

| Product | Model | Published figure or official posture |
| --- | --- | --- |
| Ground News | Consumer annual | Premium $39.99/year on official checkout (20 Nov 2026). Vantage is a higher official tier; list price not confirmed as stable in this review. |
| OSINT Industries | Monthly credits | £19 / £49 / £99 per month (30 / 100 / 300 credits). API from £49. Custom enterprise with SSO and pooled credits. |
| Liveuamap API | Monthly API quota | $150/month (200 requests/day) and starting $1,000/month (1,500 requests/day). |
| Maltego | Annual seats | Basic €0; Entry Standard €3,000/year; Professional Standard €7,500/year (up to 5 seats, billed per seat); Enterprise quote. |
| Meltwater | Annual packages, indicative | Official blog, 9 July 2026: no fixed list. Indicative US USD ranges from $10,000 (Starter), $25,000 (Pro), and $130,000 (Enterprise) per year. |
| OpenCTI / SpiderFoot / Bellingcat toolkit | Open or free | OpenCTI Community and SpiderFoot OSS are free (Apache 2.0 and MIT). OpenCTI Enterprise is quote-based. The Bellingcat toolkit is a free directory. |
| Feedly TI | Named team plans | Standard and Advanced on the official pricing page; no dollar amount published there. |
| Recorded Future, Dataminr, Flashpoint, Babel Street, Factiva | Enterprise quote | No list prices on pages reviewed. Recorded Future publishes a package structure (Core / Professional / Elite) and sizes most deals by workforce credentials. |

> **Pricing implication, not a CoreNews price list.** Published anchors leave a wide open band: above consumer news (about $40/year) and credit-priced search (tens of pounds per month), and below Maltego Entry (€3,000/year) and Meltwater's indicative Starter ($10,000/year). That is the natural home for a transparent public-source workbench aimed at journalists, NGOs, and small CTI or due-diligence teams. Do not set CoreNews prices in this research note.

<a id="win"></a>

## Where CoreNews can win

*Differentiators that are realistic on free and public data. These are product choices, not a claim that collection depth will match the firehose vendors.*

### Win on explainability and public data

- Transparent provenance on every claim. Already specified (ENT-1). Few news products show source, collection time, license, and a raw hash as the unit of the interface.
- Admiralty / NATO-style source reliability and information credibility (A–F and 1–6). Already specified (ENT-5). This is analyst language Ground News bias meters do not replace.
- Claim tracking across outlets. Build a claim graph: first seen, who repeated it, who contested it, and any ClaimReview fact checks. This is not in the roadmap today.
- Early signals from public telemetry. GDELT updates every 15 minutes and officially allows commercial use. Wikimedia pageviews are a public API. Combined with FIRMS and USGS, this is a credible early-warning layer without buying a social firehose.
- Explainable, cite-or-drop AI. AI-2 is stricter than most “AI brief” marketing. Keep the evaluation harness in CI.
- Local-language and non-English coverage via GDELT (100+ languages; GDELT also describes translating 65 languages that it says represent 98.4% of its non-English volume). Translation in the workbench is currently scheduled only in P3 and only for documents.
- Narrative and disinformation tracking, later, as competing storylines with provenance — not as an unlicensed social-graph scrape.

### Do not try to out-collect these franchises

- Dataminr, Babel Street, and Flashpoint Echosec on real-time, multilingual, multi-modal social and event firehoses.
- Recorded Future, Flashpoint Ignite, and similar vendors on dark-web and underground collections.
- Factiva on licensed full-text archives (33,000+ sources). Do not scrape paywalled news.
- Maltego Data Pass, OSINT Industries, and Social Links-class people search after platform API restrictions.
- AllSides, Ad Fontes, or Media Bias Fact Check ratings inside a paid product without a license. AllSides is explicitly CC BY-NC 4.0.

<a id="trust"></a>

## Trust, quality, and compliance

*Not legal advice. This is the quality bar customers will use to compare CoreNews with enterprise tools. Re-read current terms before shipping.*

- Verification workflow: every news item should be able to move through states such as uncorroborated, corroborated by independent sources, contested, or withdrawn. Liveuamap already cautions that locations are approximate; CoreNews should show the same humility on maps and on AI. InVID / WeVerify and metadata checks belong in the workbench and are not in the current spec.
- Misinformation handling: do not bury this in the ethics policy. Analysts need a way to flag a claim, attach contrary sources, and keep the original. ClaimReview markup and licensed fact-check datasets are the interoperable path.
- Ethics policy: the spec already bans terms-violating scraping, stolen dumps, household identification from geolocation, and sock puppets (PLT-3). Publish it. Maltego Evidence advertises sock-puppet collection; CoreNews should keep the opposite stance and say so.
- GDPR and CCPA: person, email, phone, and social data is personal data. Define lawful basis, minimization, retention, access, and deletion before people connectors go live. Retention and legal hold are P3 (CAS-6); the policy work should not wait until then.
- Audit logs: already P1 (PLT-4). Exportable, append-only logs are what due-diligence and journalist users will ask for in a security review, alongside cases and evidence hashes in P2.
- SOC 2: readiness is a P3 exit item. Type I evidence collection should start in P2 (access control, change management, logging, vendor inventory, incident response). Maltego already advertises ISO 27001:2022; enterprise buyers will compare.
- Licensing: keep the P0 license gate. GDELT is an unusually clear commercial-friendly news dataset. AllSides is not, unless licensed. NewsAPI.org's developer tier remains unsafe for staging or production, as the gap analysis already flagged.

<a id="ux"></a>

## UX and product-quality bar

*Best-in-class here is time-to-insight and trust in the interface, not visual novelty.*

- Onboarding: first run should not be an empty graph. Show today's public-source map, one featured cluster, and a 5-minute scripted investigation (domain, CVE, or sanctions — already the P1 exit pilots). The spec's “under 5 minutes to a useful graph” target needs a designed path.
- Daily briefing: a morning digest of watched entities and clusters, every sentence cited, with a “what changed since yesterday” section. Dataminr and Meltwater treat briefs as a primary artifact; CoreNews currently treats reports as case exports.
- Alert noise: Meltwater's job-to-be-done is fewer, faster, more relevant alerts (official typical delivery 2–5 minutes; vendor claim of up to 90% less noise). CoreNews NFR is “watch interval plus 5 minutes.” For news spikes, aim closer to minutes. Keep MON-4 dedupe, throttle, and digests, and do not leave all tuning until P3.
- Accessibility: add WCAG 2.2 Level AA to the NFR table. Keyboard access to the graph and map, text alternatives, contrast, and reduced-motion matter for a professional workbench and for public-sector procurement.
- Performance: keep the current targets (search p95 under 300 ms at 50 million statements; entity page under 800 ms cached; graph expand under 1.5 s for 500 neighbors; 99.5% monthly availability at v1). Add a news-map target, for example p95 under 2 seconds to first tiles and event pins on the default view, to be validated in P0/P2.

<a id="gtm"></a>

## Go-to-market

*The spec already names four personas. Best-in-class positioning should pick a wedge that incumbents price out or ignore.*

Primary wedge: investigative journalists, NGO researchers, and small CTI or due-diligence teams. They need provenance, maps, and export into professional tools, and they often cannot buy Dataminr, Recorded Future, Babel Street, or Meltwater Enterprise. Secondary: newsroom OSINT desks and academic researchers, who already live in the Bellingcat-style toolkit world and will judge CoreNews on verification and citation quality. Do not lead with enterprise physical-security operations; that is Dataminr Pulse and Flashpoint Echosec territory.

| Segment | Job to be done | Why CoreNews can be credible | Where it will lose if oversold |
| --- | --- | --- | --- |
| Journalist / NGO investigator | Verify a claim, see who else reported it, document evidence | Provenance, Admiralty scores, claim tracker, hashed capture, public news map | Live social firehoses and paywalled full text |
| Small CTI team | Triage an indicator and export to a TIP | Playbooks, graph, STIX/MISP/OpenCTI, vulnerability pack | Underground intel and huge commercial collections |
| Due diligence / compliance | Screen a name and reproduce the decision later | Official sanctions lists, explainable matches, audit log | Compliance-grade PEP and beneficial ownership without a license |
| Newsroom desk / academic | Follow a story across languages and maps | GDELT, clusters, briefings, local-language coverage | Factiva's licensed archive and Dataminr's speed at global scale |

Positioning statement options (for debate, not a final brand line):

1. The provenance-first workbench for public news and OSINT: every claim traces to a hashed source.
2. See where a story is happening, who is reporting it, and how strong the evidence is — without a black-box collection.
3. Best-in-class public-source intelligence for teams who cannot buy an enterprise firehose, built to export into OpenCTI and MISP rather than replace them.

1. **Community or NGO tier.** The market analogue is Maltego Basic, OpenCTI Community, SpiderFoot OSS, and the Bellingcat toolkit: a real product, not a crippled demo, with clear license and quota limits.
2. **Professional team tier.** Sit above Ground News and OSINT Industries credits, and below Maltego Entry (€3,000/year) and Meltwater's indicative Starter ($10,000/year). This is where cases, the API, and cited briefings should live.
3. **Organization tier.** Quote-based, like the enterprise majority of this set: SSO, SCIM, SOC 2, retention, and a license-cleared commercial mode. Still positioned as the open, inspectable alternative — not a cheaper Recorded Future.

<a id="checklist"></a>

## Best-in-class checklist, mapped to the roadmap

*In roadmap means the item is already in SYSTEM_SPEC.md or ROADMAP.md. The other items are recommended additions. Phases follow the existing 40-week plan.*

Showing 24 of 24 items. 13 recommended items are not in the current spec or roadmap.

| Best-in-class item | Phase | In current roadmap? | Notes |
| --- | --- | --- | --- |
| Provenance on every fact (source, collected-at, license, raw hash) | P0 | Yes | ENT-1, ING-3. Keep this as the default UI unit, not a footer. |
| License gate that blocks non-commercial sources in commercial mode | P0 | Yes | ING-5. Launch blocker if CoreNews is sold. |
| Admiralty-style reliability (A–F) and credibility (1–6) on every statement | P1 | Yes | ENT-5. Already specified; make it visible and explained, not a hidden score. |
| Ethical-use policy acceptance and blocked-use list | P1 | Yes | PLT-3. Publish the same policy externally as a trust asset. |
| Append-only audit log of search, enrich, export, and admin actions | P1 | Yes | PLT-4. |
| Time-to-first-insight onboarding: a live news map and one scripted investigation in under 5 minutes | P1 | No — add | The 5-minute graph target is a persona success signal only. There is no onboarding requirement. |
| GDELT news-event ingest (commercial use is explicitly allowed) with required citation | P1 | No — add | GDELT terms: unlimited use for academic, commercial, or government use without fee. 15-minute updates, 100+ languages, history to 1979. Not in the 71 FRs. |
| News-event map layer with source links and an approximate-geolocation disclaimer | P2 | No — add | GEO-1 maps sensors and transport, not news pins. This is the Liveuamap-class gap. |
| Story clustering and cross-outlet coverage comparison | P2 | No — add | Feedly “Also in” and Ground News story pages are the bar. Not in the spec. |
| Cited AI summaries that drop uncited sentences | P2 | Yes | AI-2 and the evaluation harness (AI-4). A genuine differentiator if enforced. |
| Daily (and on-demand) briefing over watched topics, with citations | P2 | No — add | Dataminr Brief Builder and Meltwater/Teams briefs are the pattern. Not in the spec. |
| Claim tracking across outlets, using ClaimReview / fact-check feeds where licensed | P2 | No — add | CAS-5 only cites claims inside a CoreNews report. Cross-outlet claim graphs are absent. |
| Image and video verification (InVID / WeVerify, metadata) presented as leads, not proof | P2 | No — add | In the gap analysis as Next; dropped from the 71-requirement spec. |
| Alert noise controls: dedupe, throttle, digests, sensitivity, and a feedback loop | P2 | Yes | Dedupe, throttle, and digests are P2 (MON-4). The feedback loop is P3 (MON-5). Consider pulling a first noise-tuning pass into P2. |
| Misinformation handling workflow: corroboration states, contest, and analyst adjudication | P2 | No — add | Ethics policy is not the same as a product workflow for disputed claims. |
| WCAG 2.2 AA accessibility target added to the NFR table | P2 | No — add | Not in the current non-functional requirements. |
| GDPR / CCPA: lawful basis, minimization, retention, access, and deletion before people connectors | P2 | Yes | Named in the spec; CAS-6 retention and legal hold ship in P3. Define the policy earlier. |
| Early-signal pack: GDELT volume spikes, Wikimedia pageview spikes, plus FIRMS/USGS already planned | P2 | No — add | MON-3 does not include news or attention spikes. Wikimedia Pageviews is an official public API. |
| Translation of foreign-language documents and, later, local-language news coverage | P3 | Yes | AI-6 is documents only. Local-language news breadth is still a gap. |
| Narrative and disinformation tracking (competing storylines, reuse, coordinated amplification) | P3 | No — add | Not in the roadmap. Do this only on licensed or clearly public data. |
| Mobile app or an excellent offline-capable PWA for alerts and briefings | P3 | No — add | Not in the roadmap. Leaders in alerting all have mobile. |
| Licensed publication-level bias or factuality data, or a first-party method — never unlicensed AllSides or MBFC reuse | P3 | No — add | AllSides is CC BY-NC 4.0; commercial use needs a license. |
| SOC 2 readiness, with control mapping started in P2 rather than only at the end of P3 | P3 | Yes | P3 already lists SOC 2 readiness. Audits take months; start evidence collection in P2. |
| SAML SSO, SCIM, commercial license remediation, and published plans | P3 | Yes | PLT-8 and P3 launch work. |

> **Highest-priority additions** If only a few items can be inserted into the live coding plan, add these: GDELT-powered news map and story clusters; claim tracking; early-signal spikes; a cited daily briefing; InVID-style verification (dropped from the spec); WCAG 2.2 AA; and a designed 5-minute onboarding path.

<a id="sources"></a>

## Sources

*Official pages and documentation reviewed for this note. Dates are America/New_York.*

- [Dataminr First Alert](https://www.dataminr.com/products/first-alert/) — dataminr.com
- [Dataminr First Alert Advanced announcement](https://www.dataminr.com/press/announcement/dataminr-launches-first-alert-advanced-awarded-dow-contract/) — dataminr.com
- [Dataminr Pulse geovisualization](https://www.dataminr.com/pulse/corporate-security/geovisualization/) — dataminr.com
- [Recorded Future Intelligence Graph](https://www.recordedfuture.com/platform/intelligence-graph) — recordedfuture.com
- [Recorded Future AI](https://www.recordedfuture.com/platform/ai) — recordedfuture.com
- [Recorded Future pricing](https://www.recordedfuture.com/pricing) — recordedfuture.com
- [Recorded Future STIX/TAXII](https://docs.recordedfuture.com/reference/stix-taxii-overview) — docs.recordedfuture.com
- [Echosec by Flashpoint](https://flashpoint.io/ignite/echosec-by-flashpoint/) — flashpoint.io
- [Flashpoint pricing](https://flashpoint.io/pricing/) — flashpoint.io
- [Maltego pricing](https://www.maltego.com/pricing/) — maltego.com
- [Babel Street platform](https://www.babelstreet.com/platform) — babelstreet.com
- [Dow Jones news datasets](https://developer.dowjones.com/datasets/datasets-details-news) — developer.dowjones.com
- [Factiva supported languages](https://developer.dowjones.com/documents/factiva_integration-essentials-supported_languages) — developer.dowjones.com
- [Meltwater real-time alerting](https://www.meltwater.com/en/products/real-time-alerting) — meltwater.com
- [Meltwater integrations and API](https://www.meltwater.com/en/platform/integrations-api) — meltwater.com
- [Meltwater pricing blog](https://www.meltwater.com/en/blog/meltwater-pricing) — meltwater.com
- [Ground News rating system](https://ground.news/rating-system) — ground.news
- [AllSides rating methods (includes license)](https://www.allsides.com/media-bias/media-bias-rating-methods) — allsides.com
- [Feedly TI pricing](https://feedly.com/threat-intelligence/pricing) — feedly.com
- [Feedly clustering docs](https://developers.feedly.com/docs/what-is-clustering) — developers.feedly.com
- [Feedly OpenCTI integration](https://developers.feedly.com/docs/integrate-with-opencti) — developers.feedly.com
- [Liveuamap API pricing](https://liveuamap.com/promo/api) — liveuamap.com
- [Bellingcat toolkit](https://bellingcat.gitbook.io/toolkit) — bellingcat.gitbook.io
- [OSINT Industries pricing](https://www.osint.industries/pricing) — osint.industries
- [SpiderFoot (OSS)](https://github.com/smicallef/spiderfoot) — github.com
- [OpenCTI (Filigran)](https://filigran.io/products/opencti) — filigran.io
- [GDELT Project](https://www.gdeltproject.org/) — gdeltproject.org
- [GDELT terms of use](https://gdeltproject.org/about.html) — gdeltproject.org
- [Wikimedia Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html) — doc.wikimedia.org
- [Schema.org ClaimReview](https://schema.org/ClaimReview) — schema.org
