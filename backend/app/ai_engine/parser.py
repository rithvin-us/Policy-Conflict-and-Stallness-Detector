"""Policy document parsing: frontmatter + section splitting + sentence split.

Pure standard library — no PyYAML dependency, so it loads on any interpreter.
Supports two metadata sources:
  1. A leading ``--- ... ---`` YAML-ish frontmatter block.
  2. The brief's inline banner: ``--- Password Policy (v2.1, Last Reviewed: 2021-08-15) ---``
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Optional

from .types import PolicyInput

_FRONTMATTER_RE = re.compile(r"^\s*---\s*\n(.*?)\n---\s*\n", re.S)
_BANNER_RE = re.compile(
    r"---\s*(?P<title>.+?)\s*\(v(?P<version>[\d.]+),\s*"
    r"Last Reviewed:\s*(?P<date>\d{4}-\d{2}-\d{2})\)\s*---",
    re.I,
)
_SECTION_RE = re.compile(
    r"^\s*(?:Section\s+)?(?P<num>\d+(?:\.\d+)*)\s*[:.]\s*(?P<body>.+)$", re.I
)
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<body>.+)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _coerce_date(value: str) -> Optional[date]:
    value = value.strip().strip('"').strip("'")
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_frontmatter(block: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            meta[key] = [x.strip().strip('"').strip("'")
                         for x in raw[1:-1].split(",") if x.strip()]
        else:
            meta[key] = raw.strip('"').strip("'")
    return meta


def parse_policy(text: str, *, policy_id: str, fallback_title: str = "Untitled",
                 source: str = "local:seed") -> PolicyInput:
    """Parse raw policy text into a normalized :class:`PolicyInput`."""
    meta: dict[str, Any] = {}
    body = text

    fm = _FRONTMATTER_RE.match(text)
    if fm:
        meta = _parse_frontmatter(fm.group(1))
        body = text[fm.end():]

    banner = _BANNER_RE.search(body)
    title = meta.get("title") or (banner.group("title") if banner else fallback_title)
    version = meta.get("version") or (banner.group("version") if banner else "1.0")

    last_reviewed = None
    if meta.get("last_reviewed"):
        last_reviewed = _coerce_date(str(meta["last_reviewed"]))
    elif banner:
        last_reviewed = _coerce_date(banner.group("date"))

    created_at = None
    if meta.get("created_at"):
        d = _coerce_date(str(meta["created_at"]))
        created_at = datetime(d.year, d.month, d.day) if d else None

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    return PolicyInput(
        id=meta.get("id") or policy_id,
        title=title,
        raw_text=text,
        owner=meta.get("owner", ""),
        author=meta.get("author"),
        version=str(version),
        status=(meta.get("status") or "ACTIVE").upper(),
        source=meta.get("source") or source,
        last_reviewed=last_reviewed,
        created_at=created_at,
        tags=list(tags),
    )


def split_sections(text: str) -> list[tuple[Optional[str], str]]:
    """Return ``[(section_number, sentence_text), ...]``.

    Wrapped lines are first re-joined into logical blocks (a block runs from a
    section header / heading until the next header or a blank line), so an
    obligation that spans two physical lines — e.g. "... erasure\nrequest within
    30 days." — is analyzed as one sentence and keeps its parameters.
    """
    # Strip frontmatter/banner noise before splitting.
    fm = _FRONTMATTER_RE.match(text)
    if fm:
        text = text[fm.end():]

    blocks: list[tuple[Optional[str], str]] = []
    cur_section: Optional[str] = None
    cur_parts: list[str] = []

    def _flush() -> None:
        if cur_parts:
            blocks.append((cur_section, " ".join(cur_parts).strip()))

    for raw in text.splitlines():
        line = raw.strip()
        if not line or _BANNER_RE.search(line):
            _flush()
            cur_section, cur_parts = None, []
            continue

        m = _SECTION_RE.match(line)
        if m:
            _flush()
            cur_section = m.group("num")
            cur_parts = [m.group("body").strip()]
            continue

        h = _MD_HEADING_RE.match(line)
        if h:
            _flush()
            cur_section, cur_parts = None, [h.group("body").strip()]
            continue

        cur_parts.append(line)
    _flush()

    units: list[tuple[Optional[str], str]] = []
    for section, block in blocks:
        for sentence in _SENTENCE_SPLIT_RE.split(block):
            sentence = sentence.strip()
            if len(sentence) > 3:
                units.append((section, sentence))
    return units
