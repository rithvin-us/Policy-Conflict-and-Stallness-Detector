"""Registered-but-unimplemented connectors.

Each remaining source type in the data dictionary is a real subclass so it appears
in the connector registry, the ``/meta`` catalogue, and the UI's "add source"
list — but reports ``NOT_CONFIGURED`` until implemented (see roadmap). Wiring one
up means giving it real ``verify``/``list``/``fetch`` bodies; nothing else changes.
"""
from __future__ import annotations

from .base import NOT_CONFIGURED, BaseConnector, RawPolicy


class _StubConnector(BaseConnector):
    def verify(self) -> str:
        return NOT_CONFIGURED

    def list_policies(self) -> list[dict[str, str]]:
        return []

    def fetch(self, ref: dict[str, str]) -> RawPolicy:  # pragma: no cover
        raise NotImplementedError(f"{self.type} connector is not implemented yet")


class GitLabConnector(_StubConnector):
    type = "GITLAB"

    def supports_webhooks(self) -> bool:
        return True


class BitbucketConnector(_StubConnector):
    type = "BITBUCKET"

    def supports_webhooks(self) -> bool:
        return True


class GoogleDriveConnector(_StubConnector):
    type = "GOOGLE_DRIVE"


class OneDriveConnector(_StubConnector):
    type = "ONEDRIVE"


class SharePointConnector(_StubConnector):
    type = "SHAREPOINT"


class SlackConnector(_StubConnector):
    type = "SLACK"


class TeamsConnector(_StubConnector):
    type = "TEAMS"
