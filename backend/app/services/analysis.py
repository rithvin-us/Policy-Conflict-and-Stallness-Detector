"""Analysis orchestration.

Bridges persisted policies to the deterministic AI engine and writes the results
back. Analysis is always corpus-wide (conflicts and the governance score are
inherently cross-policy), so findings are recomputed atomically on every run —
guaranteeing the API never serves a half-updated graph.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ai_engine import analyze_corpus
from app.ai_engine.types import PolicyInput
from app.core.config import settings
from app.core.ids import new_id
from app.core.logging import get_logger
from app.models import (
    AnalysisRun,
    Conflict,
    Obligation,
    Policy,
    StalenessFinding,
    TimelineEvent,
)
from app.risk_scoring import conflict_risk, staleness_risk

from .notify import notify_new_high

log = get_logger("analysis")


def _as_of() -> date:
    if settings.ANALYSIS_AS_OF:
        try:
            return datetime.strptime(settings.ANALYSIS_AS_OF, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


def _to_input(p: Policy) -> PolicyInput:
    return PolicyInput(
        id=p.id,
        title=p.title,
        raw_text=p.raw_text,
        owner=p.owner or "",
        author=p.author,
        version=p.version,
        status=p.status,
        source=p.source,
        last_reviewed=p.last_reviewed,
        created_at=p.created_at,
        tags=p.tags or [],
    )


def run_analysis(db: Session, policy_ids: list[str] | None = None) -> AnalysisRun:
    policies = db.query(Policy).all()
    if not policies:
        run = AnalysisRun(id=new_id("run"), governance={}, counts={})
        db.add(run)
        db.commit()
        return run

    inputs = [_to_input(p) for p in policies]
    result = analyze_corpus(inputs, as_of=_as_of())

    # Atomic replace of derived data.
    db.execute(delete(Obligation))
    db.execute(delete(Conflict))
    db.execute(delete(StalenessFinding))

    for o in result.obligations:
        db.add(Obligation(
            id=o.id, policy_id=o.policy_id, section=o.section, topic=o.topic,
            action=o.action, scope=o.scope.to_dict(), strength=o.strength,
            polarity=o.polarity, parameters=o.parameters,
            evidence_text=o.evidence_text, confidence=o.confidence,
        ))

    for c in result.conflicts:
        db.add(Conflict(
            id=c.id, policy_a_id=c.policy_a_id, policy_b_id=c.policy_b_id,
            obligation_a_id=c.obligation_a_id, obligation_b_id=c.obligation_b_id,
            conflict_type=c.conflict_type, severity=c.severity,
            explanation=c.explanation, evidence=c.evidence.to_dict(),
            confidence=c.confidence, scope_analysis=c.scope_analysis,
            resolution_suggestion=c.resolution_suggestion,
            compliance_impact=c.compliance_impact, risk=conflict_risk(c),
        ))

    for s in result.staleness:
        db.add(StalenessFinding(
            id=s.id, policy_id=s.policy_id, stale_reason=s.stale_reason,
            severity=s.severity, evidence=s.evidence,
            recommendation=s.recommendation, age_months=s.age_months,
            risk=staleness_risk(s),
        ))

    for p in policies:
        p.health_score = result.policy_health.get(p.id, 100)

    counts = result.governance.get("counts", {})
    run = AnalysisRun(id=new_id("run"), governance=result.governance, counts=counts)
    db.add(run)
    db.add(TimelineEvent(
        id=new_id("tl"), kind="ANALYZED", policy_id=None,
        title="Corpus analysis complete",
        detail=f"{counts.get('conflicts', 0)} conflicts, "
               f"{counts.get('stale', 0)} stale policies",
    ))
    db.commit()

    high = [c for c in result.conflicts if c.severity == "HIGH"]
    notify_new_high(db, high)

    log.info("analysis complete", extra={"extra_fields": {
        "policies": len(policies), "conflicts": counts.get("conflicts"),
        "overall": result.governance.get("overall")}})
    return run


def latest_run(db: Session) -> AnalysisRun | None:
    return db.query(AnalysisRun).order_by(AnalysisRun.created_at.desc()).first()
