from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StringConstraints, ValidationError

from .. import evidence_store as store
from .. import ofac_catalog
from ..workspace_access import issue_proof
from .research import RecordSelection, Workspace, record_json

router = APIRouter(prefix="/api/research", tags=["organization screening"])
Decision = Literal["same_organization", "different_organization", "inconclusive"]


class LookupInput(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=350)]
    snapshot_id: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")] | None = None


class Snapshot(BaseModel):
    id: str
    published_on: str
    imported_at: str
    entity_count: int


class CandidateResults(BaseModel):
    scope: Literal["exact_organization_name"] = "exact_organization_name"
    snapshot: Snapshot
    records: list[RecordSelection]


class ReviewInput(BaseModel):
    decision: Decision
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    version: int = Field(ge=0, le=2147483646)


class ScreeningReview(ReviewInput):
    evidence_id: UUID
    updated_at: str


@router.post("/screening/ofac", response_model=CandidateResults)
def lookup_organization(body: LookupInput, workspace_id: Workspace):
    snapshot, records = ofac_catalog.lookup(body.name, body.snapshot_id)
    if snapshot is None:
        raise HTTPException(404 if body.snapshot_id else 503,
                            "The requested SDN snapshot is not imported." if body.snapshot_id
                            else "An operator needs to import an OFAC SDN.XML snapshot.")
    return CandidateResults(snapshot=Snapshot(**snapshot), records=[
        RecordSelection(record=record, proof=issue_proof(workspace_id, record)) for record in records
    ])


def require_saved_candidate(workspace_id: str, case_id: UUID, evidence_id: UUID):
    row = store.get_evidence(workspace_id, str(case_id), str(evidence_id))
    if row is None:
        raise HTTPException(404, "Screening evidence was not found in this case.")
    try:
        record = record_json.validate_json(row["record_json"])
    except ValidationError:
        raise HTTPException(409, "The saved evidence metadata is unavailable.") from None
    if not isinstance(record, ofac_catalog.ScreeningCandidate):
        raise HTTPException(422, "Choose a saved OFAC screening candidate.")
    if store.snapshot_state(row) == "mismatch":
        raise HTTPException(409, "The saved evidence hash has changed. Verify the original before review.")


@router.get("/cases/{case_id}/evidence/{evidence_id}/screening-review", response_model=ScreeningReview | None)
def get_review(case_id: UUID, evidence_id: UUID, workspace_id: Workspace):
    require_saved_candidate(workspace_id, case_id, evidence_id)
    return store.get_screening_review(workspace_id, str(case_id), str(evidence_id))


@router.put("/cases/{case_id}/evidence/{evidence_id}/screening-review", response_model=ScreeningReview)
def save_review(case_id: UUID, evidence_id: UUID, data: ReviewInput, workspace_id: Workspace):
    require_saved_candidate(workspace_id, case_id, evidence_id)
    row = store.save_screening_review(workspace_id, str(case_id), str(evidence_id),
                                     data.decision, data.rationale, data.version)
    if row is None:
        raise HTTPException(409, "This review changed. Reopen it before editing again.")
    return row
