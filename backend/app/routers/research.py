import asyncio
from typing import Annotated, Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints, TypeAdapter, ValidationError

from .. import evidence_store as store
from ..config import settings
from ..connectors.cisa_kev import CATALOG, AdvisoryRecord, CisaKevConnector, normalize_cve
from ..connectors.edgar import EdgarConnector, FilingRecord, UnknownFiler, normalize_filer
from ..connectors.gdelt import GdeltConnector, NewsRecord, news_query
from ..connectors.usgs import EarthquakeRecord
from ..ofac_catalog import ScreeningCandidate
from ..records import CertificateRecord, normalize_domain
from ..research_entities import EntityKind, entity_matches, observation_time
from ..workspace_access import issue_proof, valid_proof, workspace
from .search import lookup_certificates

router = APIRouter(prefix="/api/research", tags=["research"])
edgar = EdgarConnector()
gdelt = GdeltConnector()
cisa = CisaKevConnector()
Workspace = Annotated[str, Depends(workspace)]
Source = Literal["crtsh", "edgar", "gdelt", "cisa"]
Record = Annotated[
    CertificateRecord | FilingRecord | NewsRecord | EarthquakeRecord | ScreeningCandidate | AdvisoryRecord,
    Field(discriminator="record_type"),
]
record_json = TypeAdapter(Record)
SCAN_LIMIT = 500
SOURCES = {
    "crtsh": ("crt.sh", "Domain", "example.org", "https://crt.sh/"),
    "edgar": ("SEC EDGAR", "Ticker or SEC CIK", "AAPL or 0000320193", "https://www.sec.gov/edgar/search/"),
    "gdelt": ("GDELT", "News topic", "port strike", "https://www.gdeltproject.org/"),
    "cisa": ("CISA KEV", "CVE identifier", "CVE-2024-1234", CATALOG),
}


class CaseInput(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class CaseSummary(BaseModel):
    id: str
    title: str
    created_at: str


class RecordSelection(BaseModel):
    record: Record
    proof: Annotated[str, StringConstraints(max_length=100)]


class CaseEvidence(BaseModel):
    id: str
    saved_at: str
    record: Record
    snapshot_sha256: str | None


class CaseDetail(CaseSummary):
    evidence: list[CaseEvidence]


class SearchEnvelope(BaseModel):
    query: str
    source: str
    total: int
    records: list[RecordSelection]


class DiscoveryInput(BaseModel):
    queries: Annotated[
        dict[Source, Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=253)]],
        Field(min_length=1, max_length=len(SOURCES)),
    ]


class DiscoverySource(BaseModel):
    source_id: Source
    total: int | None = None
    error: str | None = None
    records: list[RecordSelection] = Field(default_factory=list)


class WorkspaceEvidence(CaseEvidence):
    case_id: str
    case_title: str
    observed_at: str
    date_label: str


class EvidenceWindow(BaseModel):
    records: list[WorkspaceEvidence]
    limited: bool
    unreadable: int


def evidence_detail(row) -> CaseEvidence:
    return CaseEvidence(
        id=row["id"], saved_at=row["saved_at"],
        record=record_json.validate_json(row["record_json"]),
        snapshot_sha256=row["snapshot_sha256"],
    )


def require_case(workspace_id: str, case_id: UUID):
    row = store.get_case(workspace_id, str(case_id))
    if row is None:
        raise HTTPException(404, "Case not found.")
    return row


