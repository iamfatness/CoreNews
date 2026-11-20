from time import time
from uuid import uuid4

from sqlalchemy import and_, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from . import evidence_store as store
from .config import settings
from .records import ResearchRecord

watches = store.watches
observations = store.watch_observations
LEASE_SECONDS = 120


def epoch() -> int:
    return int(time())


def db():
    return store.database(settings.database_url)


def scope(workspace: str, case: str):
    return and_(watches.c.workspace_id == workspace, watches.c.case_id == case)


def list_watches(workspace: str, case: str):
    with db().connect() as conn:
        return conn.execute(select(watches).where(scope(workspace, case))
                            .order_by(watches.c.next_run, watches.c.id)).mappings().all()


def create_watch(workspace: str, case: str, source: str, query: str, interval: int):
    row = {
        "id": str(uuid4()), "workspace_id": workspace, "case_id": case,
        "source": source, "query": query, "interval_minutes": interval, "paused": False,
        "next_run": epoch(), "last_error": None, "last_success": None,
    }
    try:
        with db().begin() as conn:
            conn.execute(insert(watches).values(**row))
    except IntegrityError:
        with db().connect() as conn:
            existing = conn.execute(select(watches).where(
                scope(workspace, case), watches.c.source == source, watches.c.query == query,
            )).mappings().one_or_none()
        if existing is not None:
            return existing
        raise
    return row


def set_paused(workspace: str, case: str, watch_id: str, paused: bool):
    with db().begin() as conn:
        row = conn.execute(update(watches).where(
            scope(workspace, case), watches.c.id == watch_id, watches.c.paused != paused,
        ).values(paused=paused, lease_id=None, lease_until=None, next_run=epoch())
         .returning(watches)).mappings().one_or_none()
        if row is not None:
            return row
        return conn.execute(select(watches).where(
            scope(workspace, case), watches.c.id == watch_id,
        )).mappings().one_or_none()


def claim_due(now: int):
    eligible = and_(
        watches.c.paused.is_(False), watches.c.next_run <= now,
        or_(watches.c.lease_until.is_(None), watches.c.lease_until <= now),
    )
    with db().begin() as conn:
        # The conditional update rechecks eligibility after competing workers commit.
        candidate = conn.execute(select(watches.c.id).where(eligible)
                                 .order_by(watches.c.next_run, watches.c.id).limit(1)).scalar_one_or_none()
        if candidate is None:
            return None
        return conn.execute(update(watches).where(watches.c.id == candidate, eligible).values(
            lease_id=str(uuid4()), lease_until=now + LEASE_SECONDS,
        ).returning(watches)).mappings().one_or_none()


def finish_check(watch, now: int, records: list[ResearchRecord], error: str | None = None):
    interval = watch["interval_minutes"] * 60
    baseline = watch["last_success"] is None
    with db().begin() as conn:
        held = conn.execute(update(watches).where(
            watches.c.id == watch["id"], watches.c.lease_id == watch["lease_id"],
            watches.c.lease_until > now, watches.c.paused.is_(False),
        ).values(
            lease_id=None, lease_until=None, next_run=now + (min(interval, 900) if error else interval),
            last_success=watch["last_success"] if error else now, last_error=error,
        ).returning(watches.c.id)).scalar_one_or_none()
        if held is None or error or not records:
            return

        incoming = {record.id: record for record in records}
        seen = set(conn.execute(select(observations.c.record_id).where(
            observations.c.watch_id == held, observations.c.record_id.in_(incoming),
        )).scalars())
        rows = [{
            "id": str(uuid4()), "watch_id": held, "record_id": record.id,
            "record_json": None if baseline else record.model_dump_json(),
            "observed_at": now, "reviewed": False,
        } for key, record in incoming.items() if key not in seen]
        if rows:
            conn.execute(insert(observations), rows)


def _alerts(workspace: str, case: str):
    return select(observations, watches.c.source, watches.c.query).select_from(
        observations.join(watches, watches.c.id == observations.c.watch_id),
    ).where(scope(workspace, case), observations.c.record_json.is_not(None))


def list_alerts(workspace: str, case: str):
    with db().connect() as conn:
        return conn.execute(_alerts(workspace, case).order_by(
            observations.c.observed_at.desc(), observations.c.id,
        ).limit(100)).mappings().all()


def get_alert(workspace: str, case: str, alert_id: str):
    with db().connect() as conn:
        return conn.execute(_alerts(workspace, case).where(observations.c.id == alert_id)).mappings().one_or_none()


def review_alert(workspace: str, case: str, alert_id: str):
    with db().begin() as conn:
        allowed_watch = select(watches.c.id).where(scope(workspace, case))
        return conn.execute(update(observations).where(
            observations.c.id == alert_id, observations.c.watch_id.in_(allowed_watch),
            observations.c.record_json.is_not(None),
        ).values(reviewed=True).returning(observations.c.id)).scalar_one_or_none()
