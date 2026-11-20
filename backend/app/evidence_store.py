import hashlib
import json
from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4

from sqlalchemy import (
    and_,
    BigInteger, Boolean, Column, ForeignKey, ForeignKeyConstraint, Index, Integer, MetaData, String, Table, Text, UniqueConstraint,
    create_engine, insert, select, update,
)
from sqlalchemy.exc import IntegrityError

from .config import settings

metadata = MetaData()
cases = Table(
    "research_cases", metadata,
    Column("workspace_id", String(128), primary_key=True),
    Column("id", String(36), primary_key=True),
    Column("title", String(160), nullable=False),
    Column("created_at", String(32), nullable=False),
)
evidence = Table(
    "research_evidence", metadata,
    Column("id", String(36), primary_key=True),
    Column("workspace_id", String(128), nullable=False),
    Column("case_id", String(36), nullable=False),
    Column("record_id", String(128), nullable=False),
    Column("record_json", Text, nullable=False),
    Column("snapshot_sha256", String(64)),
    Column("saved_at", String(32), nullable=False),
    ForeignKeyConstraint(["workspace_id", "case_id"], [cases.c.workspace_id, cases.c.id]),
    UniqueConstraint("workspace_id", "case_id", "record_id"),
)
findings = Table(
    "research_case_findings", metadata,
    Column("id", String(36), primary_key=True),
    Column("workspace_id", String(128), nullable=False),
    Column("case_id", String(36), nullable=False),
    Column("kind", String(12), nullable=False),
    Column("body", Text, nullable=False),
    Column("evidence_ids", Text, nullable=False),
    Column("version", Integer, nullable=False),
    Column("created_at", String(32), nullable=False),
    Column("updated_at", String(32), nullable=False),
    ForeignKeyConstraint(["workspace_id", "case_id"], [cases.c.workspace_id, cases.c.id]),
)
watches = Table(
    "research_case_watches", metadata,
    Column("id", String(36), primary_key=True),
    Column("workspace_id", String(128), nullable=False),
    Column("case_id", String(36), nullable=False),
    Column("source", String(12), nullable=False),
    Column("query", String(253), nullable=False),
    Column("interval_minutes", Integer, nullable=False),
    Column("paused", Boolean, nullable=False),
    Column("next_run", BigInteger, nullable=False, index=True),
    Column("lease_id", String(36)),
    Column("lease_until", BigInteger),
    Column("last_success", BigInteger),
    Column("last_error", String(400)),
    ForeignKeyConstraint(["workspace_id", "case_id"], [cases.c.workspace_id, cases.c.id]),
    UniqueConstraint("workspace_id", "case_id", "source", "query"),
)
watch_observations = Table(
    "research_watch_observations", metadata,
    Column("id", String(36), primary_key=True),
    Column("watch_id", String(36), ForeignKey(watches.c.id), nullable=False),
    Column("record_id", String(128), nullable=False),
    Column("record_json", Text),
    Column("observed_at", BigInteger, nullable=False),
    Column("reviewed", Boolean, nullable=False),
    UniqueConstraint("watch_id", "record_id"),
)
screening_snapshots = Table(
    "research_screening_snapshots", metadata,
    Column("id", String(64), primary_key=True),
    Column("published_on", String(10), nullable=False),
    Column("imported_at", String(32), nullable=False),
    Column("entity_count", Integer, nullable=False),
)
screening_entries = Table(
    "research_screening_entities", metadata,
    Column("snapshot_id", String(64), ForeignKey(screening_snapshots.c.id), primary_key=True),
    Column("uid", String(24), primary_key=True),
    Column("name", String(350), nullable=False),
    Column("search_name", String(350), nullable=False, index=True),
    Column("programs_json", Text, nullable=False),
)
activity = Table(
    "research_case_activity", metadata,
    Column("id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True),
    Column("entry_key", String(36), nullable=False, unique=True),
    Column("workspace_id", String(128), nullable=False),
    Column("case_id", String(36), nullable=False),
    Column("action", String(24), nullable=False),
    Column("target_id", String(36), nullable=False),
    Column("version", Integer),
    Column("occurred_at", String(32), nullable=False),
    ForeignKeyConstraint(["workspace_id", "case_id"], [cases.c.workspace_id, cases.c.id]),
)
Index("ix_research_case_activity_scope", activity.c.workspace_id, activity.c.case_id, activity.c.id)


@lru_cache(maxsize=1)
def database(url: str):
    return create_engine(url, pool_pre_ping=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record_activity(conn, workspace_id, case_id, action, target_id, occurred_at, version=None):
    conn.execute(insert(activity).values(
        entry_key=str(uuid4()), workspace_id=workspace_id, case_id=case_id, action=action, target_id=target_id,
        occurred_at=occurred_at, version=version,
    ))


def case_activity(workspace_id: str, case_id: str, before: str | None, limit: int):
    scope = (activity.c.workspace_id == workspace_id, activity.c.case_id == case_id)
    query = select(activity).where(*scope)
    if before is not None:
        cursor = select(activity.c.id).where(*scope, activity.c.entry_key == before).scalar_subquery()
        query = query.where(activity.c.id < cursor)
    with database(settings.database_url).connect() as conn:
        return conn.execute(query.order_by(activity.c.id.desc()).limit(limit)).mappings().all()


def create_case(workspace_id: str, title: str):
    values = {"workspace_id": workspace_id, "id": str(uuid4()), "title": title, "created_at": now()}
    with database(settings.database_url).begin() as conn:
        conn.execute(insert(cases).values(**values))
        record_activity(conn, workspace_id, values["id"], "case_created", values["id"], values["created_at"])
    return values


def case_rows(workspace_id: str):
    with database(settings.database_url).connect() as conn:
        return conn.execute(
            select(cases).where(cases.c.workspace_id == workspace_id)
            .order_by(cases.c.created_at.desc(), cases.c.id)
        ).mappings().all()


def get_case(workspace_id: str, case_id: str):
    with database(settings.database_url).connect() as conn:
        return conn.execute(select(cases).where(
            cases.c.workspace_id == workspace_id, cases.c.id == case_id,
        )).mappings().one_or_none()


def case_evidence(workspace_id: str, case_id: str):
    with database(settings.database_url).connect() as conn:
        return conn.execute(select(evidence).where(
            evidence.c.workspace_id == workspace_id, evidence.c.case_id == case_id,
        ).order_by(evidence.c.saved_at, evidence.c.id)).mappings().all()


def recent_evidence(workspace_id: str, limit: int):
    scoped_cases = evidence.join(cases, and_(
        evidence.c.workspace_id == cases.c.workspace_id, evidence.c.case_id == cases.c.id,
    ))
    query = (
        select(evidence, cases.c.title.label("case_title"))
        .select_from(scoped_cases)
        .where(evidence.c.workspace_id == workspace_id)
        .order_by(evidence.c.saved_at.desc(), evidence.c.id.desc())
        .limit(limit)
    )
    with database(settings.database_url).connect() as conn:
        return conn.execute(query).mappings().all()


def get_evidence(workspace_id: str, case_id: str, evidence_id: str):
    with database(settings.database_url).connect() as conn:
        return conn.execute(select(evidence).where(
            evidence.c.workspace_id == workspace_id, evidence.c.case_id == case_id,
            evidence.c.id == evidence_id,
        )).mappings().one_or_none()


def case_finding_rows(workspace_id: str, case_id: str):
    with database(settings.database_url).connect() as conn:
        return conn.execute(select(findings).where(
            findings.c.workspace_id == workspace_id, findings.c.case_id == case_id,
        ).order_by(findings.c.created_at, findings.c.id)).mappings().all()


def find_finding(workspace_id: str, case_id: str, finding_id: str):
    with database(settings.database_url).connect() as conn:
        return conn.execute(select(findings).where(
            findings.c.workspace_id == workspace_id, findings.c.case_id == case_id,
            findings.c.id == finding_id,
        )).mappings().one_or_none()


def citations_belong_to_case(workspace_id: str, case_id: str, evidence_ids: list[str]) -> bool:
    if not evidence_ids:
        return True
    with database(settings.database_url).connect() as conn:
        found = conn.execute(select(evidence.c.id).where(
            evidence.c.workspace_id == workspace_id, evidence.c.case_id == case_id,
            evidence.c.id.in_(evidence_ids),
        )).scalars().all()
    return set(found) == set(evidence_ids)


def create_finding(workspace_id: str, case_id: str, kind: str, body: str, evidence_ids: list[str]):
    timestamp = now()
    values = {
        "id": str(uuid4()), "workspace_id": workspace_id, "case_id": case_id,
        "kind": kind, "body": body, "evidence_ids": json.dumps(evidence_ids),
        "version": 1, "created_at": timestamp, "updated_at": timestamp,
    }
    with database(settings.database_url).begin() as conn:
        conn.execute(insert(findings).values(**values))
        record_activity(conn, workspace_id, case_id, "finding_added", values["id"], timestamp, version=1)
    return values


def update_finding(workspace_id: str, case_id: str, finding_id: str, version: int,
                   kind: str, body: str, evidence_ids: list[str]):
    timestamp = now()
    with database(settings.database_url).begin() as conn:
        row = conn.execute(update(findings).where(
            findings.c.workspace_id == workspace_id, findings.c.case_id == case_id,
            findings.c.id == finding_id, findings.c.version == version,
        ).values(
            kind=kind, body=body, evidence_ids=json.dumps(evidence_ids),
            version=version + 1, updated_at=timestamp,
        ).returning(findings)).mappings().one_or_none()
        if row is not None:
            record_activity(conn, workspace_id, case_id, "finding_edited", finding_id, timestamp, version=row["version"])
        return row


def snapshot_state(row) -> str:
    expected = row["snapshot_sha256"]
    if expected is None:
        return "not_captured"
    return "verified" if digest(row["record_json"]) == expected else "mismatch"


def save_record(workspace_id: str, case_id: str, record_id: str, payload: str, snapshot: bool):
    engine = database(settings.database_url)
    values = {
        "id": str(uuid4()), "workspace_id": workspace_id, "case_id": case_id,
        "record_id": record_id, "record_json": payload,
        "snapshot_sha256": digest(payload) if snapshot else None, "saved_at": now(),
    }
    try:
        with engine.begin() as conn:
            conn.execute(insert(evidence).values(**values))
            record_activity(conn, workspace_id, case_id, "evidence_saved", values["id"], values["saved_at"])
    except IntegrityError:
        # The unique key preserves the first capture on repeated or racing saves.
        with engine.connect() as conn:
            existing = conn.execute(select(evidence).where(
                evidence.c.workspace_id == workspace_id, evidence.c.case_id == case_id,
                evidence.c.record_id == record_id,
            )).mappings().one_or_none()
        if existing is not None:
            return existing
        raise
    return values


if __name__ == "__main__":
    metadata.create_all(database(settings.database_url))
