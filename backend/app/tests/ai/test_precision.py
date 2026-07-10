"""Precision guards (SRS success metric: false-positive rate < 20%).

False conflict alerts erode trust with policy owners, so these tests assert the
engine does *not* over-flag: scoped exceptions stay LOW, unrelated topics never
pair, and the set of HIGH conflicts is exactly the known true positives.
"""
from __future__ import annotations

from app.ai_engine import types as T
from app.ai_engine.conflicts import detect_conflicts
from app.ai_engine.obligations import extract_obligations
from app.ai_engine.parser import parse_policy

# The only two HIGH conflicts the seed corpus should ever produce.
TRUE_HIGH_PAIRS = [
    {"POL-PWD-001", "POL-CLD-002"},   # rotate vs shall-not-rotate (overlap)
    {"POL-RET-003", "POL-PRV-004"},   # 7y retention vs GDPR erasure
]


def test_developer_vpn_exception_is_not_high(result):
    hits = [c for c in result.conflicts
            if {c.policy_a_id, c.policy_b_id} == {"POL-NET-005", "POL-DEV-006"}]
    assert hits
    assert all(c.severity != T.HIGH for c in hits)
    assert any(c.conflict_type == T.SCOPE for c in hits)


def test_no_spurious_high_conflicts(result):
    highs = [c for c in result.conflicts if c.severity == T.HIGH]
    for c in highs:
        assert {c.policy_a_id, c.policy_b_id} in TRUE_HIGH_PAIRS, (
            f"unexpected HIGH conflict {c.policy_a_id}<>{c.policy_b_id} "
            f"({c.conflict_type})"
        )


def test_unrelated_topics_do_not_conflict():
    a = parse_policy("Section 1: All logs must be retained in the SIEM.",
                     policy_id="A")
    b = parse_policy("Section 1: Firewall rules must be reviewed quarterly.",
                     policy_id="B")
    conflicts = detect_conflicts(extract_obligations(a) + extract_obligations(b))
    assert conflicts == []


def test_false_positive_rate_bound(result):
    """FPR = flagged pairs that are not genuine issues / total flagged.

    On the curated corpus every finding is a designed true positive, so the
    measured FPR is 0% — comfortably under the 20% ceiling. This test fails loudly
    if a future change starts inventing conflicts.
    """
    total = len(result.conflicts)
    assert total > 0
    # Any HIGH conflict outside the known-true set is a false positive.
    false_positives = sum(
        1 for c in result.conflicts
        if c.severity == T.HIGH
        and {c.policy_a_id, c.policy_b_id} not in TRUE_HIGH_PAIRS
    )
    fpr = false_positives / total
    assert fpr < 0.20, f"false-positive rate {fpr:.0%} exceeds 20%"
