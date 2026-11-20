from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StringConstraints

from .. import ofac_catalog
from ..workspace_access import issue_proof
from .research import RecordSelection, Workspace

router = APIRouter(prefix="/api/research/screening", tags=["organization screening"])


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


@router.post("/ofac", response_model=CandidateResults)
def lookup_organization(body: LookupInput, workspace_id: Workspace):
    snapshot, records = ofac_catalog.lookup(body.name, body.snapshot_id)
    if snapshot is None:
        raise HTTPException(404 if body.snapshot_id else 503,
                            "The requested SDN snapshot is not imported." if body.snapshot_id
                            else "An operator needs to import an OFAC SDN.XML snapshot.")
    return CandidateResults(snapshot=Snapshot(**snapshot), records=[
        RecordSelection(record=record, proof=issue_proof(workspace_id, record)) for record in records
    ])
