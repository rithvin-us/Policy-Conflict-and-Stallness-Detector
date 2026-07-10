"""Connector and webhook endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.connectors.base import ERROR, SYNCING
from app.connectors.manager import ConnectorManager, connector_manager
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
from app.services.analysis import run_analysis
from app.services.ingestion import ingest_raw_policy

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
    return {"id": new_id("whk"), "secret_ref": secret_ref,
            "url": f"/api/v1/webhooks/{connector.type.lower()}",
            "event_types": body.event_types}


def _affected_paths(payload: dict) -> list[str]:
    paths: list[str] = []
    for commit in payload.get("commits", []):
        for key in ("modified", "added", "removed"):
            paths.extend(commit.get(key, []) or [])
    return sorted(set(paths))


@router.post("/webhooks/{connector}")
async def ingest_webhook(connector: str, request: Request,
                         db: Session = Depends(get_db)) -> dict:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    source = connector.upper()
    event_type = request.headers.get("X-GitHub-Event", payload.get("event_type", "push"))

    event = WebhookEvent(id=new_id("whk"), source=source, event_type=event_type,
                         payload=payload, status="PROCESSING")
    db.add(event)
    db.commit()

    affected = _affected_paths(payload)
    # Re-sync every connector of this source type (idempotent by content hash).
    resynced = 0
    for c in db.query(Connector).filter(Connector.type == source).all():
        _sync_connector(db, c)
        resynced += 1

    event.status = "PROCESSED"
    event.processed_at = datetime.now(timezone.utc)
    event.detail = f"Re-synced {resynced} connector(s); {len(affected)} paths changed"
    db.commit()
    return {"received": True, "event_id": event.id, "affected_paths": affected}


@router.get("/webhooks/events")
def webhook_events(status: str | None = None,
                   db: Session = Depends(get_db)) -> dict:
    query = db.query(WebhookEvent)
    if status:
        query = query.filter(WebhookEvent.status == status.upper())
    rows = query.order_by(WebhookEvent.received_at.desc()).limit(100).all()
    return {"items": [webhook_to_dict(w) for w in rows], "total": len(rows)}
