"""End-to-end API flow tests against a seeded in-memory-ish SQLite instance."""
from __future__ import annotations


def test_health_and_ready(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["db"] is True


def test_seed_populated_dashboard(client):
    ov = client.get("/api/v1/dashboard/overview").json()
    assert ov["counts"]["policies"] == 6
    assert ov["counts"]["conflicts"] >= 1
    assert 0 <= ov["overall"] <= 100


def test_conflicts_include_known_high(client):
    items = client.get("/api/v1/conflicts").json()["items"]
    pairs = [{c["policy_a_id"], c["policy_b_id"]} for c in items if c["severity"] == "HIGH"]
    assert {"POL-PWD-001", "POL-CLD-002"} in pairs


def test_conflict_detail_has_explanation(client):
    cid = client.get("/api/v1/conflicts").json()["items"][0]["id"]
    payload = client.get(f"/api/v1/conflicts/{cid}").json()["explanation_payload"]
    assert payload["title"]
    assert len(payload["spans"]) == 2
    assert payload["likely_resolution"]


def test_graph_modes(client):
    pol = client.get("/api/v1/graph?mode=POLICY").json()
    assert pol["mode"] == "POLICY" and len(pol["nodes"]) == 6
    obl = client.get("/api/v1/graph?mode=OBLIGATION").json()
    assert obl["mode"] == "OBLIGATION" and len(obl["nodes"]) >= 18


def test_upload_creates_conflict_and_lowers_health(client):
    resp = client.post("/api/v1/policies/upload", json={
        "title": "Uploaded MFA Standard", "owner": "Security",
        "raw_text": "Section 1: Passwords must not be rotated periodically.",
    })
    assert resp.status_code == 201
    pid = resp.json()["id"]
    detail = client.get(f"/api/v1/policies/{pid}").json()
    assert any(c["severity"] == "HIGH" for c in detail["conflicts"])
    assert detail["health_score"] < 100
    client.delete(f"/api/v1/policies/{pid}")  # keep suite isolated


def test_report_generation_and_download(client):
    r = client.post("/api/v1/reports",
                    json={"report_type": "POLICY_HEALTH", "format": "MARKDOWN"})
    assert r.status_code == 201
    rid = r.json()["id"]
    dl = client.get(f"/api/v1/reports/{rid}/download")
    assert dl.status_code == 200 and b"Policy Guardian" in dl.content


def test_review_queue_ranked_by_risk(client):
    items = client.get("/api/v1/review-queue").json()["items"]
    assert items
    risks = [i["risk"] for i in items]
    assert risks == sorted(risks, reverse=True)


def test_compliance_coverage_shape(client):
    cov = client.get("/api/v1/compliance/coverage").json()
    assert {"frameworks", "gaps"} <= cov.keys()
    assert any(f["framework"] == "ISO 27001" for f in cov["frameworks"])


def test_analysis_run_is_idempotent(client):
    a = client.post("/api/v1/analysis/run", json={}).json()["counts"]
    b = client.post("/api/v1/analysis/run", json={}).json()["counts"]
    assert a == b  # deterministic engine → stable counts
