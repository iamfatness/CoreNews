"""Import and query the organization subset of an official OFAC SDN XML snapshot."""

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from . import evidence_store as store
from .config import settings
from .records import ResearchRecord

SOURCE = "OFAC SDN"
SOURCE_URL = "https://ofac.treasury.gov/sanctions-list-service"
MAX_BYTES = 32 * 1024 * 1024


class ScreeningCandidate(ResearchRecord):
    record_type: Literal["ofac_candidate"] = "ofac_candidate"
    snapshot_id: str
    published_on: date
    list_uid: str
    programs: list[str]


def normalized_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def parse_snapshot(payload: bytes):
    if len(payload) > MAX_BYTES:
        raise ValueError("The SDN file exceeds the snapshot size limit.")
    xml = payload.decode("utf-8-sig")
    if re.search(r"<!\s*(DOCTYPE|ENTITY)\b", xml, re.IGNORECASE):
        raise ValueError("SDN XML with document type or entity declarations is unsupported.")
    root = ElementTree.fromstring(xml)
    if root.tag.rsplit("}", 1)[-1] != "sdnList":
        raise ValueError("Expected the standard OFAC SDN.XML export.")
    version = root.findtext("./{*}publshInformation/{*}Publish_Date", "").strip()
    published = datetime.strptime(version, "%m/%d/%Y").date()
    source_rows = root.findall("./{*}sdnEntry")
    expected = root.findtext("./{*}publshInformation/{*}Record_Count", "").strip()
    if expected and (not expected.isdigit() or int(expected) != len(source_rows)):
        raise ValueError("The SDN file's record count does not match its content.")

    entries = {}
    for entry in source_rows:
        if entry.findtext("./{*}sdnType", "").strip().casefold() != "entity":
            continue
        uid = entry.findtext("./{*}uid", "").strip()
        name = entry.findtext("./{*}lastName", "").strip()
        key = normalized_name(name)
        if not re.fullmatch(r"[0-9]{1,24}", uid) or not (1 <= len(name) <= 350 and 1 <= len(key) <= 350) or uid in entries:
            raise ValueError("The SDN file contains an invalid or duplicated entity record.")
        programs = [p.text.strip() for p in entry.findall("./{*}programList/{*}program") if p.text and p.text.strip()]
        entries[uid] = {"uid": uid, "name": name, "search_name": key, "programs_json": json.dumps(programs)}
    if not entries:
        raise ValueError("The SDN file contains no organization records.")
    return published.isoformat(), list(entries.values())


def db():
    return store.database(settings.database_url)


def has_snapshot() -> bool:
    with db().connect() as conn:
        return conn.execute(select(store.screening_snapshots.c.id).limit(1)).first() is not None


def import_snapshot(payload: bytes):
    published_on, entries = parse_snapshot(payload)
    snapshot_id = hashlib.sha256(payload).hexdigest()
    snapshots = store.screening_snapshots
    row = {"id": snapshot_id, "published_on": published_on, "imported_at": store.now(), "entity_count": len(entries)}
    try:
        with db().begin() as conn:
            conn.execute(insert(snapshots).values(**row))
            conn.execute(insert(store.screening_entries), [{**entry, "snapshot_id": snapshot_id} for entry in entries])
    except IntegrityError:
        with db().connect() as conn:
            existing = conn.execute(select(snapshots).where(snapshots.c.id == snapshot_id)).mappings().one_or_none()
        if existing is not None:
            return existing
        raise
    return row


def lookup(name: str, snapshot_id: str | None):
    snapshots, entries = store.screening_snapshots, store.screening_entries
    query = select(snapshots)
    if snapshot_id:
        query = query.where(snapshots.c.id == snapshot_id)
    else:
        query = query.order_by(snapshots.c.published_on.desc(), snapshots.c.imported_at.desc(), snapshots.c.id.desc())
    with db().connect() as conn:
        snapshot = conn.execute(query.limit(1)).mappings().one_or_none()
        if snapshot is None:
            return None, []
        rows = conn.execute(select(entries).where(
            entries.c.snapshot_id == snapshot["id"], entries.c.search_name == normalized_name(name),
        ).order_by(entries.c.uid)).mappings().all()
    return snapshot, [
        ScreeningCandidate(
            id=f"ofac:{snapshot['id']}:{item['uid']}", source=SOURCE, source_url=SOURCE_URL,
            title=item["name"], collected_at=snapshot["imported_at"], snapshot_id=snapshot["id"],
            published_on=snapshot["published_on"], list_uid=item["uid"], programs=json.loads(item["programs_json"]),
        ) for item in rows
    ]


def main():
    parser = argparse.ArgumentParser(description="Import an official OFAC SDN.XML file as an immutable organization snapshot.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        with args.path.open("rb") as stream:
            snapshot = import_snapshot(stream.read(MAX_BYTES + 1))
    except (ValueError, OSError, ElementTree.ParseError) as exc:
        parser.error(str(exc))
    print(f"Imported {snapshot['entity_count']} entities for {snapshot['published_on']} · SHA-256 {snapshot['id']}")


if __name__ == "__main__":
    main()
