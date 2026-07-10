"""First-boot seeding.

If the database has no policies, register a Local Folder connector pointed at the
sample corpus, sync it, and run the first analysis — so the dashboard is populated
and meaningful the moment the stack comes up (no dead demo pages, per the brief).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.connectors.base import CONNECTED
from app.connectors.local_folder import LocalFolderConnector
from app.core.config import settings
from app.core.ids import new_id
from app.core.logging import get_logger
from app.models import Connector, Policy
from app.services.analysis import run_analysis
from app.services.ingestion import ingest_raw_policy

log = get_logger("seed")


def seed_if_empty(db: Session) -> None:
    if db.query(Policy).count() > 0:
        return
    if not settings.SEED_ON_STARTUP:
        return

    seed_dir = Path(settings.SEED_POLICY_DIR)
    if not seed_dir.is_dir():
        log.warning("seed dir missing", extra={"extra_fields": {"dir": str(seed_dir)}})
        return

    connector = Connector(
        id=new_id("con"), type="LOCAL_FOLDER", name="Seed Policy Library",
        status=CONNECTED, config={"path": str(seed_dir)},
        last_sync=datetime.now(timezone.utc),
    )
    db.add(connector)

    conn = LocalFolderConnector(config={"path": str(seed_dir)})
    for raw in conn.collect():
        ingest_raw_policy(db, raw)
    db.commit()

    run_analysis(db)
    log.info("seed complete",
             extra={"extra_fields": {"policies": db.query(Policy).count()}})
