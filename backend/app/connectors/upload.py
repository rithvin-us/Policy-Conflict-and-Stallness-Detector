"""Upload connector — the passive source for manually uploaded policies.

Uploads enter through ``POST /api/v1/policies/upload`` rather than a sync, so this
connector holds no remote state; it exists so manual uploads share the same
Connector accounting and health surface as automated sources.
"""
from __future__ import annotations

from .base import CONNECTED, BaseConnector, RawPolicy


class UploadConnector(BaseConnector):
    type = "UPLOAD"

    def verify(self) -> str:
        return CONNECTED

    def list_policies(self) -> list[dict[str, str]]:
        return []

    def fetch(self, ref: dict[str, str]) -> RawPolicy:  # pragma: no cover
        raise NotImplementedError("Upload policies are ingested directly via the API")
