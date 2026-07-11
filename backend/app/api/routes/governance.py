"""Continuous-governance endpoints layered on top of the GitHub integration:

* ``GET  /audit``                — searchable immutable audit trail
* ``PATCH /audit/{id}``          — advance the review/resolution workflow only
* ``GET  /github/status``        — repository health, webhook + sync status
* ``GET  /events/stream``        — Server-Sent Events feed for live dashboards

Nothing here re-implements analysis; it surfaces what the existing pipeline and
audit service already produced.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.connectors.github import GitHubConnector
from app.core.config import settings
from app.core.db import get_db
from app.models import AuditEvent, Connector, Policy
from app.schemas import AuditReviewRequest, audit_to_dict
from app.services import events
from app.services.audit import query_audit

router = APIRouter()

# Only the review workflow may mutate an audit row; provenance stays immutable.
_REVIEWER_STATES = {"PENDING", "ACKNOWLEDGED", "REVIEWED", "DISMISSED"}
_RESOLUTION_STATES = {"OPEN", "IN_PROGRESS", "RESOLVED", "PREVIEW", "WONT_FIX"}


@router.get("/audit")
def list_audit(repo: str | None = None, author: str | None = None,
               policy_id: str | None = None, conflict_status: str | None = None,
               reviewer_status: str | None = None, resolution_status: str | None = None,
               search: str | None = None, limit: int = 100, offset: int = 0,
               db: Session = Depends(get_db)) -> dict:
    rows, total = query_audit(
        db, repo=repo, author=author, policy_id=policy_id,
        conflict_status=conflict_status, reviewer_status=reviewer_status,
        resolution_status=resolution_status, search=search,
        limit=limit, offset=offset)
    return {"items": [audit_to_dict(a) for a in rows], "total": total}


@router.patch("/audit/{audit_id}")
def review_audit(audit_id: str, body: AuditReviewRequest,
                 db: Session = Depends(get_db)) -> dict:
    row = db.get(AuditEvent, audit_id)
    if not row:
        raise HTTPException(404, f"Audit event {audit_id} not found")
    if body.reviewer_status:
        state = body.reviewer_status.upper()
        if state not in _REVIEWER_STATES:
            raise HTTPException(400, f"Invalid reviewer_status: {state}")
        row.reviewer_status = state
    if body.resolution_status:
        state = body.resolution_status.upper()
        if state not in _RESOLUTION_STATES:
            raise HTTPException(400, f"Invalid resolution_status: {state}")
        row.resolution_status = state
    db.commit()
    events.publish("audit_updated", {"id": row.id,
                                     "reviewer_status": row.reviewer_status,
                                     "resolution_status": row.resolution_status})
    return audit_to_dict(row)


@router.get("/github/status")
def github_status(db: Session = Depends(get_db)) -> dict:
    """Repository health for every configured GitHub connector."""
    connectors = db.query(Connector).filter(Connector.type == "GITHUB").all()
    repos = []
    for c in connectors:
        cfg = c.config or {}
        impl = GitHubConnector(config=cfg)
        live = impl.verify()
        latest = impl.latest_commit() if live == "CONNECTED" else None
        policy_count = db.query(Policy).filter(
            Policy.source == f"github:{cfg.get('repo')}").count()
        repos.append({
            "connector_id": c.id,
            "name": c.name,
            "repo": cfg.get("repo"),
            "branch": cfg.get("branch", "main"),
            "path": cfg.get("path", ""),
            "status": live,
            "last_sync": c.last_sync.isoformat() if c.last_sync else None,
            "error_message": c.error_message,
            "webhook_configured": bool(cfg.get("webhook_secret_ref")),
            "webhook_events": cfg.get("webhook_events", []),
            "latest_commit": latest,
            "policy_count": policy_count,
        })
    recent = (db.query(AuditEvent).filter(AuditEvent.source == "GITHUB")
              .order_by(AuditEvent.created_at.desc()).limit(10).all())
    return {
        "connected": any(r["status"] == "CONNECTED" for r in repos),
        "signature_verification": bool(settings.GITHUB_WEBHOOK_SECRET),
        "webhook_url": f"{settings.API_PREFIX}/webhooks/github",
        "repositories": repos,
        "recent_changes": [audit_to_dict(a) for a in recent],
        "live_subscribers": events.subscriber_count(),
    }


@router.get("/events/stream")
async def events_stream(request: Request) -> StreamingResponse:
    """Server-Sent Events stream. The browser opens one ``EventSource`` here and
    receives a message every time governance state changes (webhook, analysis,
    audit)."""
    queue = events.subscribe()

    async def generator():
        # Prime the connection so the client's onopen fires immediately.
        yield "event: connected\ndata: {}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"  # comment frame keeps proxies open
        finally:
            events.unsubscribe(queue)

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no",
                                      "Connection": "keep-alive"})
