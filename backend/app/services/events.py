"""In-process event broker for live dashboard updates (Server-Sent Events).

A tiny publish/subscribe hub: request handlers and background sync call
:func:`publish` with a small JSON-able dict; the SSE endpoint holds one
subscriber queue per connected browser and streams events as they arrive.

Zero dependencies and single-process by design (matches the localhost + single
uvicorn worker deployment). For multi-worker production, swap the queue set for
Redis pub/sub behind this same ``publish``/``subscribe`` surface — nothing else
changes.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from app.core.logging import get_logger

log = get_logger("events")

# Each connected client owns one bounded queue. A bound prevents a slow/dead
# client from growing memory without limit — overflow drops the oldest event.
_MAXSIZE = 100
_subscribers: set[asyncio.Queue] = set()


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=_MAXSIZE)
    _subscribers.add(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    _subscribers.discard(q)


def publish(event_type: str, data: dict[str, Any] | None = None) -> None:
    """Fan a governance event out to every connected dashboard.

    Safe to call from sync code with no running loop (tests, worker threads):
    when there are no subscribers or no loop, it is a silent no-op.
    """
    payload = json.dumps({"type": event_type, "data": data or {}})
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:  # drop oldest, keep newest
            try:
                q.get_nowait()
                q.put_nowait(payload)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass
    if _subscribers:
        log.info("event published", extra={"extra_fields": {
            "type": event_type, "subscribers": len(_subscribers)}})


def subscriber_count() -> int:
    return len(_subscribers)
