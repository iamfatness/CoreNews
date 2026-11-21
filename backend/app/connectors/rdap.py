"""Read public domain registration metadata from the authoritative registry."""

from datetime import datetime, timezone
from typing import Literal

import httpx
from pydantic import BaseModel

from ..records import ResearchRecord, normalize_domain

SOURCE = "Registry RDAP"
BOOTSTRAP = "https://data.iana.org/rdap/dns.json"
REGISTRIES = {
    "com": "https://rdap.verisign.com/com/v1/domain/",
    "net": "https://rdap.verisign.com/net/v1/domain/",
    "org": "https://rdap.publicinterestregistry.org/rdap/domain/",
}


class DomainRegistration(ResearchRecord):
    record_type: Literal["domain_registration"] = "domain_registration"
    domain: str
    statuses: list[str]
    registered_at: datetime | None
    registry_changed_at: datetime | None
    expires_at: datetime | None


class DomainResults(BaseModel):
    query: str
    source: str = SOURCE
    total: int
    records: list[DomainRegistration]


def registry_domain(value: str) -> str | None:
    canonical = normalize_domain(value)
    name, suffix = canonical.split(".")[-2:]
    return f"{name}.{suffix}" if suffix in REGISTRIES else None


def normalize(domain: str, payload: object) -> DomainRegistration:
    if not isinstance(payload, dict) or payload.get("objectClassName") != "domain":
        raise ValueError("RDAP did not return a domain object.")
    returned = payload.get("ldhName")
    if not isinstance(returned, str) or normalize_domain(returned) != domain:
        raise ValueError("RDAP returned a record for a different domain.")
    events = payload.get("events")
    observed = {}
    if isinstance(events, list):
        for event in events:
            if not isinstance(event, dict) or event.get("eventAction") not in ("registration", "last changed", "expiration"):
                continue
            value = event.get("eventDate")
            if not isinstance(value, str):
                continue
            try:
                date = datetime.fromisoformat(value)
                if date.utcoffset() is not None:
                    observed.setdefault(event["eventAction"], date)
            except ValueError:
                continue
    statuses = payload.get("status")
    return DomainRegistration(
        id="rdap:" + domain, title=domain, source=SOURCE,
        source_url=REGISTRIES[domain.rsplit(".", 1)[1]] + domain,
        collected_at=datetime.now(timezone.utc).replace(microsecond=0), domain=domain,
        statuses=[s for s in statuses if isinstance(s, str) and 0 < len(s) <= 50][:20] if isinstance(statuses, list) else [],
        registered_at=observed.get("registration"), registry_changed_at=observed.get("last changed"),
        expires_at=observed.get("expiration"),
    )


async def search(domain: str) -> DomainResults:
    url = REGISTRIES[domain.rsplit(".", 1)[1]] + domain
    async with httpx.AsyncClient(timeout=8, follow_redirects=False) as client:
        reply = await client.get(url, headers={"Accept": "application/rdap+json"})
        if reply.status_code == 404:
            return DomainResults(query=domain, total=0, records=[])
        reply.raise_for_status()
    return DomainResults(query=domain, total=1, records=[normalize(domain, reply.json())])
