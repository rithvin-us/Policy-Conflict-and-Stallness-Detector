"""GitHub integration tests: signature verification, changed-file targeting,
pull-request preview, audit trail, and version history.

Network is fully stubbed — ``GitHubConnector`` methods are monkeypatched so the
suite is deterministic and offline (SRS NFR-2), while still exercising the real
webhook → ingest → analyze → audit → live-event pipeline end to end.
"""
from __future__ import annotations

import json

import pytest

from app.connectors.base import CONNECTED, RawPolicy
from app.connectors.github import GitHubConnector
from app.core.config import settings
from app.services import github_sync
from app.services.webhook_security import (
    compute_github_signature,
    verify_github_signature,
)

REPO = "octo/sample_policies"


# ------------------------- signature verification --------------------------

def test_signature_roundtrip():
    body = b'{"hello":"world"}'
    sig = compute_github_signature("s3cret", body)
    assert sig.startswith("sha256=")
    assert verify_github_signature("s3cret", body, sig) is True
    assert verify_github_signature("s3cret", body, "sha256=deadbeef") is False
    assert verify_github_signature("s3cret", body, None) is False


def test_no_secret_disables_verification():
    # Empty secret => local-dev mode, everything passes.
    assert verify_github_signature("", b"anything", None) is True


def test_webhook_rejects_bad_signature_when_secret_set(client, monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", "topsecret")
    payload = {"ref": "refs/heads/main",
               "repository": {"full_name": REPO}, "commits": []}
    body = json.dumps(payload)

    # Missing signature → 401.
    r = client.post("/api/v1/webhooks/github", data=body,
                    headers={"X-GitHub-Event": "push",
                             "Content-Type": "application/json"})
    assert r.status_code == 401

    # Correct signature → 200.
    sig = compute_github_signature("topsecret", body.encode())
    r = client.post("/api/v1/webhooks/github", data=body,
                    headers={"X-GitHub-Event": "push",
                             "X-Hub-Signature-256": sig,
                             "Content-Type": "application/json"})
    assert r.status_code == 200


def test_ping_event_pongs(client):
    r = client.post("/api/v1/webhooks/github", json={"zen": "Keep it simple."},
                    headers={"X-GitHub-Event": "ping"})
    assert r.status_code == 200
    assert r.json()["pong"] is True


# ------------------------------- unit helpers ------------------------------

def test_changed_paths_net_state():
    payload = {"commits": [
        {"added": ["policies/a.md"], "modified": []},
        {"modified": ["policies/a.md", "src/code.py"]},
        {"removed": ["policies/b.md"]},
    ]}
    result = github_sync.changed_paths(payload)
    assert result["policies/a.md"] == "modified"
    assert result["policies/b.md"] == "removed"
    assert result["src/code.py"] == "modified"


def test_is_policy_path_respects_base_and_ext():
    impl = GitHubConnector(config={"repo": REPO, "path": "policies"})
    assert impl.is_policy_path("policies/password_policy.md") is True
    assert impl.is_policy_path("policies/readme.txt") is True
    assert impl.is_policy_path("src/app.py") is False        # wrong dir
    assert impl.is_policy_path("policies/logo.png") is False  # wrong ext


# ------------------------- push targeting + audit --------------------------

@pytest.fixture
def gh_connector(client, monkeypatch):
    """Create a GitHub connector pointed at REPO with network stubbed out."""
    monkeypatch.setattr(GitHubConnector, "verify", lambda self: CONNECTED)
    created = client.post("/api/v1/connectors", json={
        "type": "GITHUB", "name": "Sample Policies",
        "config": {"repo": REPO, "branch": "main", "path": "policies"}}).json()
    return created


def _fake_fetch(text_by_name):
    def fetch(self, ref):
        name = ref.get("name") or ref["path"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
        text = text_by_name.get(name, f"--- {name} ---\nAll data must be encrypted.")
        return RawPolicy(path=ref["path"], name=name, text=text,
                         meta={"source": f"github:{REPO}", "ref": ref.get("ref")})
    return fetch


def test_push_ingests_only_policy_files_and_audits(client, gh_connector, monkeypatch):
    monkeypatch.setattr(GitHubConnector, "fetch", _fake_fetch({
        "password_policy": "--- Password Policy (v9.9) ---\n"
                           "Passwords must be rotated every 30 days.\n"
                           "Last Reviewed: 2026-07-01"}))

    payload = {
        "ref": "refs/heads/main",
        "after": "abc1234def5678",
        "repository": {"full_name": REPO},
        "pusher": {"name": "alice"},
        "head_commit": {"id": "abc1234def5678",
                        "url": f"https://github.com/{REPO}/commit/abc1234",
                        "author": {"name": "Alice Dev"}},
        "commits": [{"modified": ["policies/password_policy.md"],
                     "added": [], "removed": [],
                     "message": "tighten rotation"},
                    {"modified": ["README.md", "src/app.py"]}],  # unrelated → ignored
    }
    r = client.post("/api/v1/webhooks/github", json=payload,
                    headers={"X-GitHub-Event": "push"})
    assert r.status_code == 200
    body = r.json()
    # Only the one policy file counted; README/code ignored.
    assert body["changed_policies"] == 1
    assert body["files"] == ["policies/password_policy.md"]

    # An immutable audit row exists with the commit provenance.
    audit = client.get(f"/api/v1/audit?search=password_policy").json()
    assert audit["total"] >= 1
    row = audit["items"][0]
    assert row["commit_sha"] == "abc1234def5678"
    assert row["author"] == "Alice Dev"
    assert row["policy_file"] == "policies/password_policy.md"
    assert row["new_hash"]  # captured


def test_push_creates_new_policy_version(client, gh_connector, monkeypatch):
    # First push establishes the policy.
    monkeypatch.setattr(GitHubConnector, "fetch", _fake_fetch({
        "access_control_policy": "--- Access Control (v1.0) ---\n"
                                 "Access must be reviewed quarterly."}))
    payload = {"ref": "refs/heads/main", "after": "sha-v1",
               "repository": {"full_name": REPO},
               "head_commit": {"id": "sha-v1", "author": {"name": "Bob"}},
               "commits": [{"modified": ["policies/access_control_policy.md"]}]}
    client.post("/api/v1/webhooks/github", json=payload,
                headers={"X-GitHub-Event": "push"})
    pid = "pol-access-control-policy"
    v1 = client.get(f"/api/v1/policies/{pid}/versions").json()["total"]

    # Second push with different text → new version.
    monkeypatch.setattr(GitHubConnector, "fetch", _fake_fetch({
        "access_control_policy": "--- Access Control (v1.0) ---\n"
                                 "Access must be reviewed MONTHLY now."}))
    payload["after"] = "sha-v2"
    payload["head_commit"]["id"] = "sha-v2"
    client.post("/api/v1/webhooks/github", json=payload,
                headers={"X-GitHub-Event": "push"})
    v2 = client.get(f"/api/v1/policies/{pid}/versions").json()["total"]
    assert v2 == v1 + 1


# ----------------------------- pull requests -------------------------------

def test_pull_request_preview_produces_verdict(client, gh_connector, monkeypatch):
    monkeypatch.setattr(GitHubConnector, "pull_request_files",
                        lambda self, n: ["policies/password_policy.md", "README.md"])
    monkeypatch.setattr(GitHubConnector, "fetch", _fake_fetch({
        "password_policy": "--- Password Policy (v2.0) ---\n"
                           "Passwords must never expire."}))

    payload = {"action": "opened", "number": 42,
               "repository": {"full_name": REPO},
               "pull_request": {"number": 42, "html_url": f"https://github.com/{REPO}/pull/42",
                                "user": {"login": "carol"},
                                "head": {"sha": "prsha123", "ref": "feature/pw"}}}
    r = client.post("/api/v1/webhooks/github", json=payload,
                    headers={"X-GitHub-Event": "pull_request"})
    assert r.status_code == 200
    body = r.json()
    assert body["changed_policies"] == 1  # README ignored
    assert body["suggested_review"] in {"APPROVE", "COMMENT", "CHANGES_REQUESTED"}
    assert "summary" in body

    # PR audit row is PENDING review / PREVIEW resolution.
    audit = client.get("/api/v1/audit?reviewer_status=PENDING").json()
    assert any(a["event_type"] == "pull_request" for a in audit["items"])


# ------------------------------ status + SSE -------------------------------

def test_github_status_reports_connector(client, gh_connector):
    status = client.get("/api/v1/github/status").json()
    assert "webhook_url" in status
    assert any(r["repo"] == REPO for r in status["repositories"])


def test_audit_review_transition(client, gh_connector, monkeypatch):
    monkeypatch.setattr(GitHubConnector, "fetch", _fake_fetch({}))
    client.post("/api/v1/webhooks/github",
                json={"ref": "refs/heads/main", "after": "s",
                      "repository": {"full_name": REPO},
                      "head_commit": {"id": "s", "author": {"name": "Dan"}},
                      "commits": [{"added": ["policies/new_thing.md"]}]},
                headers={"X-GitHub-Event": "push"})
    row = client.get("/api/v1/audit?search=new_thing").json()["items"][0]
    patched = client.patch(f"/api/v1/audit/{row['id']}",
                           json={"reviewer_status": "REVIEWED",
                                 "resolution_status": "RESOLVED"}).json()
    assert patched["reviewer_status"] == "REVIEWED"
    assert patched["resolution_status"] == "RESOLVED"
