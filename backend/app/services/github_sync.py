"""GitHub event orchestration — the bridge between a verified webhook and the
existing ingestion + analysis pipeline.

Two entry points, both *reusing* the existing engine (no new analysis logic):

* :func:`process_push` — for ``push`` events. Identifies the changed policy
  files, downloads **only those** from GitHub at the pushed commit, feeds each
  through the existing :func:`ingest_raw_policy`, runs the existing corpus
  :func:`run_analysis`, then records an immutable audit row per file and emits a
  live event. The whole repo is not re-downloaded.

* :func:`process_pull_request` — for ``pull_request`` events. Produces a
  *preview* conflict/compliance summary for the PR head using the existing
  :func:`analyze_corpus`, **without** mutating the stored corpus, so reviewers
  see impact before merge. Future-ready for automatic PR comments.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine import analyze_corpus, parse_policy
from app.ai_engine.types import PolicyInput
from app.connectors.github import GitHubConnector
from app.core.logging import get_logger
from app.models import Connector, Policy
from app.services import events
from app.services.analysis import _as_of, _to_input, run_analysis
from app.services.audit import record_audit
from app.services.ingestion import ingest_raw_policy, policy_slug

log = get_logger("github_sync")

_CHANGE_KEYS = ("added", "modified", "removed")


# --------------------------- connector matching ----------------------------

def github_connectors_for(db: Session, repo: str | None) -> list[Connector]:
    """GitHub connector rows whose configured repo matches the payload repo.

    Case-insensitive on ``owner/name``; when the payload carries no repo (unit
    tests, simulated events) every GitHub connector is returned so a manual
    push still targets the right source.
    """
    rows = db.query(Connector).filter(Connector.type == "GITHUB").all()
    if not repo:
        return rows
    repo_l = repo.lower()
    return [c for c in rows if str((c.config or {}).get("repo", "")).lower() == repo_l]


def changed_paths(payload: dict) -> dict[str, str]:
    """Map ``path -> change_type`` across all commits in a push payload.

    Later commits win, and a removal after an add/modify (or vice-versa)
    reflects the net final state for that path in the push.
    """
    result: dict[str, str] = {}
    for commit in payload.get("commits", []):
        for key in _CHANGE_KEYS:
            for path in commit.get(key, []) or []:
                result[path] = key
    return result


# --------------------------------- push ------------------------------------

def process_push(db: Session, payload: dict) -> dict[str, Any]:
    """Handle a push: targeted ingest of changed policies + one analysis pass."""
    repo = (payload.get("repository") or {}).get("full_name")
    branch = (payload.get("ref") or "").replace("refs/heads/", "") or None
    head = payload.get("head_commit") or {}
    commit_sha = payload.get("after") or head.get("id")
    commit_url = head.get("url")
    author = (head.get("author") or {}).get("name") or \
        (payload.get("pusher") or {}).get("name")

    connectors = github_connectors_for(db, repo)
    if not connectors:
        return {"matched_connectors": 0, "changed_policies": 0,
                "detail": f"No GitHub connector configured for {repo}"}

    all_changes = changed_paths(payload)
    ingested: list[dict[str, str]] = []

    for connector in connectors:
        impl = GitHubConnector(config=connector.config or {})
        for path, change_type in all_changes.items():
            if not impl.is_policy_path(path):
                continue  # ignore non-policy files (README, code, ...)
            name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]

            if change_type == "removed":
                # No content to fetch; best-effort id from the file name.
                ingested.append({"path": path, "change_type": "removed",
                                 "policy_id": policy_slug(name), "old_hash": None,
                                 "new_hash": None})
                continue
            try:
                raw = impl.fetch({"path": path, "name": name,
                                  "ref": commit_sha or impl._branch()})
            except Exception as exc:  # noqa: BLE001 - degrade per-file, keep going
                log.warning("fetch failed", extra={"extra_fields": {
                    "path": path, "error": str(exc)}})
                continue
            # Resolve the *stable* id the way ingestion will (frontmatter ``id:``
            # wins over the filename slug) so we can capture the pre-change hash.
            stable_id = parse_policy(raw.text, policy_id=policy_slug(name)).id
            existing = db.get(Policy, stable_id)
            old_hash = existing.content_hash if existing else None
            policy = ingest_raw_policy(db, raw)
            ingested.append({"path": path, "change_type": change_type,
                             "policy_id": policy.id, "old_hash": old_hash,
                             "new_hash": policy.content_hash})
        connector.status = "CONNECTED"
    db.commit()

    # Re-analysis is inherently corpus-wide (conflicts are cross-policy), so we
    # run it once after all targeted ingests — never per file.
    if any(i["change_type"] != "removed" for i in ingested):
        run_analysis(db)

    # Append one immutable audit row per changed policy, with impact derived
    # from the just-completed analysis.
    for item in ingested:
        record_audit(db, source="GITHUB", event_type="push",
                     repo=repo, branch=branch, commit_sha=commit_sha,
                     commit_url=commit_url, author=author,
                     policy_file=item["path"], policy_id=item["policy_id"],
                     change_type=item["change_type"],
                     old_hash=item["old_hash"], new_hash=item["new_hash"],
                     detail=f"{item['change_type']} via push to {branch}",
                     commit=False)
    db.commit()

    events.publish("push_processed", {
        "repo": repo, "branch": branch, "commit_sha": commit_sha,
        "changed_policies": len(ingested),
        "files": [i["path"] for i in ingested]})

    return {"matched_connectors": len(connectors),
            "changed_policies": len(ingested),
            "files": [i["path"] for i in ingested]}


# ----------------------------- pull request --------------------------------

def process_pull_request(db: Session, payload: dict) -> dict[str, Any]:
    """Handle a PR: non-destructive preview of conflicts/compliance impact."""
    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened", "ready_for_review"):
        return {"skipped": True, "action": action}

    pr = payload.get("pull_request") or {}
    number = payload.get("number") or pr.get("number")
    head_sha = (pr.get("head") or {}).get("sha")
    pr_url = pr.get("html_url")
    author = (pr.get("user") or {}).get("login")
    repo = (payload.get("repository") or {}).get("full_name")

    connectors = github_connectors_for(db, repo)
    if not connectors or number is None:
        return {"matched_connectors": len(connectors), "changed_policies": 0,
                "detail": "No matching connector or PR number"}

    impl = GitHubConnector(config=connectors[0].config or {})
    changed = [p for p in impl.pull_request_files(int(number)) if impl.is_policy_path(p)]

    # Build a preview corpus: current stored policies, with PR-head versions of
    # the changed files overlaid (in memory only — nothing is persisted).
    inputs: dict[str, PolicyInput] = {p.id: _to_input(p) for p in db.query(Policy).all()}
    changed_ids: list[str] = []
    audited: list[dict[str, str]] = []
    for path in changed:
        name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        try:
            raw = impl.fetch({"path": path, "name": name, "ref": head_sha})
        except Exception as exc:  # noqa: BLE001
            log.warning("PR fetch failed", extra={"extra_fields": {
                "path": path, "error": str(exc)}})
            continue
        parsed = parse_policy(raw.text, policy_id=policy_slug(name),
                              fallback_title=name, source=f"github:{repo}")
        inputs[parsed.id] = PolicyInput(
            id=parsed.id, title=parsed.title, raw_text=raw.text,
            owner=parsed.owner, author=parsed.author, version=parsed.version,
            status=parsed.status, source=parsed.source,
            last_reviewed=parsed.last_reviewed, tags=parsed.tags)
        changed_ids.append(parsed.id)
        audited.append({"path": path, "policy_id": parsed.id})

    result = analyze_corpus(list(inputs.values()), as_of=_as_of())
    relevant = [c for c in result.conflicts
                if c.policy_a_id in changed_ids or c.policy_b_id in changed_ids]
    summary = {
        "conflicts": len(relevant),
        "high": sum(1 for c in relevant if c.severity == "HIGH"),
        "medium": sum(1 for c in relevant if c.severity == "MEDIUM"),
        "low": sum(1 for c in relevant if c.severity == "LOW"),
        "compliance_impact": sorted({clause for c in relevant
                                     for clause in (c.compliance_impact or [])}),
        "items": [{"type": c.conflict_type, "severity": c.severity,
                   "explanation": c.explanation,
                   "resolution": c.resolution_suggestion} for c in relevant[:20]],
    }
    verdict = "CHANGES_REQUESTED" if summary["high"] else \
        ("COMMENT" if relevant else "APPROVE")

    # Audit each changed policy with a PENDING reviewer status (pre-merge).
    for item in audited:
        record_audit(db, source="GITHUB", event_type="pull_request",
                     repo=repo, branch=(pr.get("head") or {}).get("ref"),
                     commit_sha=head_sha, commit_url=pr_url, author=author,
                     pr_number=int(number), pr_url=pr_url,
                     policy_file=item["path"], policy_id=item["policy_id"],
                     change_type="pr", reviewer_status="PENDING",
                     resolution_status="PREVIEW",
                     detail=f"PR #{number}: {summary['conflicts']} conflict(s), "
                            f"suggested review {verdict}",
                     commit=False)
    db.commit()

    events.publish("pr_analyzed", {"repo": repo, "pr_number": number,
                                   "verdict": verdict, **summary})
    maybe_comment_on_pr(connectors[0], int(number), summary, verdict)

    return {"matched_connectors": len(connectors),
            "changed_policies": len(changed_ids), "pr_number": number,
            "suggested_review": verdict, "summary": summary}


def maybe_comment_on_pr(connector: Connector, number: int, summary: dict,
                        verdict: str) -> None:
    """Future hook: post the preview summary as a PR review comment.

    Intentionally a no-op today — enabling it only requires a GitHub App/token
    with ``pull_requests: write`` and flipping ``config['pr_comments']`` on. The
    call site above already passes everything a comment needs.
    """
    if not (connector.config or {}).get("pr_comments"):
        return
    log.info("PR comment suppressed (write scope not enabled)",
             extra={"extra_fields": {"pr": number, "verdict": verdict}})
