"""Route a single research query to compatible sources and cite useful patterns."""

import asyncio
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Annotated, Literal
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StringConstraints
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from .. import ofac_catalog
from ..connectors.cisa_kev import CVE
from ..connectors.gdelt import NewsRecord
from ..connectors.gleif import LEI
from ..connectors.rdap import registry_domain
from ..records import normalize_domain
from ..workspace_access import issue_proof
from . import geo, research
from .research import RecordSelection, Workspace

router = APIRouter(prefix="/api/research", tags=["research workbench"])
Intent = Literal["auto", "domain", "organization", "advisory", "earthquake", "topic"]
Status = Literal["results", "no_match", "unavailable", "setup_required", "not_applicable"]
MAX_PER_SOURCE = 12
SOURCES = {key: value[0] for key, value in (research.SOURCES | research.SUPPLEMENTAL_SOURCES).items()}
QUAKES = re.compile(r"\b(?:earthquakes?|quakes?|seismic)\b", re.IGNORECASE)
COMPANY = re.compile(r"\b(?:inc|corp|corporation|llc|plc|ltd|limited|gmbh|company)\.?$", re.IGNORECASE)
FILER = re.compile(r"[A-Z][A-Z0-9-]{0,5}|0*[1-9][0-9]{0,9}")


class WorkbenchInput(BaseModel):
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=160)]
    intent: Intent = "auto"


class SourceOutcome(BaseModel):
    id: str
    name: str
    status: Status
    query: str | None = None
    reason: str | None = None
    available: int = 0
    shown: int = 0


class Insight(BaseModel):
    title: str
    explanation: str
    record_ids: list[str]


class WorkbenchResults(BaseModel):
    intent: Intent
    query: str
    sources: list[SourceOutcome]
    insights: list[Insight]
    records: list[RecordSelection]


@dataclass
class Batch:
    outcome: SourceOutcome
    records: list[RecordSelection]


def query_domain(query: str) -> str | None:
    try:
        host = urlsplit(query).hostname if query.lower().startswith(("https://", "http://")) else query
        return normalize_domain(host or "")
    except ValueError:
        return None


def plan(query: str, intent: Intent) -> tuple[Intent, dict[str, str]]:
    host = query_domain(query)
    identifier = LEI.fullmatch(query.upper())
    if intent == "auto":
        if CVE.fullmatch(query.upper()):
            intent = "advisory"
        elif host:
            intent = "domain"
        elif QUAKES.search(query):
            intent = "earthquake"
        elif identifier or COMPANY.search(query) or FILER.fullmatch(query):
            intent = "organization"
        else:
            intent = "topic"
    if intent == "domain":
        if not host:
            raise HTTPException(422, "Enter a domain or a website URL.")
        registration = registry_domain(host)
        queries = {"crtsh": host, "gdelt": host}
        if registration:
            queries["rdap"] = registration
        return intent, queries
    if intent == "advisory":
        if not CVE.fullmatch(query.upper()):
            raise HTTPException(422, "Enter a CVE identifier in the form CVE-YYYY-NNNN.")
        return intent, {"cisa": query.upper(), "gdelt": query.upper()}
    if intent == "earthquake":
        return intent, {"usgs": query, "gdelt": query if QUAKES.search(query) else query + " earthquake"}
    if intent == "organization":
        if identifier:
            return intent, {"gleif": query.upper()}
        if FILER.fullmatch(query):
            return intent, {"edgar": query, "gdelt": query}
        return intent, {"gleif": query, "ofac": query, "gdelt": query}
    return intent, {"gdelt": query}


async def fetch_ofac(workspace_id: str, query: str):
    snapshot, records = await run_in_threadpool(ofac_catalog.lookup, query, None)
    if snapshot is None:
        raise HTTPException(503, "Import an OFAC SDN snapshot to enable exact-name candidate lookup.")
    return len(records), [
        RecordSelection(record=row, proof=issue_proof(workspace_id, row)) for row in records[:MAX_PER_SOURCE]
    ]


async def fetch_quakes(workspace_id: str, query: str):
    words = set(re.findall(r"\w+", QUAKES.sub("", query).casefold())) - {"in", "near", "at", "the", "recent", "week", "worldwide"}
    rows = await geo.usgs.events("week")
    matches = [row for row in rows if words.issubset(set(re.findall(r"\w+", row.title.casefold())))]
    matches.sort(key=lambda row: row.occurred_at or row.collected_at, reverse=True)
    return len(matches), [
        RecordSelection(record=row, proof=issue_proof(workspace_id, row)) for row in matches[:MAX_PER_SOURCE]
    ]


