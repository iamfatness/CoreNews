import asyncio
import re
from datetime import date, datetime, timezone
from time import monotonic
from typing import Literal

import httpx
from pydantic import BaseModel

from ..records import ResearchRecord, source_text

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/"
FORMS = {"10-K", "10-Q", "8-K", "20-F", "40-F", "6-K"}
FILING_LIMIT = 50


class FilingRecord(ResearchRecord):
    record_type: Literal["sec_filing"] = "sec_filing"
    cik: str
    company: str
    accession: str
    form: str
    filed_on: date | None = None


class FilingSearchResults(BaseModel):
    query: str
    source: str = "SEC EDGAR"
    total: int
    records: list[FilingRecord]


class UnknownFiler(ValueError):
    pass


def normalize_filer(query: str) -> str:
    value = query.strip().upper()
    if re.fullmatch(r"[0-9]{1,10}", value) and int(value):
        return value.zfill(10)
    if re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", value):
        return value
    raise ValueError("Enter a ticker such as AAPL or an SEC CIK such as 0000320193.")


def filing_date(value: object) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def normalize_filings(query: str, cik: str, payload: object) -> FilingSearchResults:
    if not isinstance(payload, dict) or str(payload.get("cik", "")).zfill(10) != cik:
        raise ValueError("SEC EDGAR returned the wrong filer.")
    company = source_text(payload.get("name"))
    filings = payload.get("filings")
    recent = filings.get("recent") if isinstance(filings, dict) else None
    if not company or not isinstance(recent, dict):
        raise ValueError("SEC EDGAR did not return usable filings.")
    columns = [recent.get(field) for field in ("accessionNumber", "form", "filingDate")]
    if not all(isinstance(column, list) for column in columns):
        raise ValueError("SEC EDGAR did not return usable filing columns.")
    if len({len(column) for column in columns}) != 1:
        raise ValueError("SEC EDGAR returned inconsistent filing columns.")

    collected_at = datetime.now(timezone.utc).replace(microsecond=0)
    records = {}
    for accession, form, filed in zip(*columns, strict=True):
        if not isinstance(form, str) or form.removesuffix("/A") not in FORMS:
            continue
        if not isinstance(accession, str) or not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", accession):
            raise ValueError("SEC EDGAR returned an invalid filing identifier.")
        original = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}-index.htm"
        records.setdefault(
            accession,
            FilingRecord(
                id=f"edgar:{accession}",
                title=f"{company} · {form}",
                source="SEC EDGAR",
                source_url=original,
                collected_at=collected_at,
                company=company,
                cik=cik,
                accession=accession,
                form=form,
                filed_on=filing_date(filed),
            ),
        )
    return FilingSearchResults(query=query, total=len(records), records=list(records.values())[:FILING_LIMIT])


class EdgarConnector:
    def __init__(self):
        self._request_lock = asyncio.Lock()
        self._ticker_lock = asyncio.Lock()
        self._next_request = 0.0
        self._tickers_until = 0.0
        self._tickers: dict[str, set[str]] = {}

    async def _request(self, url: str, user_agent: str) -> object:
        # One deployment process, paced below the published service limit.
        async with self._request_lock:
            await asyncio.sleep(max(0, self._next_request - monotonic()))
            self._next_request = monotonic() + 0.5
            async with httpx.AsyncClient(timeout=10, headers={"User-Agent": user_agent}) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

    async def _resolve(self, ticker: str, user_agent: str) -> str:
        async with self._ticker_lock:
            if monotonic() >= self._tickers_until:
                payload = await self._request(SEC_TICKERS, user_agent)
                if not isinstance(payload, dict):
                    raise ValueError("SEC EDGAR did not return a usable ticker directory.")
                tickers: dict[str, set[str]] = {}
                for row in payload.values():
                    if not isinstance(row, dict):
                        continue
                    symbol = source_text(row.get("ticker"))
                    cik = str(row.get("cik_str", ""))
                    if symbol and re.fullmatch(r"[0-9]{1,10}", cik) and int(cik):
                        tickers.setdefault(symbol.upper(), set()).add(cik.zfill(10))
                if not tickers:
                    raise ValueError("SEC EDGAR returned an empty ticker directory.")
                self._tickers = tickers
                self._tickers_until = monotonic() + 86400
            candidates = self._tickers.get(ticker, set())
        if len(candidates) != 1:
            reason = "Ticker not found." if not candidates else "Ticker matches more than one filer."
            raise UnknownFiler(reason + " Try the SEC CIK.")
        return next(iter(candidates))

    async def search(self, query: str, user_agent: str) -> FilingSearchResults:
        cik = query if query.isdigit() else await self._resolve(query, user_agent)
        payload = await self._request(f"{SEC_SUBMISSIONS}CIK{cik}.json", user_agent)
        return normalize_filings(query, cik, payload)
