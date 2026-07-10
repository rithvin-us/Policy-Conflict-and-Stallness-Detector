"""Findings endpoints: conflicts, redundancies, staleness, review queue."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_engine import types as T
from app.core.db import get_db
from app.explainability import explain_conflict
from app.models import Conflict, Policy, StalenessFinding
from app.schemas import conflict_to_dict, staleness_to_dict

router = APIRouter()

_REDUNDANT = (T.REDUNDANCY, T.PARTIAL_REDUNDANCY)
_SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _rebuild_engine_conflict(c: Conflict):
    """Reconstruct the engine Conflict dataclass from an ORM row for the
    explainability builder (which expects the dataclass shape)."""
    from app.ai_engine.types import Conflict as EC, Evidence
    ev = c.evidence or {}
    return EC(
        id=c.id, policy_a_id=c.policy_a_id, policy_b_id=c.policy_b_id,
        obligation_a_id=c.obligation_a_id, obligation_b_id=c.obligation_b_id,
        conflict_type=c.conflict_type, severity=c.severity,
        explanation=c.explanation,
        evidence=Evidence(a=ev.get("a", {}), b=ev.get("b", {}),
                          trigger_terms=ev.get("trigger_terms", [])),
        confidence=c.confidence, scope_analysis=c.scope_analysis,
        resolution_suggestion=c.resolution_suggestion,
        compliance_impact=c.compliance_impact or [],
    )


@router.get("/conflicts")
def list_conflicts(type: str | None = None, severity: str | None = None,
                   policy_id: str | None = None,
                   db: Session = Depends(get_db)) -> dict:
    query = db.query(Conflict).filter(Conflict.conflict_type.notin_(_REDUNDANT))
    if type:
        query = query.filter(Conflict.conflict_type == type.upper())
    if severity:
        query = query.filter(Conflict.severity == severity.upper())
    if policy_id:
        query = query.filter((Conflict.policy_a_id == policy_id) |
                             (Conflict.policy_b_id == policy_id))
    rows = sorted(query.all(), key=lambda c: (_SEV_ORDER.get(c.severity, 3), -c.risk))
    return {"items": [conflict_to_dict(c) for c in rows], "total": len(rows)}


@router.get("/conflicts/{conflict_id}")
def get_conflict(conflict_id: str, db: Session = Depends(get_db)) -> dict:
    c = db.get(Conflict, conflict_id)
    if not c:
        raise HTTPException(404, f"Conflict {conflict_id} not found")
    data = conflict_to_dict(c)
    data["explanation_payload"] = explain_conflict(_rebuild_engine_conflict(c))
    titles = {p.id: p.title for p in db.query(Policy).all()}
    data["policy_a_title"] = titles.get(c.policy_a_id)
    data["policy_b_title"] = titles.get(c.policy_b_id)
    return data


@router.get("/redundancies")
def list_redundancies(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Conflict).filter(Conflict.conflict_type.in_(_REDUNDANT)).all()
    rows.sort(key=lambda c: -c.risk)
    return {"items": [conflict_to_dict(c) for c in rows], "total": len(rows)}


@router.get("/staleness")
def list_staleness(severity: str | None = None,
                   db: Session = Depends(get_db)) -> dict:
    query = db.query(StalenessFinding)
    if severity:
        query = query.filter(StalenessFinding.severity == severity.upper())
    rows = sorted(query.all(), key=lambda s: (_SEV_ORDER.get(s.severity, 3), -s.risk))
    return {"items": [staleness_to_dict(s) for s in rows], "total": len(rows)}


@router.get("/review-queue")
def review_queue(db: Session = Depends(get_db)) -> dict:
    titles = {p.id: p.title for p in db.query(Policy).all()}
    items = []
    for c in db.query(Conflict).all():
        items.append({
            "id": c.id, "kind": "CONFLICT", "severity": c.severity,
            "confidence": c.confidence, "risk": c.risk,
            "title": f"{c.conflict_type} — {titles.get(c.policy_a_id, c.policy_a_id)} "
                     f"↔ {titles.get(c.policy_b_id, c.policy_b_id)}",
            "policies": [c.policy_a_id, c.policy_b_id],
            "summary": c.explanation,
        })
    for s in db.query(StalenessFinding).all():
        items.append({
            "id": s.id, "kind": "STALE", "severity": s.severity,
            "confidence": 0.95, "risk": s.risk,
            "title": f"{s.stale_reason} — {titles.get(s.policy_id, s.policy_id)}",
            "policies": [s.policy_id],
            "summary": "; ".join(s.evidence or []),
        })
    items.sort(key=lambda i: (-i["risk"], _SEV_ORDER.get(i["severity"], 3)))
    return {"items": items, "total": len(items)}
