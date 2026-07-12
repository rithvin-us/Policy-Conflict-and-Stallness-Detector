"""Policy endpoints: list, detail, upload, delete, obligations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.connectors.base import RawPolicy
from app.core.db import get_db
from app.models import Conflict, Obligation, Policy, PolicyVersion, StalenessFinding
from app.schemas import (
    PolicyUploadRequest,
    conflict_to_dict,
    obligation_to_dict,
    policy_to_dict,
    policy_version_to_dict,
    staleness_to_dict,
)
from app.services.analysis import run_analysis
from app.services.ingestion import ingest_raw_policy

router = APIRouter()


@router.get("/policies")
def list_policies(limit: int = 50, offset: int = 0, status: str | None = None,
                  topic: str | None = None, db: Session = Depends(get_db)) -> dict:
    query = db.query(Policy)
    if status:
        query = query.filter(Policy.status == status.upper())
    if topic:
        pids = {o.policy_id for o in
                db.query(Obligation).filter(Obligation.topic == topic.upper()).all()}
        query = query.filter(Policy.id.in_(pids or {"__none__"}))
    total = query.count()
    rows = query.order_by(Policy.health_score.asc()).offset(offset).limit(limit).all()
    return {"items": [policy_to_dict(p) for p in rows], "total": total}


@router.get("/policies/{policy_id}")
def get_policy(policy_id: str, db: Session = Depends(get_db)) -> dict:
    p = db.get(Policy, policy_id)
    if not p:
        raise HTTPException(404, f"Policy {policy_id} not found")
    obligations = db.query(Obligation).filter(Obligation.policy_id == policy_id).all()
    conflicts = db.query(Conflict).filter(
        (Conflict.policy_a_id == policy_id) | (Conflict.policy_b_id == policy_id)).all()
    stale = db.query(StalenessFinding).filter(
        StalenessFinding.policy_id == policy_id).all()
    data = policy_to_dict(p)
    data["obligations"] = [obligation_to_dict(o) for o in obligations]
    data["conflicts"] = [conflict_to_dict(c) for c in conflicts]
    data["staleness"] = [staleness_to_dict(s) for s in stale]
    return data


@router.get("/policies/{policy_id}/obligations")
def policy_obligations(policy_id: str, db: Session = Depends(get_db)) -> dict:
    if not db.get(Policy, policy_id):
        raise HTTPException(404, f"Policy {policy_id} not found")
    rows = db.query(Obligation).filter(Obligation.policy_id == policy_id).all()
    return {"items": [obligation_to_dict(o) for o in rows], "total": len(rows)}


@router.get("/policies/{policy_id}/versions")
def policy_versions(policy_id: str, db: Session = Depends(get_db)) -> dict:
    if not db.get(Policy, policy_id):
        raise HTTPException(404, f"Policy {policy_id} not found")
    rows = (db.query(PolicyVersion)
            .filter(PolicyVersion.policy_id == policy_id)
            .order_by(PolicyVersion.created_at.desc()).all())
    return {"items": [policy_version_to_dict(v) for v in rows], "total": len(rows)}


@router.get("/policies/{policy_id}/blast-radius")
def policy_blast_radius(policy_id: str, db: Session = Depends(get_db)) -> dict:
    if not db.get(Policy, policy_id):
        raise HTTPException(404, f"Policy {policy_id} not found")
    
    conflicts = db.query(Conflict).filter(
        (Conflict.policy_a_id == policy_id) | (Conflict.policy_b_id == policy_id)).all()
    
    related_policy_ids = set()
    potential_conflicts = 0
    impact = 0.0

    for c in conflicts:
        related_policy_ids.add(c.policy_a_id)
        related_policy_ids.add(c.policy_b_id)
        if c.severity == "HIGH":
            potential_conflicts += 1
            impact -= 2.0
        elif c.severity == "MEDIUM":
            impact -= 1.0
            
    related_policy_ids.discard(policy_id)
    
    affected_policies = []
    if related_policy_ids:
        related = db.query(Policy).filter(Policy.id.in_(related_policy_ids)).all()
        for r in related:
            affected_policies.append({"id": r.id, "title": r.title, "health_score": r.health_score})
            
    return {
        "root_policy_id": policy_id,
        "affected_policies": affected_policies,
        "potential_new_findings": potential_conflicts,
        "estimated_governance_impact": round(impact, 2)
    }


@router.post("/policies/upload", status_code=201)
def upload_policy(body: PolicyUploadRequest, db: Session = Depends(get_db)) -> dict:
    header = (f"--- {body.title} (v{body.version}) ---\n"
              if "---" not in body.raw_text else "")
    raw = RawPolicy(path=f"upload:{body.title}", name=body.title,
                    text=header + body.raw_text,
                    meta={"source": body.source})
    policy = ingest_raw_policy(db, raw)
    if body.owner:
        policy.owner = body.owner
    if body.tags:
        policy.tags = body.tags
    db.commit()
    run_analysis(db)          # re-analyze corpus so findings reflect the new policy
    db.refresh(policy)
    return policy_to_dict(policy)


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: str, db: Session = Depends(get_db)) -> dict:
    p = db.get(Policy, policy_id)
    if not p:
        raise HTTPException(404, f"Policy {policy_id} not found")
    db.delete(p)
    db.commit()
    run_analysis(db)
    return {"deleted": True, "id": policy_id}
