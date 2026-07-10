"""Celery application (optional async execution).

Only used when ``USE_CELERY=1`` and a broker is reachable. The API always works
synchronously without Celery (SRS NFR-5); this exists so sync and notification
jobs can be offloaded in a production deployment with Redis.
"""
from __future__ import annotations

from app.core.config import settings

try:
    from celery import Celery
except ImportError:  # pragma: no cover - celery is optional
    Celery = None  # type: ignore


def make_celery():
    if Celery is None or not settings.REDIS_URL:
        return None
    app = Celery("policy_guardian", broker=settings.REDIS_URL,
                 backend=settings.REDIS_URL)
    app.conf.update(task_serializer="json", result_serializer="json",
                    accept_content=["json"], timezone="UTC", enable_utc=True)
    return app


celery_app = make_celery()
