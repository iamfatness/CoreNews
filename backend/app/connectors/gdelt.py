import asyncio
import hashlib
import re
from datetime import datetime, timezone
from time import monotonic
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel

from ..records import ResearchRecord, source_text

NEWS_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


class NewsRecord(ResearchRecord):
    record_type: Literal["news_article"] = "news_article"
    publisher_domain: str
    seen_at: datetime | None = None


class NewsResults(BaseModel):
    query: str
    source: str = "GDELT"
    total: int
    records: list[NewsRecord]


def news_query(value: str) -> str:
    query = " ".join(value.split())
    if not (3 <= len(query) <= 120 and re.fullmatch(r"[\w .'-]+", query) and
            sum(char.isalnum() for char in query) >= 3):
        raise ValueError("Enter a news topic of 3 to 120 characters using words, spaces, or hyphens.")
    return query


def seen_time(value: object) -> datetime | None:
    try:
        if isinstance(value, str):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return None


def normalize_news(query: str, payload: object) -> NewsResults:
    rows = payload.get("articles") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("GDELT did not return usable article metadata.")
    collected_at = datetime.now(timezone.utc).replace(microsecond=0)
    records = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        address = source_text(row.get("url"))
        title = source_text(row.get("title"))
        if not address or not title or len(address) > 2048 or not address.isascii() or any(
            char.isspace() or char == "\\" or ord(char) < 32 for char in address
        ):
            continue
        try:
            url = urlsplit(address)
            if url.scheme not in ("http", "https") or not url.hostname or url.username is not None:
                continue
            link = url._replace(fragment="").geturl()
        except ValueError:
            continue
        identifier = hashlib.sha256(link.encode()).hexdigest()
        records.setdefault(identifier, NewsRecord(
            id="gdelt:" + identifier, title=title, source="GDELT", source_url=link,
            collected_at=collected_at, publisher_domain=url.hostname, seen_at=seen_time(row.get("seendate")),
        ))
    if rows and not records:
        raise ValueError("GDELT returned no usable article links.")
    return NewsResults(query=query, total=len(rows), records=list(records.values()))


class GdeltConnector:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._next_request = 0.0

    async def search(self, query: str) -> NewsResults:
        async with self._lock:
            await asyncio.sleep(max(0, self._next_request - monotonic()))
            self._next_request = monotonic() + 5
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.get(NEWS_URL, params={
                    "query": f'"{query}"', "mode": "ArtList", "format": "json",
                    "timespan": "30d", "maxrecords": 25, "sort": "DateDesc",
                })
                response.raise_for_status()
                return normalize_news(query, response.json())
