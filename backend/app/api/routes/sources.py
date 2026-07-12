"""Connector and webhook endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import json

from app.connectors.base import ERROR, SYNCING
from app.connectors.manager import ConnectorManager, connector_manager
from app.core.config import settings
from app.core.db import get_db
from app.core.ids import new_id
from app.core.logging import get_logger
from app.models import Connector, WebhookEvent
from app.schemas import (
    ConnectorCreateRequest,
    WebhookRegisterRequest,
    connector_to_dict,
    webhook_to_dict,
)
from app.services import events, github_sync
from app.services.analysis import run_analysis
from app.services.ingestion import ingest_raw_policy
from app.services.webhook_security import verify_github_signature

router = APIRouter()
log = get_logger("sources")


def _sync_connector(db: Session, connector: Connector) -> dict:
    connector.status = SYNCING
    db.commit()
    try:
        impl = connector_manager.instantiate(connector)
        status = impl.verify()
        raws = impl.collect()
        for raw in raws:
            ingest_raw_policy(db, raw)
        connector.status = status
        connector.last_sync = datetime.now(timezone.utc)
        connector.error_message = None
        db.commit()
        run_analysis(db)
        return {"synced": len(raws), "status": connector.status}
    except Exception as exc:  # noqa: BLE001 - surface any connector failure
        connector.status = ERROR
        connector.error_message = str(exc)
        db.commit()
        log.warning("connector sync failed",
                    extra={"extra_fields": {"connector": connector.id,
                                            "error": str(exc)}})
        return {"synced": 0, "status": ERROR, "error": str(exc)}


@router.get("/connectors")
def list_connectors(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Connector).all()
    return {"items": [connector_to_dict(c) for c in rows], "total": len(rows)}


@router.post("/connectors", status_code=201)
def create_connector(body: ConnectorCreateRequest,
                     db: Session = Depends(get_db)) -> dict:
    ctype = body.type.upper()
    if not ConnectorManager.is_known(ctype):
        raise HTTPException(400, f"Unknown connector type: {ctype}")
    connector = Connector(id=new_id("con"), type=ctype, name=body.name,
                          config=body.config, status="NOT_CONFIGURED")
    # Reflect real reachability immediately.
    connector.status = connector_manager.instantiate(connector).verify()
    db.add(connector)
    db.commit()
    return connector_to_dict(connector)


@router.post("/connectors/{connector_id}/sync")
def sync_connector(connector_id: str, db: Session = Depends(get_db)) -> dict:
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, f"Connector {connector_id} not found")
    result = _sync_connector(db, connector)
    return {"job_id": new_id("job"), "status": connector.status, **result}


@router.get("/connectors/{connector_id}/health")
def connector_health(connector_id: str, db: Session = Depends(get_db)) -> dict:
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, f"Connector {connector_id} not found")
    live = connector_manager.instantiate(connector).verify()
    connector.status = live
    db.commit()
    return {"status": live,
            "last_sync": connector.last_sync.isoformat() if connector.last_sync else None,
            "error_message": connector.error_message}


# --------------------------- webhooks --------------------------------------

@router.post("/webhooks/register")
def register_webhook(body: WebhookRegisterRequest,
                     request: Request,
                     db: Session = Depends(get_db)) -> dict:
    connector = db.get(Connector, body.connector_id)
    if not connector:
        raise HTTPException(404, f"Connector {body.connector_id} not found")
    secret_ref = new_id("whsec")
    cfg = dict(connector.config or {})
    cfg["webhook_secret_ref"] = secret_ref
    cfg["webhook_events"] = body.event_types
    connector.config = cfg
    db.commit()
    
    # Determine webhook URL
    base_url = str(request.base_url).rstrip("/")
    api_url = settings.API_URL if hasattr(settings, "API_URL") and settings.API_URL else base_url
    webhook_url = f"{api_url}/api/v1/webhooks/{connector.type.lower()}"
    
    if body.github_token and connector.type == "GITHUB":
        repo = cfg.get("repo")
        if not repo:
            raise HTTPException(400, "Connector is missing a repository path")
            
        import httpx
        gh_url = f"https://api.github.com/repos/{repo}/hooks"
        headers = {
            "Authorization": f"Bearer {body.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        gh_payload = {
            "name": "web",
            "active": True,
            "events": body.event_types,
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": settings.GITHUB_WEBHOOK_SECRET
            }
        }
        
        response = httpx.post(gh_url, headers=headers, json=gh_payload)
        if response.status_code not in (200, 201):
            log.error("Failed to create webhook on GitHub", extra={"extra_fields": {"response": response.text}})
            raise HTTPException(400, f"Failed to create webhook on GitHub: {response.text}")

    return {"id": new_id("whk"), "secret_ref": secret_ref,
            "url": webhook_url,
            "event_types": body.event_types}


@router.post("/webhooks/{connector}")
async def ingest_webhook(connector: str, request: Request,
                         db: Session = Depends(get_db)) -> dict:
    # Read the RAW body first — signature verification must run over the exact
    # bytes GitHub signed, before any JSON re-encoding.
    raw_body = await request.body()
    source = connector.upper()

    if source == "GITHUB":
        signature = request.headers.get("X-Hub-Signature-256")
        if not verify_github_signature(settings.GITHUB_WEBHOOK_SECRET,
                                       raw_body, signature):
            log.warning("webhook signature rejected",
                        extra={"extra_fields": {"source": source}})
            raise HTTPException(401, "Invalid webhook signature")

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        payload = {}

    # GitHub sends the semantic event in a header; fall back for other sources.
    event_type = request.headers.get("X-GitHub-Event",
                                     payload.get("event_type", "push"))

    # GitHub's "ping" (sent when a webhook is first configured) just confirms
    # connectivity — acknowledge without running the pipeline.
    if event_type == "ping":
        _record_event(db, source, event_type, payload, "PROCESSED",
                      "ping acknowledged")
        return {"received": True, "pong": True,
                "zen": payload.get("zen", "Design for failure.")}

    event = _record_event(db, source, event_type, payload, "PROCESSING", None)

    try:
        if source == "GITHUB" and event_type == "pull_request":
            result = github_sync.process_pull_request(db, payload)
        elif source == "GITHUB":  # push (and anything push-shaped)
            result = github_sync.process_push(db, payload)
        else:
            # Non-GitHub sources: fall back to a full idempotent re-sync.
            result = {"resynced": _resync_source(db, source)}
    except Exception as exc:  # noqa: BLE001 - never 500 a webhook; record + 200
        event.status = "FAILED"
        event.processed_at = datetime.now(timezone.utc)
        event.detail = f"error: {exc}"
        db.commit()
        log.warning("webhook processing failed",
                    extra={"extra_fields": {"event": event.id, "error": str(exc)}})
        return {"received": True, "event_id": event.id, "error": str(exc)}

    event.status = "PROCESSED"
    event.processed_at = datetime.now(timezone.utc)
    event.detail = _summarize(event_type, result)
    db.commit()

    events.publish("webhook_processed", {
        "event_id": event.id, "source": source, "event_type": event_type,
        "detail": event.detail})

    return {"received": True, "event_id": event.id, **result}


def _record_event(db: Session, source: str, event_type: str, payload: dict,
                  status: str, detail: str | None) -> WebhookEvent:
    event = WebhookEvent(id=new_id("whk"), source=source, event_type=event_type,
                         payload=payload, status=status, detail=detail,
                         processed_at=datetime.now(timezone.utc)
                         if status != "PROCESSING" else None)
    db.add(event)
    db.commit()
    return event


def _resync_source(db: Session, source: str) -> int:
    resynced = 0
    for c in db.query(Connector).filter(Connector.type == source).all():
        _sync_connector(db, c)
        resynced += 1
    return resynced


def _summarize(event_type: str, result: dict) -> str:
    if event_type == "pull_request":
        return (f"PR #{result.get('pr_number')}: "
                f"{result.get('changed_policies', 0)} policy file(s), "
                f"review {result.get('suggested_review', 'n/a')}")
    changed = result.get("changed_policies")
    if changed is not None:
        return (f"{changed} policy file(s) changed across "
                f"{result.get('matched_connectors', 0)} connector(s)")
    return f"resynced {result.get('resynced', 0)} connector(s)"


@router.get("/webhooks/events")
def webhook_events(status: str | None = None,
                   db: Session = Depends(get_db)) -> dict:
    query = db.query(WebhookEvent)
    if status:
        query = query.filter(WebhookEvent.status == status.upper())
    rows = query.order_by(WebhookEvent.received_at.desc()).limit(100).all()
    return {"items": [webhook_to_dict(w) for w in rows], "total": len(rows)}


@router.delete("/connectors/{connector_id}", status_code=204)
def delete_connector(connector_id: str, db: Session = Depends(get_db)):
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, f"Connector {connector_id} not found")
    db.delete(connector)
    db.commit()
    return None

@router.patch("/connectors/{connector_id}")
def update_connector(connector_id: str, body: dict, db: Session = Depends(get_db)) -> dict:
    connector = db.get(Connector, connector_id)
    if not connector:
        raise HTTPException(404, f"Connector {connector_id} not found")
    if "name" in body:
        connector.name = body["name"]
    if "config" in body:
        connector.config = body["config"]
    db.commit()
    return connector_to_dict(connector)

