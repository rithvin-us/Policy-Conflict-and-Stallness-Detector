"""Staleness detection (SRS success metric: > 90%)."""
from __future__ import annotations

import datetime

from app.ai_engine import types as T
from app.ai_engine.parser import parse_policy
from app.ai_engine.staleness import detect_staleness

AS_OF = datetime.date(2026, 7, 11)


def _reasons(findings, policy_id):
    return {f.stale_reason for f in findings if f.policy_id == policy_id}


def test_deprecated_tls_flagged(result):
    net = [f for f in result.staleness
           if f.policy_id == "POL-NET-005" and f.stale_reason == T.DEPRECATED_TECH]
    assert net
    assert any("TLS 1.0" in e for e in net[0].evidence)


def test_sha1_flagged_on_password(result):
    pwd = [f for f in result.staleness
           if f.policy_id == "POL-PWD-001" and f.stale_reason == T.DEPRECATED_TECH]
    assert pwd


def test_review_overdue_flagged(result):
    assert T.REVIEW_OVERDUE in _reasons(result.staleness, "POL-PWD-001")
    overdue = next(f for f in result.staleness
                   if f.policy_id == "POL-PWD-001"
                   and f.stale_reason == T.REVIEW_OVERDUE)
    assert overdue.age_months and overdue.age_months > 18


def test_orphaned_owner_flagged(result):
    assert T.ORPHANED_OWNER in _reasons(result.staleness, "POL-NET-005")


def test_fresh_policy_not_review_overdue():
    text = ("---\ntitle: Fresh Policy\nlast_reviewed: 2026-06-01\n---\n"
            "Section 1: All systems must use TLS 1.2 or higher.")
    p = parse_policy(text, policy_id="FRESH")
    findings = detect_staleness(p, as_of=AS_OF)
    assert not any(f.stale_reason == T.REVIEW_OVERDUE for f in findings)


def test_staleness_recall(result):
    # Every policy in the seed corpus is stale for at least one reason as of the
    # fixed reference date; recall must be comprehensive (> 90%).
    stale_ids = {f.policy_id for f in result.staleness}
    expected = {"POL-PWD-001", "POL-CLD-002", "POL-RET-003",
                "POL-PRV-004", "POL-NET-005", "POL-DEV-006"}
    recall = len(stale_ids & expected) / len(expected)
    assert recall >= 0.9, f"staleness recall {recall:.0%} below 90%"
