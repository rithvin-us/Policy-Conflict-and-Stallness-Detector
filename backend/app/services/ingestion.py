"""Ingestion & versioning pipeline.

Normalizes a :class:`RawPolicy` from any connector into a :class:`Policy` plus a
:class:`PolicyVersion`. Re-ingesting changed text creates a new version and bumps
metadata; unchanged text is a no-op (content-hash dedupe), so repeated syncs and
webhook re-triggers are idempotent.
"""
from __future__ import annotations

import hashlib
import re

from sqlalchemy.orm import Session

from app.ai_engine import parse_policy
from app.connectors.base import RawPolicy
from app.core.ids import new_id
from app.core.logging import get_logger
from app.models import Policy, PolicyVersion, TimelineEvent

log = get_logger("ingestion")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(name: str) -> str:
    return "pol-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]


def _timeline(db: Session, kind: str, policy: Policy, detail: str) -> None:
    db.add(TimelineEvent(id=new_id("tl"), kind=kind, policy_id=policy.id,
                         title=policy.title, detail=detail))


def ingest_raw_policy(db: Session, raw: RawPolicy) -> Policy:
    """Insert or update a policy from fetched text. Returns the Policy row."""
    parsed = parse_policy(raw.text, policy_id=_slug(raw.name),
                          fallback_title=raw.name,
                          source=raw.meta.get("source", "upload"))
    content_hash = _hash(raw.text)
    existing = db.get(Policy, parsed.id)

    if existing is None:
        policy = Policy(
            id=parsed.id,
            title=parsed.title,
            source=parsed.source,
            owner=parsed.owner,
            author=parsed.author,
            version=parsed.version,
            status=parsed.status,
            last_reviewed=parsed.last_reviewed,
            tags=parsed.tags,
            content=raw.text,
            raw_text=raw.text,
            summary=_auto_summary(raw.text),
            content_hash=content_hash,
        )
        db.add(policy)
        db.flush()
        db.add(PolicyVersion(id=new_id("ver"), policy_id=policy.id,
                             version=policy.version, raw_text=raw.text,
                             content_hash=content_hash))
        _timeline(db, "INGESTED", policy, f"Ingested from {policy.source}")
        log.info("policy ingested", extra={"extra_fields": {"policy_id": policy.id}})
        return policy

    if existing.content_hash == content_hash:
        return existing  # unchanged → idempotent no-op

    # Changed → new version + metadata refresh.
    existing.raw_text = raw.text
    existing.content = raw.text
    existing.last_reviewed = parsed.last_reviewed or existing.last_reviewed
    existing.owner = parsed.owner or existing.owner
    existing.tags = parsed.tags or existing.tags
    existing.summary = _auto_summary(raw.text)
    existing.content_hash = content_hash
    existing.version = _bump(existing.version)
    db.add(PolicyVersion(id=new_id("ver"), policy_id=existing.id,
                         version=existing.version, raw_text=raw.text,
                         content_hash=content_hash))
    _timeline(db, "UPDATED", existing, f"New version {existing.version}")
    log.info("policy updated", extra={"extra_fields": {"policy_id": existing.id}})
    return existing


def _bump(version: str) -> str:
    m = re.match(r"(\d+)\.(\d+)", version or "1.0")
    if not m:
        return "1.1"
    return f"{m.group(1)}.{int(m.group(2)) + 1}"


def _auto_summary(text: str, limit: int = 240) -> str:
    for line in text.splitlines():
        s = line.strip()
        if len(s) > 40 and not s.startswith("---") and "Last Reviewed" not in s:
            return (s[:limit] + "...") if len(s) > limit else s
    return ""
