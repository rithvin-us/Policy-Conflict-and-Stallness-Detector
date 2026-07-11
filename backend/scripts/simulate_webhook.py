"""Local webhook simulator — exercise the full GitHub pipeline with no network.

Signs a GitHub-shaped payload with ``GITHUB_WEBHOOK_SECRET`` (exactly as GitHub
does) and POSTs it to a running backend, so you can test the whole
webhook -> ingest -> analyze -> audit -> live-feed pipeline without pushing to a
real repo or exposing a tunnel.

Usage (backend running on :8000):

    # push touching an existing sample policy
    python scripts/simulate_webhook.py push --repo owner/sample_policies \\
        --file policies/password_policy.md

    # pull-request preview
    python scripts/simulate_webhook.py pr --repo owner/sample_policies \\
        --number 7 --file policies/password_policy.md

The referenced ``--file`` must exist in the connected GitHub repo (the backend
downloads it for real over the API); the payload only *names* what changed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

# Reuse the exact signing the server verifies with.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.webhook_security import compute_github_signature  # noqa: E402


def _post(url: str, event: str, payload: dict, secret: str) -> None:
    body = json.dumps(payload)
    headers = {"Content-Type": "application/json", "X-GitHub-Event": event}
    if secret:
        headers["X-Hub-Signature-256"] = compute_github_signature(secret, body.encode())
    resp = httpx.post(url, content=body, headers=headers, timeout=30)
    print(f"HTTP {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except ValueError:
        print(resp.text)


def build_push(repo: str, files: list[str], branch: str, sha: str,
               author: str) -> dict:
    return {
        "ref": f"refs/heads/{branch}",
        "after": sha,
        "repository": {"full_name": repo},
        "pusher": {"name": author},
        "head_commit": {
            "id": sha,
            "url": f"https://github.com/{repo}/commit/{sha}",
            "author": {"name": author},
            "message": "simulated policy change",
        },
        "commits": [{"modified": files, "added": [], "removed": []}],
    }


def build_pr(repo: str, number: int, branch: str, sha: str, author: str) -> dict:
    return {
        "action": "opened",
        "number": number,
        "repository": {"full_name": repo},
        "pull_request": {
            "number": number,
            "html_url": f"https://github.com/{repo}/pull/{number}",
            "user": {"login": author},
            "head": {"sha": sha, "ref": branch},
            "base": {"ref": "main"},
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulate a GitHub webhook locally.")
    ap.add_argument("event", choices=["push", "pr"])
    ap.add_argument("--url", default="http://localhost:8000/api/v1/webhooks/github")
    ap.add_argument("--repo", required=True, help="owner/name of the connected repo")
    ap.add_argument("--file", action="append", default=[], dest="files",
                    help="changed policy path (repeatable)")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--sha", default="0000000000000000000000000000000000000000")
    ap.add_argument("--number", type=int, default=1, help="PR number (pr event)")
    ap.add_argument("--author", default="local-tester")
    ap.add_argument("--secret", default=os.getenv("GITHUB_WEBHOOK_SECRET", ""))
    args = ap.parse_args()

    if args.event == "push":
        payload = build_push(args.repo, args.files or ["policies/password_policy.md"],
                             args.branch, args.sha, args.author)
        _post(args.url, "push", payload, args.secret)
    else:
        payload = build_pr(args.repo, args.number, args.branch, args.sha, args.author)
        _post(args.url, "pull_request", payload, args.secret)


if __name__ == "__main__":
    main()
