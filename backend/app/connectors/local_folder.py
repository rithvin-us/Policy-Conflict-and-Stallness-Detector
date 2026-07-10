"""Local folder connector — fully implemented.

Reads ``*.md`` / ``*.txt`` / ``*.markdown`` policy files from a directory on disk.
This is the zero-dependency, always-available source used to seed the demo.
"""
from __future__ import annotations

from pathlib import Path

from .base import CONNECTED, ERROR, NOT_CONFIGURED, BaseConnector, RawPolicy

_EXTS = {".md", ".markdown", ".txt"}


class LocalFolderConnector(BaseConnector):
    type = "LOCAL_FOLDER"

    def _root(self) -> Path | None:
        path = self.config.get("path")
        return Path(path) if path else None

    def verify(self) -> str:
        root = self._root()
        if root is None:
            return NOT_CONFIGURED
        return CONNECTED if root.is_dir() else ERROR

    def list_policies(self) -> list[dict[str, str]]:
        root = self._root()
        if root is None or not root.is_dir():
            return []
        refs = []
        for f in sorted(root.rglob("*")):
            if f.suffix.lower() in _EXTS and f.is_file():
                refs.append({"path": str(f), "name": f.stem})
        return refs

    def fetch(self, ref: dict[str, str]) -> RawPolicy:
        p = Path(ref["path"])
        text = p.read_text(encoding="utf-8", errors="replace")
        return RawPolicy(path=str(p), name=ref.get("name", p.stem), text=text,
                         meta={"source": f"local:{p.parent.name}"})
