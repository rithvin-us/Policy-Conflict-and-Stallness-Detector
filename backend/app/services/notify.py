"""Compliance-manager notifications (FR-12).

Notifies compliance managers — never employees — when a *new* HIGH-severity
conflict appears. New-ness is tracked by a stable signature so repeated analysis
runs do not re-alert on the same conflict. Outbound delivery to a configured
webhook is best-effort; the notification is always persisted for the in-app feed.
"""
from __future__ import annotations

import httpx
from sqlalchemy.orm import Session

from app.ai_engine.types import Conflict
from app.core.config import settings
from app.core.ids import new_id
from app.core.logging import get_logger
from app.models import Notification

log = get_logger("notify")


def _signature(c: Conflict) -> str:
    a, b = sorted((c.policy_a_id, c.policy_b_id))
    return f"{a}|{b}|{c.conflict_type}"


def notify_new_high(db: Session, high_conflicts: list[Conflict]) -> list[Notification]:
    existing = {n.title for n in db.query(Notification.title).all()}
    created: list[Notification] = []

    for c in high_conflicts:
        title = f"HIGH conflict: {_signature(c)}"
        if title in existing:
            continue
        body = f"{c.explanation} Resolution: {c.resolution_suggestion}"
        note = Notification(id=new_id("ntf"), audience="compliance_manager",
                            severity="HIGH", title=title, body=body)
        _deliver(note)
        db.add(note)
        created.append(note)

    if created:
        db.commit()
        log.info("notified compliance managers",
                 extra={"extra_fields": {"count": len(created)}})
    return created


def _deliver(note: Notification) -> None:
    if not settings.NOTIFY_WEBHOOK_URL:
        return
    try:
        httpx.post(settings.NOTIFY_WEBHOOK_URL, json={
            "audience": note.audience, "severity": note.severity,
            "title": note.title, "body": note.body}, timeout=8)
        note.delivered = True
    except httpx.HTTPError as exc:  # pragma: no cover - network dependent
        log.warning("notification delivery failed",
                    extra={"extra_fields": {"error": str(exc)}})
