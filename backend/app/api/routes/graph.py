"""Graph endpoint — React-Flow-ready policy / obligation graph."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.graph_builder import build_graph
from app.models import Conflict, Obligation, Policy

router = APIRouter()


@router.get("/graph")
def get_graph(mode: str = "POLICY", topic: str | None = None,
              policy_id: str | None = None, db: Session = Depends(get_db)) -> dict:
    policies = db.query(Policy).all()
    obligations = db.query(Obligation).all()
    conflicts = db.query(Conflict).all()
    health = {p.id: p.health_score for p in policies}
    # ORM rows are duck-type compatible with the engine dataclasses the builder
    # reads (same attribute names), so no conversion is needed.
    return build_graph(mode, policies, obligations, conflicts, health,
                       topic=topic.upper() if topic else None, policy_id=policy_id)
