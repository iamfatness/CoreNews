"""Workspace-scoped case findings and a portable report snapshot."""

import json
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StringConstraints, ValidationError, computed_field

from .. import evidence_store as store
from ..research_entities import observation_time
from .research import CaseSummary, Workspace, record_json, require_case

router = APIRouter(prefix="/api/research/cases", tags=["case reports"])
Kind = Literal["finding", "question"]
Verification = Literal["verified", "not_captured", "mismatch"]


class FindingInput(BaseModel):
    kind: Kind
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    evidence_ids: list[UUID] = Field(default_factory=list, max_length=25)


class FindingUpdate(FindingInput):
    version: int = Field(ge=1, le=2147483646)


class FindingDetail(BaseModel):
    id: str
    kind: Kind
    body: str
    evidence_ids: list[str]
    version: int
    created_at: str
    updated_at: str

    @computed_field
    @property
    def uncited(self) -> bool:
        return self.kind == "finding" and not self.evidence_ids


class ReportEvidence(BaseModel):
    id: str
    label: str
    title: str
    source: str | None = None
    source_url: str | None = None
    source_date: str | None = None
    date_label: str | None = None
    collected_at: str | None = None
    saved_at: str
    snapshot_sha256: str | None
    verification: Verification
    metadata_available: bool


class CaseReport(BaseModel):
    schema_version: Literal[1] = 1
    case: CaseSummary
    exported_at: str
    findings: list[FindingDetail]
    evidence: list[ReportEvidence]
    uncited_findings: int


def describe_finding(row) -> FindingDetail:
    return FindingDetail(**{**row, "evidence_ids": json.loads(row["evidence_ids"])})


def checked_citations(data: FindingInput, workspace_id: str, case_id: str) -> list[str]:
    evidence_ids = list(dict.fromkeys(str(identifier) for identifier in data.evidence_ids))
    if not store.citations_belong_to_case(workspace_id, case_id, evidence_ids):
        raise HTTPException(422, "Citations must refer to evidence saved in this case.")
    return evidence_ids


def report_source(row, number: int) -> ReportEvidence:
    common = {
        "id": row["id"], "label": f"E{number}", "saved_at": row["saved_at"],
        "snapshot_sha256": row["snapshot_sha256"], "verification": store.snapshot_state(row),
    }
    try:
        record = record_json.validate_json(row["record_json"])
    except ValidationError:
        return ReportEvidence(**common, title="Saved record metadata unavailable", metadata_available=False)
    observed, label = observation_time(record)
    return ReportEvidence(
        **common, title=record.title, source=record.source, source_url=record.source_url,
        source_date=observed, date_label=label, collected_at=record.collected_at.isoformat(),
        metadata_available=True,
    )


@router.post("/{case_id}/findings", response_model=FindingDetail, status_code=201)
def add_finding(case_id: UUID, data: FindingInput, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    case_key = str(case_id)
    refs = checked_citations(data, workspace_id, case_key)
    return describe_finding(store.create_finding(workspace_id, case_key, data.kind, data.body, refs))


@router.put("/{case_id}/findings/{finding_id}", response_model=FindingDetail)
def revise_finding(case_id: UUID, finding_id: UUID, data: FindingUpdate, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    case_key, finding_key = str(case_id), str(finding_id)
    if store.find_finding(workspace_id, case_key, finding_key) is None:
        raise HTTPException(404, "Finding not found.")
    refs = checked_citations(data, workspace_id, case_key)
    row = store.update_finding(workspace_id, case_key, finding_key, data.version, data.kind, data.body, refs)
    if row is None:
        raise HTTPException(409, "This entry changed. Reload the report before editing again.")
    return describe_finding(row)


@router.get("/{case_id}/report", response_model=CaseReport)
def read_report(case_id: UUID, workspace_id: Workspace):
    case = require_case(workspace_id, case_id)
    case_key = str(case_id)
    findings = [describe_finding(row) for row in store.case_finding_rows(workspace_id, case_key)]
    evidence = [
        report_source(row, number)
        for number, row in enumerate(store.case_evidence(workspace_id, case_key), start=1)
    ]
    return CaseReport(
        case=CaseSummary(**case), exported_at=store.now(), findings=findings, evidence=evidence,
        uncited_findings=sum(item.uncited for item in findings),
    )
