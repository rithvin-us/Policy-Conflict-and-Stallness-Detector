"""System endpoints: meta, dashboard overview, timeline, compliance coverage."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai_engine import types as T
from app.ai_engine.lexicon import COMPLIANCE_BY_TOPIC, FRAMEWORK_CLAUSES
from app.connectors.manager import ConnectorManager
from app.core.db import get_db
from app.models import Conflict, Obligation, Policy, StalenessFinding, TimelineEvent
from app.schemas import timeline_to_dict
from app.services.analysis import latest_run

router = APIRouter()

_TOPICS = [T.PASSWORD, T.AUTHENTICATION, T.ENCRYPTION, T.ACCESS_CONTROL,
           T.DATA_RETENTION, T.DATA_CLASSIFICATION, T.NETWORK, T.LOGGING,
           T.BACKUP, T.INCIDENT_RESPONSE]
_CONFLICT_TYPES = [T.DIRECT, T.TEMPORAL, T.SCOPE, T.STRENGTH, T.PARAMETER,
                   T.REDUNDANCY, T.PARTIAL_REDUNDANCY]


@router.get("/meta")
def meta() -> dict:
    return {
        "topics": _TOPICS,
        "conflict_types": _CONFLICT_TYPES,
        "severities": [T.HIGH, T.MEDIUM, T.LOW],
        "connectors": ConnectorManager.types(),
        "stale_reasons": [T.REVIEW_OVERDUE, T.DEPRECATED_TECH,
                          T.SUPERSEDED_STANDARD, T.ORPHANED_OWNER],
    }


@router.get("/dashboard/overview")
def dashboard_overview(db: Session = Depends(get_db)) -> dict:
    run = latest_run(db)
    if run and run.governance:
        return run.governance
    # Empty-state fallback so the UI always has a shape to render.
    return {
        "overall": 100, "policy_health": 100, "conflict_pressure": 0,
        "staleness_index": 0, "coverage": 0, "trend": [],
        "counts": {"policies": 0, "conflicts": 0, "redundancies": 0,
                   "stale": 0, "obligations": 0},
        "policy_health_by_id": {},
    }


@router.get("/timeline")
def timeline(limit: int = 40, db: Session = Depends(get_db)) -> dict:
    events = (db.query(TimelineEvent)
              .order_by(TimelineEvent.at.desc()).limit(limit).all())
    return {"items": [timeline_to_dict(e) for e in events]}


@router.get("/compliance/coverage")
def compliance_coverage(db: Session = Depends(get_db)) -> dict:
    obligations = db.query(Obligation).all()
    conflicts = db.query(Conflict).all()

    # Which framework clauses are touched by at least one obligation's topic.
    touched: dict[str, list[str]] = {}
    for o in obligations:
        for clause in COMPLIANCE_BY_TOPIC.get(o.topic, []):
            touched.setdefault(clause, [])
            if o.policy_id not in touched[clause]:
                touched[clause].append(o.policy_id)

    finding_clauses: dict[str, int] = {}
    for c in conflicts:
        for clause in (c.compliance_impact or []):
            finding_clauses[clause] = finding_clauses.get(clause, 0) + 1

    frameworks = []
    for framework, clauses in FRAMEWORK_CLAUSES.items():
        clause_rows = []
        for clause, title in clauses.items():
            key = f"{framework} {clause}" if not clause.startswith(("A.", "Art.")) \
                else f"{framework} {clause}"
            # Match against the short forms used in COMPLIANCE_BY_TOPIC.
            covered_policies = _match_clause(touched, framework, clause)
            clause_rows.append({
                "clause": clause,
                "title": title,
                "covered": bool(covered_policies),
                "policies": covered_policies,
                "findings": _match_clause_count(finding_clauses, framework, clause),
            })
        frameworks.append({"framework": framework, "clauses": clause_rows})

    covered_topics = {o.topic for o in obligations}
    gaps = [{"topic": t, "reason": "No policy defines any obligation for this topic"}
            for t in _TOPICS if t not in covered_topics]

    return {"frameworks": frameworks, "gaps": gaps}


def _match_clause(touched: dict[str, list[str]], framework: str, clause: str) -> list[str]:
    for key, policies in touched.items():
        if framework.split()[0] in key and clause in key:
            return policies
    return []


def _match_clause_count(counts: dict[str, int], framework: str, clause: str) -> int:
    total = 0
    for key, n in counts.items():
        if framework.split()[0] in key and clause in key:
            total += n
    return total
