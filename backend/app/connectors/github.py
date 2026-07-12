"""GitHub connector — fully implemented against the GitHub REST API.

Config: ``{ "repo": "owner/name", "branch": "main", "path": "policies",
            "token_env": "GITHUB_TOKEN" }``

Lists and fetches markdown/text policy files under ``path``. Works on public
repos without a token; a token (read from the named env var, never persisted)
raises rate limits and enables private repos. Network/HTTP failures degrade to an
ERROR status rather than crashing the sync (SRS NFR-5). Supports webhooks (push).
"""
from __future__ import annotations

import base64
import os

import httpx

from app.core.config import settings

from .base import CONNECTED, ERROR, NOT_CONFIGURED, BaseConnector, RawPolicy

_API = "https://api.github.com"
_EXTS = (".md", ".markdown", ".txt")


class GitHubConnector(BaseConnector):
    type = "GITHUB"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28"}
        token = os.getenv(self.config.get("token_env", "GITHUB_TOKEN"), "") \
            or settings.GITHUB_TOKEN
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _repo(self) -> str | None:
        return self.config.get("repo")

    def _branch(self) -> str:
        return self.config.get("branch", "main")

    def _paths(self) -> list[str]:
        # Support legacy "path" string, or new "paths" list
        paths = self.config.get("paths")
        if not paths:
            single = self.config.get("path", "").strip("/")
            paths = [single] if single else []
        return [p.strip("/") for p in paths if p.strip("/")]

    def supports_webhooks(self) -> bool:
        return True

    def verify(self) -> str:
        repo = self._repo()
        if not repo:
            return NOT_CONFIGURED
        try:
            r = httpx.get(f"{_API}/repos/{repo}", headers=self._headers(), timeout=10)
            return CONNECTED if r.status_code == 200 else ERROR
        except httpx.HTTPError:
            return ERROR

    def list_policies(self) -> list[dict[str, str]]:
        repo = self._repo()
        if not repo:
            return []
        
        all_items = []
        # If no paths specified, we fetch root.
        paths_to_fetch = self._paths() or [""]
        
        for path in paths_to_fetch:
            url = f"{_API}/repos/{repo}/contents/{path}".rstrip("/")
            try:
                r = httpx.get(url, headers=self._headers(),
                              params={"ref": self._branch()}, timeout=15)
                r.raise_for_status()
                items = r.json()
            except (httpx.HTTPError, ValueError):
                continue
            
            if isinstance(items, dict):  # single file returned
                items = [items]
            
            all_items.extend([
                {"path": it["path"], "name": it["name"].rsplit(".", 1)[0]}
                for it in items
                if it.get("type") == "file" and it["name"].lower().endswith(_EXTS)
            ])
            
        return all_items

    def fetch(self, ref: dict[str, str]) -> RawPolicy:
        repo = self._repo()
        # A commit SHA / branch may be pinned per-ref (webhook targeting); fall
        # back to the connector's configured branch for plain full syncs.
        gitref = ref.get("ref") or self._branch()
        url = f"{_API}/repos/{repo}/contents/{ref['path']}"
        r = httpx.get(url, headers=self._headers(),
                      params={"ref": gitref}, timeout=15)
        r.raise_for_status()
        data = r.json()
        text = base64.b64decode(data.get("content", "")).decode("utf-8", "replace")
        name = ref.get("name") or ref["path"].rsplit("/", 1)[-1].rsplit(".", 1)[0]

        # Fetch the last commit date for this file (used for staleness detection).
        last_modified = None
        try:
            commits_url = f"{_API}/repos/{repo}/commits"
            cr = httpx.get(commits_url, headers=self._headers(),
                           params={"sha": gitref, "path": ref["path"], "per_page": 1},
                           timeout=10)
            if cr.status_code == 200:
                commits = cr.json()
                if commits:
                    commit_info = commits[0].get("commit", {})
                    last_modified = (commit_info.get("committer") or {}).get("date")
        except httpx.HTTPError:
            pass  # best-effort; staleness still works without it

        return RawPolicy(path=ref["path"], name=name, text=text,
                         meta={"source": f"github:{repo}", "ref": gitref,
                               "last_modified": last_modified})

    def is_policy_path(self, path: str) -> bool:
        """True when ``path`` is a policy file inside one of the connector's trees."""
        if not path.lower().endswith(_EXTS):
            return False
            
        bases = self._paths()
        if not bases:
            return True
            
        for base in bases:
            if path == base or path.startswith(base + "/"):
                return True
        return False

    def latest_commit(self) -> dict[str, str] | None:
        """Return ``{sha, url, message, author, date}`` for HEAD of the branch.

        Best-effort — network/HTTP failures return ``None`` so status views
        degrade gracefully rather than error (SRS NFR-5).
        """
        repo = self._repo()
        if not repo:
            return None
        try:
            r = httpx.get(f"{_API}/repos/{repo}/commits",
                          headers=self._headers(),
                          params={"sha": self._branch(), "per_page": 1}, timeout=10)
            r.raise_for_status()
            items = r.json()
        except (httpx.HTTPError, ValueError):
            return None
        if not items:
            return None
        c = items[0]
        commit = c.get("commit", {})
        return {
            "sha": c.get("sha", ""),
            "url": c.get("html_url", ""),
            "message": (commit.get("message") or "").split("\n", 1)[0],
            "author": (commit.get("author") or {}).get("name", ""),
            "date": (commit.get("author") or {}).get("date", ""),
        }

    def pull_request_files(self, number: int) -> list[str]:
        """List file paths changed in a pull request (paginated GitHub API)."""
        repo = self._repo()
        if not repo:
            return []
        paths: list[str] = []
        page = 1
        while True:
            try:
                r = httpx.get(f"{_API}/repos/{repo}/pulls/{number}/files",
                              headers=self._headers(),
                              params={"per_page": 100, "page": page}, timeout=15)
                r.raise_for_status()
                items = r.json()
            except (httpx.HTTPError, ValueError):
                break
            if not items:
                break
            paths.extend(it["filename"] for it in items if "filename" in it)
            if len(items) < 100:
                break
            page += 1
        return paths
