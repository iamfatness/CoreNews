"""Persist bounded workbench runs and compare successful source observations."""

import json
from uuid import uuid4

from sqlalchemy import and_, case, func, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from . import evidence_store as store
from .config import settings
from .routers.research import record_json
from .routers.workbench import WorkbenchResults, headline_key
from .watch_store import db, epoch

saved = store.investigations
runs = store.investigation_runs
seen = store.investigation_seen
changes = store.investigation_changes
LEASE_SECONDS = 120
PROVENANCE_ONLY = {
    "ofac_candidate": {"id", "snapshot_id", "published_on"},
    "news_article": {"seen_at"},
    "cisa_advisory": {"catalog_version"},
    "earthquake": {"source_updated_at"},
    "legal_entity": {"updated_at"},
}


def scope(workspace_id: str, case_id: str):
    return and_(saved.c.workspace_id == workspace_id, saved.c.case_id == case_id)


def all_saved(workspace_id: str, case_id: str):
    with db().connect() as conn:
        return conn.execute(select(saved).where(scope(workspace_id, case_id)).order_by(
            saved.c.created_at.desc(), saved.c.id,
        )).mappings().all()


def get_saved(workspace_id: str, case_id: str, investigation_id: str):
    with db().connect() as conn:
        return conn.execute(select(saved).where(
            scope(workspace_id, case_id), saved.c.id == investigation_id,
        )).mappings().one_or_none()


def create(workspace_id: str, case_id: str, query: str, intent: str):
    row = {
        "id": str(uuid4()), "workspace_id": workspace_id, "case_id": case_id, "query": query,
        "intent": intent, "created_at": epoch(), "baselines_json": "[]",
        "interval_minutes": None, "next_run": None,
    }
    try:
        with db().begin() as conn:
            conn.execute(insert(saved).values(**row))
    except IntegrityError:
        with db().connect() as conn:
            existing = conn.execute(select(saved).where(
                scope(workspace_id, case_id), saved.c.query == query, saved.c.intent == intent,
            )).mappings().one_or_none()
        if existing is None:
            raise
        return existing
    return row


def schedule(workspace_id: str, case_id: str, investigation_id: str, minutes: int | None):
    with db().begin() as conn:
        return conn.execute(update(saved).where(
            scope(workspace_id, case_id), saved.c.id == investigation_id,
        ).values(interval_minutes=minutes, next_run=epoch() + minutes * 60 if minutes else None)
         .returning(saved)).mappings().one_or_none()


def _claim(conn, now: int, *conditions):
    eligible = or_(saved.c.lease_until.is_(None), saved.c.lease_until <= now)
    identifier = conn.execute(select(saved.c.id).where(eligible, *conditions)
                              .order_by(saved.c.next_run, saved.c.id).limit(1)).scalar_one_or_none()
    if identifier is None:
        return None
    return conn.execute(update(saved).where(saved.c.id == identifier, eligible, *conditions).values(
        lease_id=str(uuid4()), lease_until=now + LEASE_SECONDS,
    ).returning(saved)).mappings().one_or_none()


def claim_manual(workspace_id: str, case_id: str, investigation_id: str):
    with db().begin() as conn:
        return _claim(conn, epoch(), scope(workspace_id, case_id), saved.c.id == investigation_id)


def claim_due(now: int):
    with db().begin() as conn:
        return _claim(conn, now, saved.c.interval_minutes.is_not(None), saved.c.next_run <= now)


def material_fields(record):
    fields = record.model_dump(mode="json")
    volatile = {"collected_at"} | PROVENANCE_ONLY.get(record.record_type, set())
    for key in ("names", "statuses", "programs"):
        if isinstance(fields.get(key), list):
            fields[key] = sorted(fields[key])
    return {k: v for k, v in fields.items() if k not in volatile}


def fingerprint(record):
    return store.digest(json.dumps(material_fields(record), sort_keys=True))


def _observe(conn, investigation_id: str, source_scope: str, records, baseline: bool) -> list[dict]:
    predicate = (seen.c.investigation_id == investigation_id, seen.c.scope == source_scope)
    incoming = {
        record.list_uid if record.record_type == "ofac_candidate" else record.id: record for record in records
    }
    if not incoming:
        return []
    previous = {row["identity"]: row for row in conn.execute(select(seen).where(
        *predicate, seen.c.identity.in_(incoming),
    )).mappings()}
    events = []
    for identity, record in incoming.items():
        old = previous.get(identity)
        digest = fingerprint(record)
        if old and old["fingerprint"] == digest:
            continue
        payload = record.model_dump_json()
        if old:
            conn.execute(update(seen).where(*predicate, seen.c.identity == identity)
                         .values(fingerprint=digest, record_json=payload))
        else:
            conn.execute(insert(seen).values(investigation_id=investigation_id, scope=source_scope, identity=identity,
                                             fingerprint=digest, record_json=payload))
        if not baseline:
            events.append({
                "id": str(uuid4()), "kind": "updated" if old else "new",
                "previous_json": old["record_json"] if old else None, "record_json": payload, "reviewed": False,
            })
    return events


