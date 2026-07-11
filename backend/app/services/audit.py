"""Audit-trail service.

Creates immutable :class:`~app.models.AuditEvent` rows and derives each row's
analysis-impact fields (conflict / duplicate / staleness / compliance / risk)
from the findings the existing engine already persisted. Also exposes a
searchable query used by the ``/audit`` endpoint.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine import types as T
from app.core.ids import new_id
from app.core.logging import get_logger
from app.models import AuditEvent, Conflict, StalenessFinding

log = get_logger("audit")

_SEVERITY_RANK = {T.HIGH: 3, T.MEDIUM: 2, T.LOW: 1}
_DUPLICATE_TYPES = {T.REDUNDANCY, T.PARTIAL_REDUNDANCY}


def finding_status_for(db: Session, policy_id: str | None) -> dict[str, Any]:
    """Summarize a policy's current findings into audit-row status fields.

    Reads the findings the engine wrote in the latest ``run_analysis`` — never
    recomputes — so the audit row is a faithful snapshot of that analysis.
    """
    empty = {"conflict_status": "NONE", "duplicate_status": "NONE",
             "staleness_status": "NONE", "compliance_impact": [], "risk_score": 0.0}
    if not policy_id:
        return empty

    conflicts = db.query(Conflict).filter(
        (Conflict.policy_a_id == policy_id) | (Conflict.policy_b_id == policy_id)
    ).all()
    stale = db.query(StalenessFinding).filter(
        StalenessFinding.policy_id == policy_id
    ).all()

    # Split true conflicts from redundancy/duplicate findings.
    real = [c for c in conflicts if c.conflict_type not in _DUPLICATE_TYPES]
    dupes = [c for c in conflicts if c.conflict_type in _DUPLICATE_TYPES]

    conflict_status = _top_severity([c.severity for c in real])
    duplicate_status = _top_severity([c.severity for c in dupes]) if dupes else "NONE"
    staleness_status = _top_severity([s.severity for s in stale]) if stale else "NONE"

    compliance: list[str] = []
    for c in conflicts:
        for clause in (c.compliance_impact or []):
            if clause not in compliance:
                compliance.append(clause)

    risk = max([c.risk for c in conflicts] + [s.risk for s in stale] + [0.0])
    return {"conflict_status": conflict_status, "duplicate_status": duplicate_status,
            "staleness_status": staleness_status, "compliance_impact": compliance,
            "risk_score": round(risk, 3)}


def _top_severity(severities: list[str]) -> str:
    if not severities:
        return "NONE"
    return max(severities, key=lambda s: _SEVERITY_RANK.get(s, 0))


def record_audit(db: Session, *, policy_file: str, policy_id: str | None,
                 source: str = "GITHUB", event_type: str = "push",
                 change_type: str = "modified", repo: str | None = None,
                 branch: str | None = None, commit_sha: str | None = None,
                 commit_url: str | None = None, author: str | None = None,
                 pr_number: int | None = None, pr_url: str | None = None,
                 old_hash: str | None = None, new_hash: str | None = None,
                 reviewer_status: str = "PENDING", resolution_status: str = "OPEN",
                 detail: str | None = None, commit: bool = True) -> AuditEvent:
    """Append one immutable audit row, deriving impact fields from findings."""
    impact = finding_status_for(db, policy_id)
    event = AuditEvent(
        id=new_id("aud"), source=source, event_type=event_type,
        repo=repo, branch=branch, commit_sha=commit_sha, commit_url=commit_url,
        author=author, pr_number=pr_number, pr_url=pr_url,
        policy_file=policy_file, policy_id=policy_id, change_type=change_type,
        old_hash=old_hash, new_hash=new_hash,
        reviewer_status=reviewer_status, resolution_status=resolution_status,
        detail=detail, **impact,
    )
    db.add(event)
    if commit:
        db.commit()
    log.info("audit recorded", extra={"extra_fields": {
        "policy_file": policy_file, "commit": commit_sha,
        "conflict_status": impact["conflict_status"]}})
    return event


def query_audit(db: Session, *, repo: str | None = None, author: str | None = None,
                policy_id: str | None = None, conflict_status: str | None = None,
                reviewer_status: str | None = None, resolution_status: str | None = None,
                search: str | None = None, limit: int = 100,
                offset: int = 0) -> tuple[list[AuditEvent], int]:
    """Filtered, newest-first audit search. Returns ``(rows, total)``."""
    q = db.query(AuditEvent)
    if repo:
        q = q.filter(AuditEvent.repo == repo)
    if author:
        q = q.filter(AuditEvent.author == author)
    if policy_id:
        q = q.filter(AuditEvent.policy_id == policy_id)
    if conflict_status:
        q = q.filter(AuditEvent.conflict_status == conflict_status.upper())
    if reviewer_status:
        q = q.filter(AuditEvent.reviewer_status == reviewer_status.upper())
    if resolution_status:
        q = q.filter(AuditEvent.resolution_status == resolution_status.upper())
    if search:
        like = f"%{search}%"
        q = q.filter(AuditEvent.policy_file.ilike(like)
                     | AuditEvent.commit_sha.ilike(like)
                     | AuditEvent.author.ilike(like)
                     | AuditEvent.detail.ilike(like))
    total = q.count()
    rows = q.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()
    return rows, total
