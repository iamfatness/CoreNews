"""Normalized search records and certificates from public transparency logs."""

import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel


class ResearchRecord(BaseModel):
    id: str
    record_type: str
    title: str
    source: str
    source_url: str
    collected_at: datetime


class CertificateRecord(ResearchRecord):
    record_type: Literal["certificate_transparency"] = "certificate_transparency"
    logged_at: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    issuer: str | None = None
    names: list[str]


class CertificateSearchResults(BaseModel):
    query: str
    source: Literal["crt.sh"] = "crt.sh"
    total: int
    records: list[CertificateRecord]


DOMAIN_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def normalize_domain(value: str) -> str:
    domain = value.strip().lower().removesuffix(".")
    labels = domain.split(".")
    if (
        len(domain) > 253
        or len(labels) < 2
        or labels[-1].isdigit()
        or not all(DOMAIN_LABEL.fullmatch(label) for label in labels)
    ):
        raise ValueError("Enter a domain such as example.org. Use Punycode for internationalized names.")
    return domain


def source_text(value: object) -> str | None:
    return (value.strip() or None) if isinstance(value, str) else None


def source_time(value: object) -> str | None:
    text = source_text(value)
    if text is None or ("T" not in text and " " not in text):
        return None
    try:
        return datetime.fromisoformat(text).isoformat()
    except ValueError:
        return None


def normalize_certificates(
    domain: str, rows: list, limit: int
) -> CertificateSearchResults:
    collected_at = datetime.now(timezone.utc).replace(microsecond=0)
    records = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        certificate_id = str(row.get("id", ""))
        if not re.fullmatch(r"[1-9][0-9]{0,19}", certificate_id) or certificate_id in seen:
            continue
        seen.add(certificate_id)

        names = dict.fromkeys(
            name for line in (source_text(row.get("name_value")) or "").splitlines()
            if (name := line.strip())
        )
        records.append(
            CertificateRecord(
                id=f"crtsh:{certificate_id}",
                title=source_text(row.get("common_name")) or next(iter(names), domain),
                source="crt.sh",
                source_url=f"https://crt.sh/?id={certificate_id}",
                collected_at=collected_at,
                logged_at=source_time(row.get("entry_timestamp")),
                valid_from=source_time(row.get("not_before")),
                valid_until=source_time(row.get("not_after")),
                issuer=source_text(row.get("issuer_name")),
                names=list(names),
            )
        )
        if len(records) == limit:
            break
    return CertificateSearchResults(query=domain, total=len(rows), records=records)
