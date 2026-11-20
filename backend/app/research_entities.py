from typing import Literal

from .connectors.edgar import FilingRecord
from .connectors.gdelt import NewsRecord
from .connectors.usgs import EarthquakeRecord
from .records import CertificateRecord, normalize_domain

EntityKind = Literal["domain", "company"]


def entity_domain(value: str) -> str | None:
    try:
        return normalize_domain(value)
    except ValueError:
        return None


def entity_matches(record: CertificateRecord | FilingRecord | NewsRecord | EarthquakeRecord, kind: EntityKind, key: str) -> bool:
    if kind == "company":
        return isinstance(record, FilingRecord) and record.cik == key
    if isinstance(record, CertificateRecord):
        return any(entity_domain(name) == key for name in [record.title, *record.names])
    if isinstance(record, NewsRecord):
        return entity_domain(record.publisher_domain) == key
    return False


def observation_time(record: CertificateRecord | FilingRecord | NewsRecord | EarthquakeRecord) -> tuple[str, str]:
    if isinstance(record, EarthquakeRecord) and record.occurred_at:
        return record.occurred_at.isoformat(), "Event time"
    if isinstance(record, FilingRecord) and record.filed_on:
        return record.filed_on.isoformat(), "Filed"
    if isinstance(record, NewsRecord) and record.seen_at:
        return record.seen_at.isoformat(), "Seen by GDELT"
    if isinstance(record, CertificateRecord) and record.logged_at:
        return record.logged_at, "Logged by crt.sh"
    return record.collected_at.isoformat(), "Collected by CoreNews"
