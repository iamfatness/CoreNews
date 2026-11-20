from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StringConstraints

from .. import evidence_store as store
from .. import watch_store as watches
from ..config import settings
from ..connectors.edgar import normalize_filer
from ..connectors.gdelt import news_query
from .research import CaseEvidence, Record, Workspace, evidence_detail, record_json, require_case

router = APIRouter(prefix="/api/research/cases", tags=["case watches"])
Source = Literal["edgar", "gdelt"]


class WatchInput(BaseModel):
    source: Source
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=253)]
    interval_minutes: Annotated[int, Field(ge=60, le=10080)] = 1440


class WatchDetail(WatchInput):
    id: str
    paused: bool
    next_run: int
    last_success: int | None
    last_error: str | None


class PauseInput(BaseModel):
    paused: bool


class AlertDetail(BaseModel):
    id: str
    source: Source
    query: str
    observed_at: int
    reviewed: bool
    record: Record


class MonitoringDetail(BaseModel):
    enabled: bool
    sources: list[Source]
    watches: list[WatchDetail]
    alerts: list[AlertDetail]


def enabled_sources() -> list[Source]:
    return [source for source, configured in (
        ("edgar", bool(settings.edgar_user_agent)), ("gdelt", settings.gdelt_enabled),
    ) if configured]


@router.get("/{case_id}/monitoring", response_model=MonitoringDetail)
def monitoring(case_id: UUID, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    key = str(case_id)
    return {
        "enabled": settings.research_watches_enabled, "sources": enabled_sources(),
        "watches": watches.list_watches(workspace_id, key),
        "alerts": [
            {**row, "record": record_json.validate_json(row["record_json"])}
            for row in watches.list_alerts(workspace_id, key)
        ],
    }


@router.post("/{case_id}/watches", response_model=WatchDetail, status_code=201)
def add_watch(case_id: UUID, body: WatchInput, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    if not settings.research_watches_enabled or body.source not in enabled_sources():
        raise HTTPException(503, "Scheduled checks for that source are disabled on this deployment.")
    try:
        query = normalize_filer(body.query) if body.source == "edgar" else news_query(body.query).casefold()
        if body.source == "edgar" and not query.isdigit():
            raise ValueError("Use the company’s SEC CIK to keep the watch pinned to the same filer.")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return watches.create_watch(workspace_id, str(case_id), body.source, query, body.interval_minutes)


@router.patch("/{case_id}/watches/{watch_id}", response_model=WatchDetail)
def pause_watch(case_id: UUID, watch_id: UUID, body: PauseInput, workspace_id: Workspace):
    require_case(workspace_id, case_id)
    if not body.paused and not settings.research_watches_enabled:
        raise HTTPException(503, "Scheduled checks are disabled on this deployment.")
    result = watches.set_paused(workspace_id, str(case_id), str(watch_id), body.paused)
    if result is None:
        raise HTTPException(404, "Watch not found.")
    return result


@router.put("/{case_id}/alerts/{alert_id}/review")
def mark_reviewed(case_id: UUID, alert_id: UUID, workspace_id: Workspace):
    if watches.review_alert(workspace_id, str(case_id), str(alert_id)) is None:
        raise HTTPException(404, "Alert not found.")
    return {"reviewed": True}


@router.put("/{case_id}/alerts/{alert_id}/evidence", response_model=CaseEvidence)
def save_alert(case_id: UUID, alert_id: UUID, workspace_id: Workspace):
    row = watches.get_alert(workspace_id, str(case_id), str(alert_id))
    if row is None:
        raise HTTPException(404, "Alert not found.")
    record = record_json.validate_json(row["record_json"])
    saved = store.save_record(
        workspace_id, str(case_id), record.id, record.model_dump_json(),
        record.source in settings.research_snapshot_sources,
    )
    return evidence_detail(saved)
