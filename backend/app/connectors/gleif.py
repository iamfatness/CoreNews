"""Public organization reference data indexed by LEI."""

import re
import unicodedata
from datetime import datetime, timezone
from typing import Literal

import httpx
from pydantic import BaseModel

from ..records import ResearchRecord, source_text

SOURCE = "GLEIF"
WEBSITE = "https://www.gleif.org/en/lei-data/gleif-api/"
ENDPOINT = "https://api.gleif.org/api/v1/lei-records"
LEI = re.compile(r"[A-Z0-9]{18}[0-9]{2}")
PAGE_SIZE = 12


class OrganizationRecord(ResearchRecord):
    record_type: Literal["legal_entity"] = "legal_entity"
    lei: str
    jurisdiction: str | None
    registration_status: str | None
    entity_status: str | None
    updated_at: datetime | None


class OrganizationResults(BaseModel):
    query: str
    source: str = SOURCE
    total: int
    records: list[OrganizationRecord]


def timestamp(value: object) -> datetime | None:
    if isinstance(value, str):
        try:
            result = datetime.fromisoformat(value)
            return result if result.utcoffset() is not None else None
        except ValueError:
            pass
    return None


def normalized_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def normalize(query: str, payload: object) -> OrganizationResults:
    data = payload.get("data") if isinstance(payload, dict) else None
    entries = [data] if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError("GLEIF did not return organization records.")
    collected = datetime.now(timezone.utc).replace(microsecond=0)
    identifier = query.upper() if LEI.fullmatch(query.upper()) else None
    records = {}
    for entry in entries:
        attributes = entry.get("attributes") if isinstance(entry, dict) else None
        if not isinstance(attributes, dict):
            raise ValueError("GLEIF returned an invalid organization record.")
        lei, entity, registration = (attributes.get(field) for field in ("lei", "entity", "registration"))
        if not isinstance(lei, str) or not LEI.fullmatch(lei) or not isinstance(entity, dict) or not isinstance(registration, dict):
            raise ValueError("GLEIF returned invalid organization identifiers or metadata.")
        legal_name = entity.get("legalName")
        name = source_text(legal_name.get("name")) if isinstance(legal_name, dict) else None
        if name is None:
            raise ValueError("GLEIF returned an organization without its legal name.")
        if identifier and lei != identifier:
            raise ValueError("GLEIF returned a record for a different LEI.")
        if identifier is None and normalized_name(name) != normalized_name(query):
            continue
        records[lei] = OrganizationRecord(
            id="gleif:" + lei, title=name, source=SOURCE, source_url=ENDPOINT + "/" + lei,
            collected_at=collected, lei=lei, jurisdiction=source_text(entity.get("jurisdiction")),
            entity_status=source_text(entity.get("status")), registration_status=source_text(registration.get("status")),
            updated_at=timestamp(registration.get("lastUpdateDate")),
        )
    return OrganizationResults(query=query, total=len(records), records=list(records.values()))


async def search(query: str) -> OrganizationResults:
    identifier = query.upper() if LEI.fullmatch(query.upper()) else None
    url = ENDPOINT + "/" + identifier if identifier else ENDPOINT
    params = None if identifier else {"filter[entity.legalName]": query, "page[size]": PAGE_SIZE}
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(url, params=params)
        if identifier and response.status_code == 404:
            return OrganizationResults(query=query, total=0, records=[])
        response.raise_for_status()
        return normalize(query, response.json())
