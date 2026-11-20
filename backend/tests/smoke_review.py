"""Verify the packaged app against the disposable Compose fixture."""

import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8080"
ROOT = "/api/research"


def request(path, method="GET", body=None, *, authorized=True, expected=200):
    headers = {}
    if authorized:
        headers["Authorization"] = "Bearer " + os.environ["CORENEWS_SMOKE_KEY"]
    if body is not None:
        headers["Content-Type"] = "application/json"
    data = json.dumps(body).encode() if body is not None else None
    req = Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=5)
    except HTTPError as failure:
        assert failure.code == expected, f"{method} {path} returned {failure.code}"
        return None
    with response:
        assert response.status == expected, f"{method} {path} returned {response.status}"
        return response.read()


def main():
    assert b"Organization screening" in request("/research/", authorized=False)
    request(ROOT + "/cases", authorized=False, expected=401)
    case = json.loads(request(ROOT + "/cases", "POST", {"title": "Release smoke case"}, expected=201))
    case_path = ROOT + "/cases/" + case["id"]
    results = json.loads(request(ROOT + "/screening/ofac", "POST", {"name": "Fixture Organization"}))
    candidate, = results["records"]
    evidence = json.loads(request(case_path + "/evidence", "PUT", candidate))
    request(case_path + "/evidence/" + evidence["id"] + "/screening-review", "PUT", {
        "decision": "inconclusive", "rationale": "Synthetic catalog fixture.", "version": 0,
    })
    request(case_path + "/findings", "POST", {
        "kind": "finding", "body": "Fixture evidence reviewed.", "evidence_ids": [evidence["id"]],
    }, expected=201)
    report = json.loads(request(case_path + "/report"))
    assert report["evidence"][0]["source_date"] == "2026-11-01"
    assert report["findings"][0]["evidence_ids"] == [evidence["id"]]
    assert report["screening_reviews"][0]["evidence_id"] == evidence["id"]
    activity = json.loads(request(case_path + "/activity"))
    assert [entry["action"] for entry in activity["events"]] == [
        "finding_added", "screening_reviewed", "evidence_saved", "case_created",
    ]
    print("Review stack passed workspace, screening evidence, report, and activity smoke checks.")


if __name__ == "__main__":
    main()