def finish(claim, started_at: int, now: int, result: WorkbenchResults | None, error: str | None = None):
    investigation_id = claim["id"]
    interval = saved.c.interval_minutes * 60
    retry = case((interval > 900, 900), else_=interval)
    unavailable = result is not None and any(item.status == "unavailable" for item in result.sources)
    answered = result is not None and any(item.status in {"results", "no_match"} for item in result.sources)
    needs_retry = error or (unavailable and not answered)
    with db().begin() as conn:
        held = conn.execute(update(saved).where(
            saved.c.id == investigation_id, saved.c.lease_id == claim["lease_id"], saved.c.lease_until > now,
        ).values(lease_id=None, lease_until=None, next_run=now + (retry if needs_retry else interval))
         .returning(saved.c.baselines_json)).scalar_one_or_none()
        if held is None:
            return None
        baselines = set(json.loads(held))
        rows, events, sources = [], [], []
        if result:
            for source in result.sources:
                item = source.model_dump(mode="json")
                retained = source.name in settings.research_investigation_sources
                item.update(retained=retained, baseline=False)
                sources.append(item)
                if not retained or source.status not in {"results", "no_match"}:
                    continue
                eligible = [entry.record for entry in result.records if entry.record.source == source.name]
                source_scope = store.digest(json.dumps([source.id, source.query]))
                item["baseline"] = source_scope not in baselines
                rows.extend(record.model_dump(mode="json") for record in eligible)
                events.extend(_observe(conn, investigation_id, source_scope, eligible, item["baseline"]))
                baselines.add(source_scope)
        conn.execute(update(saved).where(saved.c.id == investigation_id).values(baselines_json=json.dumps(sorted(baselines))))
        sequence = conn.execute(select(func.coalesce(func.max(runs.c.sequence), 0)).where(
            runs.c.investigation_id == investigation_id,
        )).scalar_one() + 1
        retained_ids = {record["id"] for record in rows}
        insights = [
            insight.model_dump(mode="json") for insight in result.insights
            if set(insight.record_ids).issubset(retained_ids)
        ] if result else []
        row = {
            "id": str(uuid4()), "investigation_id": investigation_id, "started_at": started_at, "finished_at": now,
            "sequence": sequence, "source_json": json.dumps(sources), "result_json": json.dumps(rows),
            "insights_json": json.dumps(insights),
            "change_count": len(events), "error": error,
        }
        conn.execute(insert(runs).values(**row))
        if events:
            conn.execute(insert(changes), [{**event, "run_id": row["id"]} for event in events])
        return row


def run_history(investigation_id: str, before: str | None, limit: int = 20):
    predicate = runs.c.investigation_id == investigation_id
    pending = select(func.count()).where(changes.c.run_id == runs.c.id, changes.c.reviewed.is_(False))
    columns = (runs.c.sequence, runs.c.id, runs.c.started_at, runs.c.finished_at, runs.c.change_count, runs.c.error,
               pending.scalar_subquery().label("pending_count"))
    query = select(*columns).where(predicate)
    with db().connect() as conn:
        if before:
            cursor = conn.execute(select(runs.c.sequence).where(predicate, runs.c.id == before)).scalar_one_or_none()
            if cursor is None:
                return [], None
            query = query.where(runs.c.sequence < cursor)
        rows = conn.execute(query.order_by(runs.c.sequence.desc()).limit(limit + 1)).mappings().all()
        return rows[:limit], rows[limit - 1]["id"] if len(rows) > limit else None


def pending_count(investigation_id: str) -> int:
    with db().connect() as conn:
        return conn.execute(select(func.count()).select_from(changes).where(
            _change_scope(investigation_id), changes.c.reviewed.is_(False),
        )).scalar_one()


def get_run(investigation_id: str, run_id: str):
    with db().connect() as conn:
        return conn.execute(select(runs).where(
            runs.c.investigation_id == investigation_id, runs.c.id == run_id,
        )).mappings().one_or_none()


def change_group(record):
    if record.record_type == "news_article":
        words = headline_key(record.title)
        if len(words) >= 4:
            return store.digest(" ".join(words))
    return None


def _change_scope(investigation_id: str):
    return changes.c.run_id.in_(select(runs.c.id).where(runs.c.investigation_id == investigation_id))


def run_changes(investigation_id: str, run_id: str):
    with db().connect() as conn:
        return conn.execute(select(changes).where(_change_scope(investigation_id), changes.c.run_id == run_id)
                            .order_by(changes.c.reviewed, changes.c.id)).mappings().all()


def review(investigation_id: str, change_id: str):
    with db().begin() as conn:
        return conn.execute(update(changes).where(
            _change_scope(investigation_id), changes.c.id == change_id,
        ).values(reviewed=True).returning(changes)).mappings().one_or_none()


def promote(investigation, change_id: str, body: str):
    with db().begin() as conn:
        # Mutating the review row first serializes competing promotion requests.
        row = conn.execute(update(changes).where(
            _change_scope(investigation["id"]), changes.c.id == change_id,
        ).values(reviewed=True).returning(changes)).mappings().one_or_none()
        if row is None:
            return None
        if row["finding_id"]:
            return conn.execute(select(store.findings).where(store.findings.c.id == row["finding_id"])).mappings().one()
        workspace_id, case_id = investigation["workspace_id"], investigation["case_id"]
        evidence_ids = []
        for payload in (row["previous_json"], row["record_json"]):
            if payload is None:
                continue
            record = record_json.validate_json(payload)
            # Include the original published identifier and park materially different versions separately.
            key = "revision:" + store.digest(record.id + ":" + fingerprint(record))
            item = store.capture_record(
                conn, workspace_id, case_id, key, payload, record.source in settings.research_snapshot_sources,
            )
            evidence_ids.append(item["id"])
        finding = store.insert_finding(conn, workspace_id, case_id, "finding", body, evidence_ids)
        conn.execute(update(changes).where(changes.c.id == change_id).values(finding_id=finding["id"]))
        return finding
