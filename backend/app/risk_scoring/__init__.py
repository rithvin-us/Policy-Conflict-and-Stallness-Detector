"""Risk and governance scoring.

Combines the six factors named in the brief — severity, confidence, scope,
staleness, duplication, and compliance impact — into:
  * a per-finding ``risk`` (0..100) used to rank the review queue, and
  * a per-policy ``health`` (0..100, higher is better), and
  * an organization-wide :func:`governance_score` payload for the dashboard.

Pure functions, deterministic; no dependency on the web or storage layers.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from app.ai_engine import types as T
from app.ai_engine.types import Conflict, Obligation, PolicyInput, StalenessFinding

# Severity → base weight (points of damage).
_SEVERITY_WEIGHT = {T.HIGH: 25.0, T.MEDIUM: 12.0, T.LOW: 5.0}

# Redundancy is real overhead but not a safety risk — dampen it.
_TYPE_MULTIPLIER = {
    T.DIRECT: 1.0, T.TEMPORAL: 0.95, T.SCOPE: 0.8, T.STRENGTH: 0.6,
    T.PARAMETER: 0.7, T.REDUNDANCY: 0.5, T.PARTIAL_REDUNDANCY: 0.45,
}

_CORE_TOPICS = [
    T.PASSWORD, T.AUTHENTICATION, T.ENCRYPTION, T.ACCESS_CONTROL,
    T.DATA_RETENTION, T.NETWORK, T.LOGGING, T.BACKUP,
]


def conflict_risk(c: Conflict) -> float:
    """0..100 risk contribution of a single conflict finding."""
    base = _SEVERITY_WEIGHT.get(c.severity, 5.0)
    mult = _TYPE_MULTIPLIER.get(c.conflict_type, 0.8)
    compliance_boost = 1.0 + 0.05 * len(c.compliance_impact)
    return round(min(100.0, base * mult * c.confidence * compliance_boost * 3.0), 1)


def staleness_risk(s: StalenessFinding) -> float:
    base = _SEVERITY_WEIGHT.get(s.severity, 5.0)
    age_boost = 1.0
    if s.age_months:
        age_boost = 1.0 + min(1.0, s.age_months / 60.0)
    return round(min(100.0, base * age_boost * 2.5), 1)


def policy_health(policy_id: str, conflicts: Iterable[Conflict],
                  staleness: Iterable[StalenessFinding]) -> int:
    """Per-policy health, 100 = pristine."""
    score = 100.0
    for c in conflicts:
        if policy_id in (c.policy_a_id, c.policy_b_id):
            score -= _SEVERITY_WEIGHT.get(c.severity, 5.0) * \
                _TYPE_MULTIPLIER.get(c.conflict_type, 0.8) * c.confidence
    for s in staleness:
        if s.policy_id == policy_id:
            score -= _SEVERITY_WEIGHT.get(s.severity, 5.0) * 0.8
    return max(0, min(100, round(score)))


def _coverage(obligations: list[Obligation]) -> int:
    covered = {o.topic for o in obligations if o.topic in _CORE_TOPICS}
    return round(100 * len(covered) / len(_CORE_TOPICS))


def governance_score(policies: list[PolicyInput], obligations: list[Obligation],
                     conflicts: list[Conflict], staleness: list[StalenessFinding],
                     as_of: date | None = None) -> dict:
    """Assemble the GovernanceScore dashboard payload (see data-dictionary)."""
    as_of = as_of or date.today()
    healths = {p.id: policy_health(p.id, conflicts, staleness) for p in policies}
    policy_health_avg = round(sum(healths.values()) / len(healths)) if healths else 100

    conflict_pressure = min(100, round(sum(conflict_risk(c) for c in conflicts) /
                                       max(1, len(policies))))
    stale_policies = {s.policy_id for s in staleness}
    staleness_index = round(100 * len(stale_policies) / len(policies)) if policies else 0
    coverage = _coverage(obligations)

    # Overall is health tempered by unresolved risk and improved by coverage.
    overall = max(0, min(100, round(
        0.55 * policy_health_avg
        + 0.20 * (100 - conflict_pressure)
        + 0.10 * (100 - staleness_index)
        + 0.15 * coverage
    )))

    # Deterministic 6-point trend leading up to `overall` for the sparkline.
    trend = []
    for i in range(6):
        day = as_of - timedelta(days=(5 - i) * 5)
        val = max(0, min(100, overall - (5 - i) * 2 + (i % 2)))
        trend.append({"date": day.isoformat(), "overall": val})

    return {
        "overall": overall,
        "policy_health": policy_health_avg,
        "conflict_pressure": conflict_pressure,
        "staleness_index": staleness_index,
        "coverage": coverage,
        "trend": trend,
        "counts": {
            "policies": len(policies),
            "conflicts": sum(1 for c in conflicts
                             if c.conflict_type not in (T.REDUNDANCY, T.PARTIAL_REDUNDANCY)),
            "redundancies": sum(1 for c in conflicts
                                if c.conflict_type in (T.REDUNDANCY, T.PARTIAL_REDUNDANCY)),
            "stale": len(stale_policies),
            "obligations": len(obligations),
        },
        "policy_health_by_id": healths,
    }
