"""Conflict detection rate + correct severity classification.

Success metric: conflict detection rate > 75% on the labeled expectation set.
"""
from __future__ import annotations

from app.ai_engine import types as T
from app.ai_engine.conflicts import detect_conflicts
from app.ai_engine.obligations import extract_obligations
from app.ai_engine.parser import parse_policy

# Ground-truth conflicts we expect the engine to surface on the seed corpus.
# (policy_a, policy_b, expected_type, expected_severity)
EXPECTED = [
    ("POL-PWD-001", "POL-CLD-002", T.DIRECT, T.HIGH),      # rotate vs shall-not-rotate
    ("POL-RET-003", "POL-PRV-004", T.TEMPORAL, T.MEDIUM),  # retain 7y vs delete 30d
    ("POL-NET-005", "POL-DEV-006", T.SCOPE, T.LOW),        # VPN vs developer bypass
]


def _match(conflicts, a, b):
    pair = {a, b}
    return [c for c in conflicts if {c.policy_a_id, c.policy_b_id} == pair]


def test_password_cloud_is_high_direct(result):
    hits = _match(result.conflicts, "POL-PWD-001", "POL-CLD-002")
    assert any(c.conflict_type == T.DIRECT and c.severity == T.HIGH for c in hits)
    top = next(c for c in hits if c.conflict_type == T.DIRECT)
    assert "rotate" in top.evidence.trigger_terms
    assert top.compliance_impact  # carries ISO/NIST refs
    assert top.resolution_suggestion


def test_detection_rate(result):
    found = 0
    for a, b, _type, _sev in EXPECTED:
        if _match(result.conflicts, a, b):
            found += 1
    rate = found / len(EXPECTED)
    assert rate >= 0.75, f"conflict detection rate {rate:.0%} below 75%"


def test_severity_classification(result):
    for a, b, exp_type, exp_sev in EXPECTED:
        hits = _match(result.conflicts, a, b)
        assert hits, f"no finding for {a}<>{b}"
        assert any(c.severity == exp_sev for c in hits), (
            f"{a}<>{b} expected {exp_sev}, got {[c.severity for c in hits]}"
        )


def test_ps_worked_example_verbatim():
    """The brief's exact password/cloud excerpts must yield a HIGH conflict."""
    pwd = parse_policy(
        "--- Password Policy (v2.1, Last Reviewed: 2021-08-15) ---\n"
        "Section 3.1: All employees must rotate their passwords every 90 days.",
        policy_id="PWD",
    )
    cloud = parse_policy(
        "--- Cloud Security Policy (v1.0, Last Reviewed: 2024-11-20) ---\n"
        "Section 5.2: Password rotation shall not be required for cloud systems; "
        "MFA replaces the need for periodic credential changes.",
        policy_id="CLOUD",
    )
    obs = extract_obligations(pwd) + extract_obligations(cloud)
    conflicts = detect_conflicts(obs)
    assert conflicts
    top = conflicts[0]
    assert top.severity == T.HIGH
    assert top.conflict_type == T.DIRECT