async def fetch(workspace_id: str, source: str, query: str) -> Batch:
    outcome = SourceOutcome(id=source, name=SOURCES[source], query=query, status="unavailable")
    if not research.source_enabled(source):
        outcome.status = "setup_required"
        outcome.reason = "This source is disabled or requires configuration."
        return Batch(outcome, [])
    try:
        async with asyncio.timeout(12):
            if source == "ofac":
                total, rows = await fetch_ofac(workspace_id, query)
            elif source == "usgs":
                total, rows = await fetch_quakes(workspace_id, query)
            else:
                result = await research.source_search(workspace_id, source, query)
                total, rows = result.total, result.records[:MAX_PER_SOURCE]
    except HTTPException as failure:
        outcome.status = {404: "no_match", 422: "not_applicable"}.get(failure.status_code, "unavailable")
        if source == "ofac" and failure.status_code == 503 and str(failure.detail).startswith("Import"):
            outcome.status = "setup_required"
        outcome.reason = str(failure.detail)
        return Batch(outcome, [])
    except (httpx.TimeoutException, TimeoutError):
        outcome.reason = "The source timed out. Results from other sources are still available."
        return Batch(outcome, [])
    except (httpx.HTTPError, SQLAlchemyError, ValueError):
        outcome.reason = "The source could not return usable records."
        return Batch(outcome, [])
    outcome.status = "results" if rows else "no_match"
    outcome.available, outcome.shown = total, len(rows)
    if source == "gleif" and not LEI.fullmatch(query.upper()):
        outcome.reason = "Exact legal-name matches among the first 12 records returned by GLEIF."
    elif source == "ofac":
        outcome.reason = "Primary organization names in the latest imported snapshot."
    elif source == "usgs":
        outcome.reason = "Magnitude 2.5+ events from the past seven days. Place terms are matched in the event title."
    return Batch(outcome, rows)


def derive_insights(batches: dict[str, Batch]) -> list[Insight]:
    found = {key: [item.record for item in batch.records] for key, batch in batches.items() if batch.records}
    insights = []
    domain_comparison = "rdap" in found and "crtsh" in found
    if len(found) > 1 and not domain_comparison:
        insights.append(Insight(
            title="Compare records across sources",
            explanation="Each linked record comes from a different source. Open the originals to compare what each establishes.",
            record_ids=[rows[0].id for rows in found.values()],
        ))
    if domain_comparison:
        insights.append(Insight(
            title="Compare registration and certificate records",
            explanation="RDAP shows registry status and key dates for the registered domain. Certificate logs show the names recorded on certificates.",
            record_ids=[found["rdap"][0].id, found["crtsh"][0].id],
        ))
    if len(found.get("gleif", [])) > 1:
        insights.append(Insight(
            title="One name returned multiple LEIs",
            explanation="Compare the registry identifiers and jurisdictions before treating these records as the same organization.",
            record_ids=[row.id for row in found["gleif"][:4]],
        ))
    dated_filings = [row for row in found.get("edgar", []) if row.filed_on]
    if dated_filings:
        latest = max(dated_filings, key=lambda row: row.filed_on)
        insights.append(Insight(
            title="Latest filing returned",
            explanation=f"{latest.company} filed form {latest.form} on {latest.filed_on.isoformat()}.",
            record_ids=[latest.id],
        ))
    if found.get("ofac"):
        insights.append(Insight(
            title="Review the screening candidates",
            explanation="The imported SDN snapshot returned exact primary-name candidates. Confirm the organization's identity using the original entry and independent evidence.",
            record_ids=[row.id for row in found["ofac"][:4]],
        ))
    headlines: dict[tuple[str, ...], list[NewsRecord]] = defaultdict(list)
    for row in found.get("gdelt", []):
        key = headline_key(row.title)
        if len(key) >= 4:
            headlines[key].append(row)
    repeated = sorted(headlines.values(), key=lambda group: len({row.publisher_domain for row in group}), reverse=True)
    for group in repeated[:2]:
        by_publisher = {row.publisher_domain: row for row in group}
        if len(by_publisher) > 1:
            insights.append(Insight(
                title="The same headline appears on multiple domains",
                explanation="Check the bylines and original reporting before counting these records as independent coverage.",
                record_ids=[row.id for row in list(by_publisher.values())[:4]],
            ))
    return insights


def headline_key(title: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\w+", title.casefold()))


@router.post("/workbench", response_model=WorkbenchResults)
async def workbench(data: WorkbenchInput, workspace_id: Workspace):
    return await run_query(data, workspace_id)


async def run_query(data: WorkbenchInput, workspace_id: str):
    query = " ".join(data.query.split())
    intent, queries = plan(query, data.intent)
    initial = await asyncio.gather(*(fetch(workspace_id, source, value) for source, value in queries.items()))
    batches = {batch.outcome.id: batch for batch in initial}
    if intent == "organization" and len(queries) <= 2:
        if "edgar" in batches and batches["edgar"].records:
            name = batches["edgar"].records[0].record.company
            followups = {"gleif": name, "ofac": name}
        elif len(queries) == 1 and batches["gleif"].records:
            name = batches["gleif"].records[0].record.title
            followups = {"gdelt": name, "ofac": name}
        else:
            followups = {}
        more = await asyncio.gather(*(fetch(workspace_id, source, value) for source, value in followups.items()))
        batches.update((batch.outcome.id, batch) for batch in more)
    groups = [batch.records for batch in batches.values()]
    records = [group[index] for index in range(MAX_PER_SOURCE) for group in groups if index < len(group)]
    sources = [
        batches[key].outcome if key in batches else SourceOutcome(id=key, name=name, status="not_applicable")
        for key, name in SOURCES.items()
    ]
    return WorkbenchResults(query=query, intent=intent, sources=sources, insights=derive_insights(batches), records=records)
