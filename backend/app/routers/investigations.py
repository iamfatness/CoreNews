"""Case-scoped saved workbench queries, histories, and change review."""

import json
import logging
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from starlette.concurrency import run_in_threadpool

from .. import investigation_store as history
from ..config import settings
from . import workbench
from .case_reports import FindingDetail, describe_finding
from .research import Record, Workspace, record_json, require_case

router = APIRouter(prefix="/api/research/cases/{case_id}/investigations", tags=["saved investigations"])
log = logging.getLogger(__name__)


class Investigation(BaseModel):
    id: UUID
    query: str
    intent: workbench.Intent
    created_at: int
    interval_minutes: int | None
    next_run: int | None


class InvestigationList(BaseModel):
    investigations: list[Investigation]
    scheduling_enabled: bool
    retained_sources: list[str]


class Schedule(BaseModel):
    interval_minutes: Annotated[int, Field(ge=60, le=10080)] | None


class RunSummary(BaseModel):
    id: UUID
    sequence: int
    started_at: int
    finished_at: int
    change_count: int
    pending_count: int = 0
    error: str | None


class RunPage(BaseModel):
    runs: list[RunSummary]
    next_before: UUID | None
    pending_count: int


class RetainedSource(workbench.SourceOutcome):
    retained: bool
    baseline: bool


class Change(BaseModel):
    id: UUID
    kind: Literal["new", "updated"]
    reviewed: bool
    finding_id: UUID | None
    group_key: str | None
    changed_fields: list[str]
    record: Record
    previous: Record | None


class RunDetail(RunSummary):
    sources: list[RetainedSource]
    records: list[Record]
    insights: list[workbench.Insight]
    changes: list[Change]


class FindingInput(BaseModel):
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


def authorized(workspace_id: str, case_id: UUID, investigation_id: UUID):
    row = history.get_saved(workspace_id, str(case_id), str(investigation_id))
    if row is None:
        raise HTTPException(404, "Saved investigation not found.")
    return row


def describe_change(row) -> Change:
    record = record_json.validate_json(row["record_json"])
    previous = record_json.validate_json(row["previous_json"]) if row["previous_json"] else None
    affected = []
    if previous:
        before, after = history.material_fields(previous), history.material_fields(record)
        affected = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    return Change(**row, record=record, previous=previous, group_key=history.change_group(record), changed_fields=affected)


async def run_investigation(claim):
    start = history.epoch()
    error = None
    result = None
    try:
        result = await workbench.run_query(
            workbench.WorkbenchInput(query=claim["query"], intent=claim["intent"]), claim["workspace_id"],
        )
    except Exception:
        log.exception("Saved investigation could not complete")
        error = "The workbench could not finish the run. Try running it again."
    return await run_in_threadpool(history.finish, claim, start, history.epoch(), result, error)


@router.get("", response_model=InvestigationList)
def list_investigations(case_id: UUID, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    return {
        "investigations": history.all_saved(workspace_id, str(case_id)),
        "scheduling_enabled": settings.research_watches_enabled,
        "retained_sources": sorted(settings.research_investigation_sources),
    }


@router.post("", response_model=Investigation, status_code=201)
def save_investigation(case_id: UUID, body: workbench.WorkbenchInput, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    query = " ".join(body.query.split())
    intent, _ = workbench.plan(query, body.intent)
    if intent == "domain":
        # Keep the effective hostname and avoid retaining an unnecessary URL path or parameters.
        query = workbench.query_domain(query)
    return history.create(workspace_id, str(case_id), query, intent)


@router.put("/{investigation_id}/schedule", response_model=Investigation)
def update_schedule(case_id: UUID, investigation_id: UUID, body: Schedule, workspace_id: Workspace):
    target = authorized(workspace_id, case_id, investigation_id)
    if body.interval_minutes is not None and not settings.research_watches_enabled:
        raise HTTPException(503, "Scheduled runs require an enabled research watch worker.")
    return history.schedule(workspace_id, str(case_id), target["id"], body.interval_minutes)


@router.get("/{investigation_id}/runs", response_model=RunPage)
def list_runs(case_id: UUID, investigation_id: UUID, workspace_id: Workspace, before: UUID | None = None):
    target = authorized(workspace_id, case_id, investigation_id)
    rows, next_before = history.run_history(target["id"], str(before) if before else None)
    return {"runs": rows, "next_before": next_before, "pending_count": history.pending_count(target["id"])}


@router.post("/{investigation_id}/runs", response_model=RunSummary, status_code=201)
async def run_now(case_id: UUID, investigation_id: UUID, workspace_id: Workspace):
    target = await run_in_threadpool(authorized, workspace_id, case_id, investigation_id)
    claim = await run_in_threadpool(history.claim_manual, workspace_id, str(case_id), target["id"])
    if claim is None:
        raise HTTPException(409, "This investigation already has a run in progress.")
    completed = await run_investigation(claim)
    if completed is None:
        raise HTTPException(409, "The run expired before saving. Refresh history and try again.")
    return {**completed, "pending_count": completed["change_count"]}


@router.get("/{investigation_id}/runs/{run_id}", response_model=RunDetail)
def show_run(case_id: UUID, investigation_id: UUID, run_id: UUID, workspace_id: Workspace):
    target = authorized(workspace_id, case_id, investigation_id)
    row = history.get_run(target["id"], str(run_id))
    if row is None:
        raise HTTPException(404, "Investigation run not found.")
    changes = [describe_change(item) for item in history.run_changes(target["id"], str(run_id))]
    return {
        **row, "sources": json.loads(row["source_json"]), "records": json.loads(row["result_json"]),
        "insights": json.loads(row["insights_json"]),
        "changes": changes, "pending_count": sum(not change.reviewed for change in changes),
    }


@router.put("/{investigation_id}/changes/{change_id}/review", response_model=Change)
def review_change(case_id: UUID, investigation_id: UUID, change_id: UUID, workspace_id: Workspace):
    target = authorized(workspace_id, case_id, investigation_id)
    row = history.review(target["id"], str(change_id))
    if row is None:
        raise HTTPException(404, "Investigation change not found.")
    return describe_change(row)


@router.put("/{investigation_id}/changes/{change_id}/finding", response_model=FindingDetail)
def create_finding(case_id: UUID, investigation_id: UUID, change_id: UUID, body: FindingInput, workspace_id: Workspace):
    target = authorized(workspace_id, case_id, investigation_id)
    finding = history.promote(target, str(change_id), body.body)
    if finding is None:
        raise HTTPException(404, "Investigation change not found.")
    return describe_finding(finding)
