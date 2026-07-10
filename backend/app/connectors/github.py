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

    def _path(self) -> str:
        return self.config.get("path", "").strip("/")

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
        repo, path = self._repo(), self._path()
        if not repo:
            return []
        url = f"{_API}/repos/{repo}/contents/{path}".rstrip("/")
        try:
            r = httpx.get(url, headers=self._headers(),
                          params={"ref": self._branch()}, timeout=15)
            r.raise_for_status()
            items = r.json()
        except (httpx.HTTPError, ValueError):
            return []
        if isinstance(items, dict):  # single file returned
            items = [items]
        return [
            {"path": it["path"], "name": it["name"].rsplit(".", 1)[0]}
            for it in items
            if it.get("type") == "file" and it["name"].lower().endswith(_EXTS)
        ]

    def fetch(self, ref: dict[str, str]) -> RawPolicy:
        repo = self._repo()
        url = f"{_API}/repos/{repo}/contents/{ref['path']}"
        r = httpx.get(url, headers=self._headers(),
                      params={"ref": self._branch()}, timeout=15)
        r.raise_for_status()
        data = r.json()
        text = base64.b64decode(data.get("content", "")).decode("utf-8", "replace")
        return RawPolicy(path=ref["path"], name=ref.get("name", ref["path"]),
                         text=text, meta={"source": f"github:{repo}"})
