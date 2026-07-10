"""Connector framework + webhook ingestion tests."""
from __future__ import annotations

from app.connectors.local_folder import LocalFolderConnector
from app.connectors.manager import ConnectorManager
from app.connectors.stubs import GitLabConnector


def test_registry_has_all_ten_types():
    types = set(ConnectorManager.types())
    expected = {"LOCAL_FOLDER", "GITHUB", "UPLOAD", "GITLAB", "BITBUCKET",
                "GOOGLE_DRIVE", "ONEDRIVE", "SHAREPOINT", "SLACK", "TEAMS"}
    assert expected <= types


def test_local_folder_connector_collects(tmp_path):
    (tmp_path / "p1.md").write_text(
        "Section 1: All data must be encrypted at rest.", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Section 1: Logs must be retained.",
                                        encoding="utf-8")
    (tmp_path / "ignore.pdf").write_text("binary-ish", encoding="utf-8")
    conn = LocalFolderConnector(config={"path": str(tmp_path)})
    assert conn.verify() == "CONNECTED"
    raws = conn.collect()
    assert len(raws) == 2  # .pdf ignored


def test_stub_connector_is_not_configured():
    assert GitLabConnector().verify() == "NOT_CONFIGURED"
    assert GitLabConnector().supports_webhooks() is True


def test_connector_create_and_sync(client):
    created = client.post("/api/v1/connectors", json={
        "type": "GITHUB", "name": "Nonexistent",
        "config": {"repo": "does-not-exist-xyz/none"}}).json()
    assert created["type"] == "GITHUB"
    # A local seed connector already exists and syncs cleanly.
    local = next(c for c in client.get("/api/v1/connectors").json()["items"]
                 if c["type"] == "LOCAL_FOLDER")
    result = client.post(f"/api/v1/connectors/{local['id']}/sync").json()
    assert result["status"] == "CONNECTED"


def test_webhook_ingestion_records_event(client):
    resp = client.post("/api/v1/webhooks/github",
                       json={"ref": "refs/heads/main",
                             "commits": [{"modified": ["policies/x.md"]}]},
                       headers={"X-GitHub-Event": "push"})
    body = resp.json()
    assert body["received"] is True
    assert "policies/x.md" in body["affected_paths"]
    events = client.get("/api/v1/webhooks/events").json()
    assert events["total"] >= 1


def test_secrets_never_returned(client):
    client.post("/api/v1/connectors", json={
        "type": "GITHUB", "name": "WithToken",
        "config": {"repo": "a/b", "token": "supersecret", "api_secret": "x"}})
    for c in client.get("/api/v1/connectors").json()["items"]:
        assert "token" not in c["config"]
        assert "api_secret" not in c["config"]
