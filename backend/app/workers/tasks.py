"""Async task definitions and a synchronous dispatch fallback.

``dispatch(name, *args)`` runs the task via Celery when configured, otherwise runs
it inline — so callers never branch on whether a broker exists.
"""
from __future__ import annotations

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.services.analysis import run_analysis

from .celery_app import celery_app

log = get_logger("workers")


def _run_analysis_job(policy_ids=None) -> str:
    db = SessionLocal()
    try:
        run = run_analysis(db, policy_ids=policy_ids)
        return run.id
    finally:
        db.close()


if celery_app is not None:  # pragma: no cover - requires broker
    analyze_task = celery_app.task(name="analyze")( _run_analysis_job)
else:
    analyze_task = None


def dispatch_analysis(policy_ids=None) -> str:
    if analyze_task is not None:  # pragma: no cover - requires broker
        return analyze_task.delay(policy_ids).id
    return _run_analysis_job(policy_ids)
