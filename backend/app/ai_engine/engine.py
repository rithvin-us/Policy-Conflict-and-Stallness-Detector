"""Top-level orchestration of the policy intelligence pipeline.

One call, ``analyze_corpus``, runs the full deterministic pipeline described in
``docs/architecture.md`` §3 and returns an :class:`AnalysisResult`. The backend
analysis service and the AI evaluation tests both go through this single entry
point, guaranteeing the API and the tests exercise identical logic.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from app.risk_scoring import governance_score, policy_health

from .conflicts import detect_conflicts
from .obligations import extract_obligations
from .staleness import detect_staleness
from .types import AnalysisResult, PolicyInput


def analyze_corpus(policies: list[PolicyInput],
                   as_of: Optional[date] = None) -> AnalysisResult:
    as_of = as_of or date.today()

    obligations = []
    for p in policies:
        obligations.extend(extract_obligations(p))

    conflicts = detect_conflicts(obligations, policies)

    staleness = []
    for p in policies:
        staleness.extend(detect_staleness(p, as_of=as_of))

    health = {p.id: policy_health(p.id, conflicts, staleness) for p in policies}
    governance = governance_score(policies, obligations, conflicts, staleness, as_of)

    return AnalysisResult(
        obligations=obligations,
        conflicts=conflicts,
        staleness=staleness,
        policy_health=health,
        governance=governance,
    )