async def lookup_filings(query: str):
    try:
        filer = normalize_filer(query)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not settings.edgar_user_agent:
        raise HTTPException(503, "SEC EDGAR requires a configured requester identity.")
    try:
        return await edgar.search(filer, settings.edgar_user_agent)
    except UnknownFiler as exc:
        raise HTTPException(404, str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(504, "SEC EDGAR timed out. Try again.") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(404, "No SEC filer was found for that CIK.") from exc
        if exc.response.status_code in (403, 429):
            raise HTTPException(503, "SEC EDGAR declined the request. Try again later.") from exc
        raise HTTPException(502, "SEC EDGAR is temporarily unavailable.") from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(502, "SEC EDGAR did not return usable filings. Try again.") from exc


async def lookup_news(query: str):
    if not settings.gdelt_enabled:
        raise HTTPException(503, "GDELT is disabled on this instance.")
    try:
        query = news_query(query)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        return await gdelt.search(query)
    except httpx.TimeoutException as exc:
        raise HTTPException(504, "GDELT timed out. Try again.") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise HTTPException(503, "GDELT is limiting requests. Try again in a moment.") from exc
        raise HTTPException(502, "GDELT is temporarily unavailable.") from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(502, "GDELT did not return usable results.") from exc


async def lookup_advisory(query: str):
    if not settings.cisa_kev_enabled:
        raise HTTPException(503, "CISA KEV is disabled on this instance.")
    try:
        identifier = normalize_cve(query)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        return await cisa.search(identifier)
    except (httpx.TimeoutException, TimeoutError) as exc:
        raise HTTPException(504, "CISA KEV timed out. Try again.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "CISA KEV is temporarily unavailable.") from exc


async def source_search(workspace_id: str, source: Source, query: str) -> SearchEnvelope:
    fetch = {"crtsh": lookup_certificates, "edgar": lookup_filings, "gdelt": lookup_news, "cisa": lookup_advisory}[source]
    result = await fetch(query)
    return SearchEnvelope(
        query=result.query, source=result.source, total=result.total,
        records=[RecordSelection(record=row, proof=issue_proof(workspace_id, row)) for row in result.records],
    )


@router.get("/search", response_model=SearchEnvelope)
async def search(
    workspace_id: Workspace, source: Source,
    q: Annotated[str, Query(min_length=1, max_length=253)],
):
    return await source_search(workspace_id, source, q)


@router.get("/sources")
def list_sources(workspace_id: Workspace):
    enabled = {
        "crtsh": True, "edgar": bool(settings.edgar_user_agent),
        "gdelt": settings.gdelt_enabled, "cisa": settings.cisa_kev_enabled,
    }
    return [
        {"id": key, "name": name, "input_label": label, "example": example,
         "website": website, "enabled": enabled[key]}
        for key, (name, label, example, website) in SOURCES.items()
    ]


@router.post("/discover", response_model=list[DiscoverySource])
async def discover(data: DiscoveryInput, workspace_id: Workspace):
    async def one(source: Source, query: str):
        try:
            result = await source_search(workspace_id, source, query)
            return DiscoverySource(source_id=source, total=result.total, records=result.records)
        except HTTPException as exc:
            return DiscoverySource(source_id=source, error=str(exc.detail))

    return await asyncio.gather(*(one(source, q) for source, q in data.queries.items()))


def scan_evidence(workspace_id: str) -> EvidenceWindow:
    rows = store.recent_evidence(workspace_id, SCAN_LIMIT + 1)
    matched = []
    unreadable = 0
    for row in rows[:SCAN_LIMIT]:
        try:
            item = evidence_detail(row)
        except ValidationError:
            unreadable += 1
            continue
        observed, label = observation_time(item.record)
        matched.append(WorkspaceEvidence(
            **item.model_dump(), case_id=row["case_id"], case_title=row["case_title"],
            observed_at=observed, date_label=label,
        ))
    return EvidenceWindow(records=matched, limited=len(rows) > SCAN_LIMIT, unreadable=unreadable)


@router.get("/evidence", response_model=EvidenceWindow)
def workspace_evidence(workspace_id: Workspace, source: Source | None = None):
    result = scan_evidence(workspace_id)
    if source is not None:
        result.records = [item for item in result.records if item.record.source == SOURCES[source][0]]
    return result


@router.get("/entities/{kind}/{key}", response_model=EvidenceWindow)
def entity_timeline(kind: EntityKind, key: str, workspace_id: Workspace):
    try:
        canonical = normalize_domain(key) if kind == "domain" else normalize_filer(key)
        if kind == "company" and not canonical.isdigit():
            raise ValueError("Company timelines require an SEC CIK.")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    result = scan_evidence(workspace_id)
    result.records = sorted(
        (item for item in result.records if entity_matches(item.record, kind, canonical)),
        key=lambda item: (item.observed_at[:10], item.saved_at, item.id), reverse=True,
    )
    return result


@router.get("/cases", response_model=list[CaseSummary])
def list_cases(workspace_id: Workspace):
    return store.case_rows(workspace_id)


@router.post("/cases", response_model=CaseSummary, status_code=201)
def create_case(data: CaseInput, workspace_id: Workspace):
    return store.create_case(workspace_id, data.title)


@router.get("/cases/{case_id}", response_model=CaseDetail)
def read_case(case_id: UUID, workspace_id: Workspace):
    case = require_case(workspace_id, case_id)
    return {**case, "evidence": [
        evidence_detail(row) for row in store.case_evidence(workspace_id, str(case_id))
    ]}


@router.put("/cases/{case_id}/evidence", response_model=CaseEvidence)
def save_evidence(case_id: UUID, data: RecordSelection, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    record = data.record
    if not valid_proof(workspace_id, record, data.proof):
        raise HTTPException(422, "Search again to obtain a valid record for this workspace.")
    return evidence_detail(store.save_record(
        workspace_id, str(case_id), record.id, record.model_dump_json(),
        record.source in settings.research_snapshot_sources,
    ))


@router.get("/cases/{case_id}/evidence/{evidence_id}/verify")
def verify_evidence(case_id: UUID, evidence_id: UUID, workspace_id: Workspace):
    row = store.get_evidence(workspace_id, str(case_id), str(evidence_id))
    if row is None:
        raise HTTPException(404, "Evidence not found.")
    state = store.snapshot_state(row)
    if state == "verified":
        return {"status": state, "sha256": row["snapshot_sha256"]}
    return {"status": state}
