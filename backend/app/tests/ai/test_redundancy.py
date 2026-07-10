"""Redundancy / partial-overlap detection (SRS success metric: > 70%)."""
from __future__ import annotations

from app.ai_engine import types as T

_REDUNDANT = {T.REDUNDANCY, T.PARTIAL_REDUNDANCY}


def test_encryption_redundancy_detected(result):
    reds = [c for c in result.conflicts if c.conflict_type in _REDUNDANT]
    assert reds, "expected at least one redundancy finding"
    enc = [c for c in reds if {c.policy_a_id, c.policy_b_id} ==
           {"POL-CLD-002", "POL-NET-005"}]
    assert enc, "expected encryption redundancy between cloud & network policies"


def test_redundancy_is_low_severity(result):
    for c in result.conflicts:
        if c.conflict_type in _REDUNDANT:
            assert c.severity == T.LOW
            assert 0.0 < c.confidence <= 1.0
