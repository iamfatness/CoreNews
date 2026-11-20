import hashlib
from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4

from sqlalchemy import (
    and_,
    Column, ForeignKeyConstraint, MetaData, String, Table, Text, UniqueConstraint,
    create_engine, insert, select,
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


@lru_cache(maxsize=1)
def database(url: str):
    return create_engine(url, pool_pre_ping=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_case(workspace_id: str, title: str):
    values = {"workspace_id": workspace_id, "id": str(uuid4()), "title": title, "created_at": now()}
    with database(settings.database_url).begin() as conn:
        conn.execute(insert(cases).values(**values))
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
