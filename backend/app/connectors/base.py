"""Connector SPI.

Every policy source implements :class:`BaseConnector`. Ingestion, analysis, and
the API depend only on this interface, so adding GitLab/Drive/SharePoint later is
a pure plug-in (subclass + register) with no changes elsewhere.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RawPolicy:
    """A fetched policy document, pre-ingestion."""

    path: str                      # stable identifier within the source
    name: str                      # display/file name
    text: str                      # verbatim content
    meta: dict[str, Any] = field(default_factory=dict)


# ConnectorStatus values (mirror data-dictionary).
CONNECTED = "CONNECTED"
SYNCING = "SYNCING"
ERROR = "ERROR"
DISCONNECTED = "DISCONNECTED"
NOT_CONFIGURED = "NOT_CONFIGURED"


class BaseConnector(abc.ABC):
    #: Connector type key (matches ``ConnectorType`` in the data dictionary).
    type: str = "BASE"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abc.abstractmethod
    def verify(self) -> str:
        """Return a ConnectorStatus indicating whether the source is reachable."""

    @abc.abstractmethod
    def list_policies(self) -> list[dict[str, str]]:
        """Return lightweight refs ``[{path, name}]`` without fetching bodies."""

    @abc.abstractmethod
    def fetch(self, ref: dict[str, str]) -> RawPolicy:
        """Fetch a single policy body for a ref returned by :meth:`list_policies`."""

    def supports_webhooks(self) -> bool:
        return False

    def collect(self) -> list[RawPolicy]:
        """Convenience: list + fetch everything. Used by the sync pipeline."""
        return [self.fetch(ref) for ref in self.list_policies()]
