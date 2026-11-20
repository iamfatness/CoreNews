import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import update

from app.config import settings
from app.connectors.edgar import EdgarConnector
from app.evidence_store import database, evidence, metadata
from app.main import app
from app.routers import research, search

ROOT = "/api/research"
CERTIFICATES = [{"id": 123, "common_name": "example.org", "name_value": "example.org"}]
FILINGS = {
    "cik": "320193",
    "name": "Apple Inc.",
    "filings": {"recent": {
        "accessionNumber": ["0000320193-25-000079", "0000320193-25-000080"],
        "form": ["10-K", "4"],
        "filingDate": ["2025-10-31", "2025-11-01"],
    }},
}


def headers(workspace):
    return {"Authorization": f"Bearer fixture-{workspace}"}


class ResearchEvidenceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.addCleanup(database.cache_clear)
        url = "sqlite:///" + (Path(directory.name) / "research.sqlite").as_posix()
        experiment = patch.multiple(
            settings,
            database_url=url,
            research_workspace_token_hashes={
                name: hashlib.sha256(f"fixture-{name}".encode()).hexdigest()
                for name in ("first", "second")
            },
            research_signing_key=SecretStr("fixture-only-signing-key-for-tests"),
            research_snapshot_sources={"SEC EDGAR"},
            edgar_user_agent="CoreNews test contact@example.org",
        )
        experiment.start()
        self.addCleanup(experiment.stop)
        self.engine = database(url)
        self.addCleanup(self.engine.dispose)
        metadata.create_all(self.engine)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        patcher = patch.object(research, "edgar", EdgarConnector())
        patcher.start()
        self.addCleanup(patcher.stop)

    def create(self, workspace, title="Sample investigation"):
        response = self.client.post(ROOT + "/cases", headers=headers(workspace), json={"title":title})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def search(self, workspace, source, query):
        return self.client.get(ROOT + "/search", headers=headers(workspace),
                               params={"source":source, "q":query})

    def save(self, workspace, case, entry):
        return self.client.put(ROOT + f"/cases/{case}/evidence", headers=headers(workspace), json=entry)

    def test_saves_both_sources_and_reopens_without_upstream(self):
        case = self.create("first")
        with patch.object(search.crtsh, "search_domain", AsyncMock(return_value=CERTIFICATES)):
            ct = self.search("first", "crtsh", "example.org").json()["records"][0]
        directory = {"0": {"ticker": "AAPL", "cik_str": 320193}}
        with patch.object(research.edgar, "_request", AsyncMock(side_effect=[directory, FILINGS, FILINGS])) as upstream:
            by_ticker = self.search("first", "edgar", "aapl")
            by_cik = self.search("first", "edgar", "320193")
            self.assertEqual(by_ticker.status_code, 200, by_ticker.text)
            self.assertEqual(by_cik.status_code, 200, by_cik.text)
            filing = by_ticker.json()["records"][0]
            self.assertEqual(by_ticker.json()["total"], 1)
            self.assertEqual(filing["record"]["id"], by_cik.json()["records"][0]["record"]["id"])
            self.assertTrue(filing["record"]["source_url"].endswith("0000320193-25-000079-index.htm"))
            self.assertEqual(upstream.await_count, 3)

        for item in (ct, filing):
            first = self.save("first", case, item)
            second = self.save("first", case, item)
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(first.json(), second.json())
        with patch.object(search.crtsh, "search_domain", AsyncMock(side_effect=httpx.ReadTimeout("offline"))), \
             patch.object(research.edgar, "search", AsyncMock(side_effect=httpx.ReadTimeout("offline"))):
            opened = self.client.get(ROOT + f"/cases/{case}", headers=headers("first"))
        self.assertEqual(opened.status_code, 200, opened.text)
        saved = {row["record"]["source"]:row for row in opened.json()["evidence"]}
        self.assertEqual(set(saved), {"crt.sh", "SEC EDGAR"})
        for label, expected in (("crt.sh", "not_captured"), ("SEC EDGAR", "verified")):
            item = saved[label]
            verify = ROOT + f"/cases/{case}/evidence/{item['id']}/verify"
            self.assertEqual(self.client.get(verify, headers=headers("first")).json()["status"], expected)
            self.assertEqual(self.client.get(verify, headers=headers("second")).status_code, 404)
        filing_id = saved["SEC EDGAR"]["id"]
        with self.engine.begin() as connection:
            connection.execute(update(evidence).where(evidence.c.id == filing_id).values(record_json="altered"))
        mismatch = self.client.get(ROOT + f"/cases/{case}/evidence/{filing_id}/verify", headers=headers("first"))
        self.assertEqual(mismatch.json()["status"], "mismatch")

    def test_protects_cases_and_signed_records(self):
        first = self.create("first")
        second = self.create("second")
        self.assertEqual(self.client.get(ROOT + "/cases").status_code, 401)
        self.assertEqual(self.client.get(ROOT + f"/cases/{first}", headers=headers("second")).status_code, 404)
        self.assertEqual([row["id"] for row in self.client.get(ROOT + "/cases", headers=headers("second")).json()], [second])
        with patch.object(search.crtsh, "search_domain", AsyncMock(return_value=CERTIFICATES)):
            entry = self.search("first", "crtsh", "example.org").json()["records"][0]
        self.assertEqual(self.save("second", first, entry).status_code, 404)
        self.assertEqual(self.save("second", second, entry).status_code, 422)
        entry["record"]["title"] = "Fabricated record"
        self.assertEqual(self.save("first", first, entry).status_code, 422)

    def test_separates_edgar_timeout_from_bad_identifier_and_empty_results(self):
        with patch.object(research.edgar, "search", AsyncMock(side_effect=httpx.ReadTimeout("timeout"))):
            self.assertEqual(self.search("first", "edgar", "AAPL").status_code, 504)
            self.assertEqual(self.search("first", "edgar", "https://example.org").status_code, 422)
        empty_filings = {**FILINGS, "filings":{"recent":{"accessionNumber":[], "form":[], "filingDate":[]}}}
        with patch.object(research.edgar, "_request", AsyncMock(return_value=empty_filings)):
            self.assertEqual(self.search("first", "edgar", "320193").json()["records"], [])
