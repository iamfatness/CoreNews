import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app


class ResearchSearchTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    @patch("app.routers.search.crtsh.search_domain", new_callable=AsyncMock)
    def test_preserves_source_link_and_timestamp_meanings(self, source):
        row = {
            "id": 123,
            "common_name": "example.org",
            "name_value": "example.org\nwww.example.org",
            "entry_timestamp": None,
            "not_before": "2026-09-26T22:05:05",
        }
        source.return_value = [row, row]
        response = self.client.get("/search/records", params={"q": "Example.ORG."})
        self.assertEqual(response.status_code, 200)
        source.assert_awaited_once_with("example.org")
        payload = response.json()
        self.assertEqual(payload["total"], 2)
        self.assertEqual(len(payload["records"]), 1)
        record = payload["records"][0]
        self.assertEqual(record["source_url"], "https://crt.sh/?id=123")
        self.assertEqual(record["names"], ["example.org", "www.example.org"])
        self.assertIsNone(record["logged_at"])
        self.assertEqual(record["valid_from"], "2026-09-26T22:05:05")
        self.assertTrue(record["collected_at"].endswith("Z"))

    @patch("app.routers.search.crtsh.search_domain", new_callable=AsyncMock)
    def test_keeps_raw_api_response_compatible(self, source):
        source.return_value = [{"id": 42, "name_value": "example.org"}]
        self.assertEqual(
            self.client.get("/search/crtsh", params={"q": "example.org"}).json(),
            {
                "source": "crt.sh",
                "query": "example.org",
                "count": 1,
                "results": source.return_value,
            },
        )

    @patch("app.routers.search.crtsh.search_domain", new_callable=AsyncMock)
    def test_timeout_and_empty_results_are_distinct(self, source):
        source.side_effect = [httpx.ReadTimeout("timeout"), []]
        self.assertEqual(
            self.client.get("/search/records", params={"q": "example.org"}).status_code, 504
        )
        response = self.client.get("/search/records", params={"q": "example.org"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["records"], [])

    @patch("app.routers.search.crtsh.search_domain", new_callable=AsyncMock)
    def test_rejects_urls_without_querying_source(self, source):
        response = self.client.get(
            "/search/records", params={"q": "https://example.org"}
        )
        self.assertEqual(response.status_code, 422)
        source.assert_not_awaited()
