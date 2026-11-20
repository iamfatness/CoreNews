from typing import Annotated, Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints, TypeAdapter

from .. import evidence_store as store
from ..config import settings
from ..connectors.edgar import EdgarConnector, FilingRecord, UnknownFiler, normalize_filer
from ..records import CertificateRecord
from ..workspace_access import issue_proof, valid_proof, workspace
from .search import lookup_certificates

router = APIRouter(prefix="/api/research", tags=["research"])
edgar = EdgarConnector()
Workspace = Annotated[str, Depends(workspace)]
Record = Annotated[CertificateRecord | FilingRecord, Field(discriminator="record_type")]
record_json = TypeAdapter(Record)


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


@router.get("/search", response_model=SearchEnvelope)
async def search(
    workspace_id: Workspace, source: Literal["crtsh", "edgar"],
    q: Annotated[str, Query(min_length=1, max_length=253)],
):
    result = await (lookup_filings(q) if source == "edgar" else lookup_certificates(q))
    return SearchEnvelope(
        query=result.query, source=result.source, total=result.total,
        records=[RecordSelection(record=row, proof=issue_proof(workspace_id, row)) for row in result.records],
    )


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
    expected = row["snapshot_sha256"]
    if expected is None:
        return {"status": "not_captured"}
    if store.digest(row["record_json"]) != expected:
        return {"status": "mismatch"}
    return {"status": "verified", "sha256": expected}
