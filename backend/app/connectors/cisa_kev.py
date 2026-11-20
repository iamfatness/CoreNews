"""Exact CVE lookup for remediation records from CISA's public KEV mirror."""

import asyncio
import json
import re
from datetime import date, datetime, timezone
from time import monotonic
from typing import Literal

import httpx
from pydantic import BaseModel

from ..records import ResearchRecord, source_text

SOURCE = "CISA KEV"
CATALOG = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
FEED = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json"
CVE = re.compile(r"CVE-[0-9]{4}-[0-9]{4,12}")
MAX_BYTES = 8 * 1024 * 1024


class AdvisoryRecord(ResearchRecord):
    record_type: Literal["cisa_advisory"] = "cisa_advisory"
    cve: str
    vendor: str | None
    product: str | None
    added_on: date
    action: str | None
    federal_due_on: date | None
    catalog_version: str


class AdvisoryResults(BaseModel):
    query: str
    source: str = SOURCE
    total: int
    records: list[AdvisoryRecord]


def normalize_cve(value: str) -> str:
    identifier = value.strip().upper()
    if not CVE.fullmatch(identifier):
        raise ValueError("Enter a CVE identifier in the form CVE-YYYY-NNNN.")
    return identifier


def optional_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def normalize_catalog(payload: object) -> dict[str, AdvisoryRecord]:
    rows = payload.get("vulnerabilities") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows or payload.get("count") != len(rows):
        raise ValueError("CISA did not return a complete advisory catalog.")
    version = source_text(payload.get("catalogVersion"))
    if not version:
        raise ValueError("The CISA catalog version is unavailable.")
    collected = datetime.now(timezone.utc).replace(microsecond=0)
    records = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("CISA returned an invalid advisory.")
        cve = row.get("cveID")
        added_on = optional_date(row.get("dateAdded"))
        if not isinstance(cve, str) or not CVE.fullmatch(cve) or cve in records or not added_on:
            raise ValueError("CISA returned an invalid or duplicated advisory reference.")
        records[cve] = AdvisoryRecord(
            id=f"cisa:{cve}", cve=cve, title=source_text(row.get("vulnerabilityName")) or cve,
            source=SOURCE, source_url=f"{CATALOG}?search_api_fulltext={cve}", collected_at=collected,
            vendor=source_text(row.get("vendorProject")), product=source_text(row.get("product")),
            added_on=added_on, action=source_text(row.get("requiredAction")),
            federal_due_on=optional_date(row.get("dueDate")), catalog_version=version,
        )
    return records


class CisaKevConnector:
    def __init__(self):
        self.cached: tuple[float, dict[str, AdvisoryRecord]] | None = None
        self.lock = asyncio.Lock()

    async def catalog(self):
        async with self.lock:
            if self.cached and monotonic() < self.cached[0]:
                return self.cached[1]
            body = bytearray()
            async with asyncio.timeout(12), httpx.AsyncClient(timeout=8) as client:
                async with client.stream("GET", FEED) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        if len(body) + len(chunk) > MAX_BYTES:
                            raise ValueError("The CISA catalog exceeds the configured download limit.")
                        body.extend(chunk)
            records = normalize_catalog(json.loads(body))
            self.cached = (monotonic() + 300, records)
            return records

    async def search(self, identifier: str) -> AdvisoryResults:
        row = (await self.catalog()).get(identifier)
        records = [row] if row else []
        return AdvisoryResults(query=identifier, total=len(records), records=records)
