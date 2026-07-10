"""Connector registry + manager.

Single source of truth for which connector types exist and how to instantiate one
from a stored :class:`~app.models.Connector` row.
"""
from __future__ import annotations

from app.models import Connector as ConnectorModel

from .base import BaseConnector
from .github import GitHubConnector
from .local_folder import LocalFolderConnector
from .stubs import (
    BitbucketConnector,
    GitLabConnector,
    GoogleDriveConnector,
    OneDriveConnector,
    SharePointConnector,
    SlackConnector,
    TeamsConnector,
)
from .upload import UploadConnector

_REGISTRY: dict[str, type[BaseConnector]] = {
    LocalFolderConnector.type: LocalFolderConnector,
    GitHubConnector.type: GitHubConnector,
    UploadConnector.type: UploadConnector,
    GitLabConnector.type: GitLabConnector,
    BitbucketConnector.type: BitbucketConnector,
    GoogleDriveConnector.type: GoogleDriveConnector,
    OneDriveConnector.type: OneDriveConnector,
    SharePointConnector.type: SharePointConnector,
    SlackConnector.type: SlackConnector,
    TeamsConnector.type: TeamsConnector,
}


class ConnectorManager:
    @staticmethod
    def types() -> list[str]:
        return list(_REGISTRY.keys())

    @staticmethod
    def register(connector_type: str, cls: type[BaseConnector]) -> None:
        _REGISTRY[connector_type] = cls

    @staticmethod
    def is_known(connector_type: str) -> bool:
        return connector_type in _REGISTRY

    @staticmethod
    def instantiate(model: ConnectorModel) -> BaseConnector:
        cls = _REGISTRY.get(model.type)
        if cls is None:
            raise ValueError(f"Unknown connector type: {model.type}")
        return cls(config=model.config or {})


connector_manager = ConnectorManager()
