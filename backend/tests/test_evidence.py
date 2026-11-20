import asyncio
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine, update
from sqlalchemy.schema import CreateSchema, DropSchema

from app.config import settings
from app import watch_store, watch_worker
from app.connectors.edgar import EdgarConnector
from app.connectors.gdelt import normalize_news
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
        pg_url = os.environ.get("CORENEWS_TEST_DATABASE_URL")
        url = pg_url or "sqlite:///" + (Path(directory.name) / "research.sqlite").as_posix()
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
            gdelt_enabled=True,
        )
        experiment.start()
        self.addCleanup(experiment.stop)
        if pg_url:
            base = create_engine(url)
            self.addCleanup(base.dispose)
            schema = "corenews_test_" + uuid4().hex
            with base.begin() as connection:
                connection.execute(CreateSchema(schema))
            def remove_schema():
                with base.begin() as connection:
                    connection.execute(DropSchema(schema, cascade=True))
            self.addCleanup(remove_schema)
            self.engine = base.execution_options(schema_translate_map={None: schema})
            bind = patch("app.evidence_store.database", return_value=self.engine)
            bind.start()
            self.addCleanup(bind.stop)
        else:
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

    def test_scheduled_watches_baseline_deduplicate_and_save_case_alert(self):
        case = self.create("first")
        root = ROOT + f"/cases/{case}"
        first_payload = {"articles": [{"url":"https://example.org/news/a","title":"First"}]}
        next_payload = {"articles": [
            {"url":"https://example.org/news/a","title":"First"},
            {"url":"https://example.org/news/b","title":"Second"},
        ]}
        with patch.object(settings, "research_watches_enabled", True):
            with patch.object(watch_store, "epoch", return_value=10000):
                creation = self.client.post(root + "/watches", headers=headers("first"),
                                            json={"source":"gdelt","query":"Port Strike","interval_minutes":60})
                self.assertEqual(creation.status_code, 201, creation.text)
                duplicate = self.client.post(root + "/watches", headers=headers("first"),
                                             json={"source":"gdelt","query":"port strike","interval_minutes":60})
                self.assertEqual(duplicate.json()["id"], creation.json()["id"])
            with patch.object(watch_worker, "lookup_news", AsyncMock(side_effect=[
                normalize_news("port strike", first_payload),
                normalize_news("port strike", next_payload),
                normalize_news("port strike", next_payload),
            ])):
                for check, expected in ((10000, 0), (13600, 1), (17200, 1)):
                    with patch.object(watch_store, "epoch", return_value=check):
                        self.assertTrue(asyncio.run(watch_worker.run_once()))
                    alerts = self.client.get(root + "/monitoring", headers=headers("first")).json()["alerts"]
                    self.assertEqual(len(alerts), expected)
        alert = alerts[0]
        self.assertEqual(alert["record"]["title"], "Second")
        self.assertEqual(self.client.get(root + "/monitoring", headers=headers("second")).status_code, 404)
        alert_path = root + "/alerts/" + alert["id"]
        self.assertEqual(self.client.put(alert_path + "/review", headers=headers("second")).status_code, 404)
        self.assertEqual(self.client.put(alert_path + "/evidence", headers=headers("second")).status_code, 404)
        saved = self.client.put(alert_path + "/evidence", headers=headers("first"))
        self.assertEqual(saved.status_code, 200, saved.text)
        repeated = self.client.put(alert_path + "/evidence", headers=headers("first"))
        self.assertEqual(saved.json()["id"], repeated.json()["id"])
        self.assertTrue(self.client.put(alert_path + "/review", headers=headers("first")).json()["reviewed"])
        after = self.client.get(root + "/monitoring", headers=headers("first")).json()
        self.assertTrue(after["alerts"][0]["reviewed"])

    def test_watch_recovers_expired_lease_and_ignores_old_worker(self):
        case = self.create("first")
        root = ROOT + f"/cases/{case}"
        body = {"source":"edgar","query":"320193","interval_minutes":60}
        disabled = self.client.post(root + "/watches", headers=headers("first"), json=body)
        self.assertEqual(disabled.status_code, 503)
        with patch.object(settings, "research_watches_enabled", True), \
             patch.object(watch_store, "epoch", return_value=10000):
            creation = self.client.post(root + "/watches", headers=headers("first"), json=body)
            self.assertEqual(creation.status_code, 201, creation.text)
            old = watch_store.claim_due(10000)
            self.assertIsNotNone(old)
            self.assertIsNone(watch_store.claim_due(10001))
            replacement = watch_store.claim_due(10000 + watch_store.LEASE_SECONDS)
            self.assertNotEqual(old["lease_id"], replacement["lease_id"])
            watch_store.finish_check(old, 10121, [], "Stale worker error")
            watch_store.finish_check(replacement, 10122, [], "Retryable source error")
            current = self.client.get(root + "/monitoring", headers=headers("first")).json()["watches"][0]
            self.assertIsNone(current["last_success"])
            self.assertEqual(current["last_error"], "Retryable source error")
            target = root + "/watches/" + current["id"]
            self.assertEqual(self.client.patch(target, headers=headers("first"), json={"paused":True}).status_code, 200)
            self.assertIsNone(watch_store.claim_due(20000))
            self.assertTrue(self.client.patch(target, headers=headers("first"), json={"paused":False}).status_code == 200)
            self.assertIsNotNone(watch_store.claim_due(20000))

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
        company = ROOT + "/entities/company/320193"
        timeline = self.client.get(company, headers=headers("first")).json()["records"]
        self.assertEqual([item["record"]["id"] for item in timeline], [filing["record"]["id"]])
        self.assertEqual(timeline[0]["date_label"], "Filed")
        self.assertEqual(self.client.get(company, headers=headers("second")).json()["records"], [])
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

    def test_combines_sources_and_labels_partial_failure(self):
        with patch.object(search.crtsh, "search_domain", AsyncMock(return_value=CERTIFICATES)), \
             patch.object(research.edgar, "search", AsyncMock(side_effect=httpx.ReadTimeout("offline"))):
            response = self.client.post(
                ROOT + "/discover", headers=headers("first"),
                json={"queries": {"crtsh": "example.org", "edgar": "AAPL"}},
            )
        self.assertEqual(response.status_code, 200, response.text)
        result = {row["source_id"]: row for row in response.json()}
        self.assertEqual(result["crtsh"]["records"][0]["record"]["id"], "crtsh:123")
        self.assertIn("timed out", result["edgar"]["error"])
        self.assertEqual(result["edgar"]["records"], [])
        self.assertEqual(self.client.get(ROOT + "/sources").status_code, 401)

    def test_news_and_certificate_timeline_uses_saved_workspace_evidence(self):
        news = normalize_news("port strike", {"articles": [
            {"url": "https://example.org/a#story", "title": "Test article", "seendate": "20261101T090000Z"},
            {"url": "javascript:alert(1)", "title": "Invalid link"},
        ]})
        self.assertEqual([item.source_url for item in news.records], ["https://example.org/a"])
        case = self.create("first", "First workspace case")
        with patch.object(search.crtsh, "search_domain", AsyncMock(return_value=CERTIFICATES)), \
             patch.object(research.gdelt, "search", AsyncMock(return_value=news)):
            for source, query in (("crtsh", "example.org"), ("gdelt", "port strike")):
                entry = self.search("first", source, query).json()["records"][0]
                self.assertEqual(self.save("first", case, entry).status_code, 200)
        timeline = ROOT + "/entities/domain/EXAMPLE.ORG."
        records = self.client.get(timeline, headers=headers("first")).json()["records"]
        self.assertEqual({item["record"]["source"] for item in records}, {"crt.sh", "GDELT"})
        self.assertTrue(all(item["case_title"] == "First workspace case" for item in records))
        self.assertEqual(next(item["date_label"] for item in records if item["record"]["source"] == "GDELT"),
                         "Seen by GDELT")
        self.assertEqual(self.client.get(timeline, headers=headers("second")).json()["records"], [])
        self.assertEqual(self.client.get(ROOT + "/entities/domain/org.example", headers=headers("first")).json()["records"], [])
        filtered = self.client.get(ROOT + "/evidence?source=gdelt", headers=headers("first")).json()["records"]
        self.assertEqual([item["record"]["source"] for item in filtered], ["GDELT"])

    def test_case_report_keeps_citations_and_flags_uncited_findings_offline(self):
        case = self.create("first", "Case report")
        path = ROOT + f"/cases/{case}"
        with patch.object(research.edgar, "_request", AsyncMock(return_value=FILINGS)):
            selection = self.search("first", "edgar", "320193").json()["records"][0]
        saved = self.save("first", case, selection).json()
        for entry in (
            {"kind": "finding", "body": "Annual report filed.", "evidence_ids": [saved["id"], saved["id"]]},
            {"kind": "finding", "body": "Confirm publication date."},
            {"kind": "question", "body": "What does the next filing say?"},
        ):
            response = self.client.post(path + "/findings", headers=headers("first"), json=entry)
            self.assertEqual(response.status_code, 201, response.text)
        with patch.object(research.edgar, "_request", AsyncMock(side_effect=httpx.ReadTimeout("offline"))):
            response = self.client.get(path + "/report", headers=headers("first"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        report = response.json()
        self.assertEqual(report["uncited_findings"], 1)
        self.assertEqual(report["schema_version"], 1)
        entries = {item["body"]:item for item in report["findings"]}
        self.assertEqual(entries["Annual report filed."]["evidence_ids"], [saved["id"]])
        self.assertTrue(entries["Confirm publication date."]["uncited"])
        self.assertFalse(entries["What does the next filing say?"]["uncited"])
        self.assertEqual(report["evidence"][0]["verification"], "verified")
        self.assertEqual(report["evidence"][0]["source_url"], selection["record"]["source_url"])
        self.assertEqual(report["evidence"][0]["snapshot_sha256"], saved["snapshot_sha256"])
        with self.engine.begin() as connection:
            connection.execute(update(evidence).where(evidence.c.id == saved["id"]).values(record_json="altered"))
        changed = self.client.get(path + "/report", headers=headers("first")).json()["evidence"][0]
        self.assertEqual(changed["verification"], "mismatch")
        self.assertFalse(changed["metadata_available"])
        self.assertIsNone(changed["source_url"])

    def test_case_report_rejects_foreign_citations_and_stale_edits(self):
        owner = self.create("first")
        another_case = self.create("first")
        foreign_workspace = self.create("second")
        with patch.object(search.crtsh, "search_domain", AsyncMock(return_value=CERTIFICATES)):
            selection = self.search("first", "crtsh", "example.org").json()["records"][0]
        saved = self.save("first", owner, selection).json()
        body = {"kind": "finding", "body": "Case note", "evidence_ids": [saved["id"]]}
        owner_path = ROOT + f"/cases/{owner}"
        for case_id, key in ((another_case, "first"), (foreign_workspace, "second")):
            response = self.client.post(ROOT + f"/cases/{case_id}/findings", headers=headers(key), json=body)
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.get(owner_path + "/report", headers=headers("second")).status_code, 404)
        created = self.client.post(owner_path + "/findings", headers=headers("first"), json=body).json()
        edit_path = owner_path + "/findings/" + created["id"]
        update_body = {**body, "body": "Corrected note", "version": created["version"]}
        self.assertEqual(self.client.put(edit_path, headers=headers("second"), json=update_body).status_code, 404)
        edited = self.client.put(edit_path, headers=headers("first"), json=update_body)
        self.assertEqual(edited.status_code, 200, edited.text)
        self.assertEqual(edited.json()["version"], 2)
        stale = self.client.put(edit_path, headers=headers("first"), json={**update_body, "body": "Stale edit"})
        self.assertEqual(stale.status_code, 409)
        report = self.client.get(owner_path + "/report", headers=headers("first")).json()
        self.assertEqual(report["findings"][0]["body"], "Corrected note")
