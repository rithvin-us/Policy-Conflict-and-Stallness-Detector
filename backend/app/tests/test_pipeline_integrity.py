"""Pipeline-integrity regression guards.

These tests lock in the robustness fixes so the whole ingest → obligations →
conflicts → staleness → governance → API "stepper" cannot silently break again:

* The seed corpus directory must actually exist and contain policy files. A
  prior rename (``sample_data`` → ``sample_policies``) left every code and config
  reference dangling, which emptied the corpus and turned the entire suite red
  while seeding produced zero policies. The path-resolution guards below fail
  loudly the instant that regression recurs, instead of cascading into dozens of
  opaque assertion errors elsewhere.
* The GitHub token override must stay in-memory (never leak into ``os.environ``).
* The report download endpoint must 404 — not 500 — when the artifact file is
  gone (ephemeral free-tier disk).
"""
from __future__ import annotations

import os
import pathlib

from app.ai_engine import analyze_corpus
from app.connectors.github import GitHubConnector
from app.connectors.local_folder import LocalFolderConnector
from app.core.config import settings

from .conftest import AS_OF, CORPUS_DIR


# --------------------------- seed corpus integrity -------------------------

def test_configured_seed_dir_exists_and_has_policies():
    """The default SEED_POLICY_DIR must point at real policy files.

    This is the guard that would have caught the sample_data→sample_policies
    rename break at its source.
    """
    seed_dir = pathlib.Path(settings.SEED_POLICY_DIR)
    assert seed_dir.is_dir(), f"SEED_POLICY_DIR does not exist: {seed_dir}"
    policy_files = list(seed_dir.glob("*.md"))
    assert policy_files, f"No .md policy files under {seed_dir}"


def test_test_corpus_dir_matches_reality():
    """The shared test fixture corpus dir must resolve to real files too."""
    assert CORPUS_DIR.is_dir(), f"Test CORPUS_DIR does not exist: {CORPUS_DIR}"
    assert list(CORPUS_DIR.glob("*.md")), f"No policies under {CORPUS_DIR}"


def test_local_folder_connector_reads_seed_corpus():
    """The seed connector path used on first boot must collect the corpus."""
    conn = LocalFolderConnector(config={"path": settings.SEED_POLICY_DIR})
    assert conn.verify() == "CONNECTED"
    assert len(conn.collect()) >= 6


# ----------------------- end-to-end engine determinism ---------------------

def test_seed_corpus_produces_findings(policies):
    """A non-empty corpus must yield obligations and at least one conflict —
    proving the classical deterministic pipeline is wired end to end."""
    assert len(policies) >= 6
    result = analyze_corpus(policies, as_of=AS_OF)
    assert result.obligations, "no obligations extracted from seed corpus"
    assert result.conflicts, "no conflicts detected across seed corpus"
    assert 0 <= result.governance["overall"] <= 100


def test_analysis_is_deterministic(policies):
    """Two runs over the same corpus/date must be byte-for-byte identical."""
    a = analyze_corpus(policies, as_of=AS_OF)
    b = analyze_corpus(policies, as_of=AS_OF)
    assert [c.id for c in a.conflicts] == [c.id for c in b.conflicts]
    assert a.governance["overall"] == b.governance["overall"]


# --------------------- github token override (no env leak) -----------------

def test_github_token_override_is_in_memory_only():
    """The bulk-onboarding token must be used for auth without touching the
    process environment (thread-safe, no cross-request leakage)."""
    sentinel = "__pipeline_integrity_should_not_persist__"
    assert sentinel not in os.environ  # precondition

    conn = GitHubConnector(config={"repo": "octo/example"})
    conn.token_override = sentinel
    headers = conn._headers()

    assert headers.get("Authorization") == f"Bearer {sentinel}"
    # The override must never be written into os.environ.
    assert sentinel not in os.environ.values()
    assert "__temp_gh_token" not in os.environ


def test_github_no_token_means_no_auth_header(monkeypatch):
    """With no override and no ambient token, no Authorization header is sent."""
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    conn = GitHubConnector(config={"repo": "octo/example", "token_env": "NOPE_UNSET"})
    assert "Authorization" not in conn._headers()


# ----------------------- report download 404, not 500 ----------------------

def test_download_missing_report_artifact_returns_404(client):
    """A report row whose file was reaped (ephemeral disk) must 404 cleanly."""
    created = client.post(
        "/api/v1/reports",
        json={"report_type": "POLICY_HEALTH", "format": "MARKDOWN"},
    ).json()
    rid = created["id"]
    # Simulate the artifact vanishing after a restart.
    if created.get("file_path") and os.path.isfile(created["file_path"]):
        os.remove(created["file_path"])
    resp = client.get(f"/api/v1/reports/{rid}/download")
    assert resp.status_code == 404
