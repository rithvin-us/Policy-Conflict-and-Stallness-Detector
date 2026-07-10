"""Aggregate every resource router under the API prefix."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import analysis, findings, graph, policies, sources, system

api_router = APIRouter()
api_router.include_router(system.router, tags=["system"])
api_router.include_router(policies.router, tags=["policies"])
api_router.include_router(findings.router, tags=["findings"])
api_router.include_router(graph.router, tags=["graph"])
api_router.include_router(sources.router, tags=["connectors", "webhooks"])
api_router.include_router(analysis.router, tags=["analysis", "reports"])
