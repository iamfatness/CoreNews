# Free OSINT Sources Inventory

## Keyless / No Registration Required
- **crt.sh** — Certificate Transparency logs
- **Wayback Machine CDX API** — Historical web snapshots
- **GDELT DOC API / GEO API** — Global event and news data
- **RDAP / ICANN Lookup** — Domain registration data
- **OpenStreetMap / Nominatim** — Geocoding
- **USGS Earthquakes**
- **NASA FIRMS** — Fire data
- **Common Crawl** (bulk)
- **BGPView / RIPEstat** — IP / ASN data
- **URLhaus / ThreatFox (abuse.ch)** — Threat indicators
- **OpenSanctions bulk data** — Free for non-commercial use (no key)

## Free-Tier Accounts (API Keys Available)
These were registered via the OpenIntel Grok Bot under a dedicated Gmail. Logins are stored in the user's vault. Keys live on the respective service dashboards.

| Service | Status | Notes |
|---------|--------|-------|
| Shodan | Active | Free account, key on account page |
| Censys | Active | Free Plan, create personal access token |
| VirusTotal | Active | Free API key available |
| AlienVault OTX | Active | Key on settings page |
| AbuseIPDB | Active | Free tier key created |
| urlscan.io | Active | Free API key created |
| Hunter.io | Active | Free plan (50 credits/mo) |
| GreyNoise | Account only | No Community API key for personal email domains |

## Skipped / Limited
- **OpenSanctions API**: Free keys only for approved public-interest work. Use bulk downloads instead.
- **Have I Been Pwned**: Full breach API is paid. Pwned Passwords range API is free and keyless.

## Priority Connectors for MVP
1. GDELT (events / news)
2. crt.sh (domains / certificates)
3. OpenSanctions bulk (entities / sanctions)
4. Shodan free tier
5. VirusTotal free
6. urlscan.io
7. AbuseIPDB

## Notes
- Always respect rate limits.
- Prefer keyless sources when functionally equivalent.
- Store keys in a secure vault, never hardcode.
