"""Staleness detection.

Four independent signals, each producing its own finding so the UI can show a
policy's *reasons* for being stale rather than a single opaque flag:
  * REVIEW_OVERDUE     — last_reviewed older than 18 months
  * DEPRECATED_TECH    — references TLS 1.0 / SHA-1 / Windows Server 2012 / ...
  * SUPERSEDED_STANDARD— references an obsolete standard revision
  * ORPHANED_OWNER     — author/owner marker indicates the owner has left
Staleness is the easiest signal to get right (SRS target > 90%), so recall here
is prioritized while remaining evidence-backed.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from . import lexicon as L
from . import types as T
from .types import PolicyInput, StalenessFinding


def _months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def detect_staleness(policy: PolicyInput,
                     as_of: Optional[date] = None) -> list[StalenessFinding]:
    as_of = as_of or date.today()
    findings: list[StalenessFinding] = []
    seq = 0
    lower = policy.raw_text.lower()

    def _new(reason: str, severity: str, evidence: list[str],
             recommendation: str, age: Optional[int]) -> StalenessFinding:
        nonlocal seq
        seq += 1
        return StalenessFinding(
            id=f"stf_{policy.id}_{seq}",
            policy_id=policy.id,
            stale_reason=reason,
            severity=severity,
            evidence=evidence,
            recommendation=recommendation,
            age_months=age,
        )

    # 1. Review overdue -----------------------------------------------------
    age = None
    if policy.last_reviewed:
        age = _months_between(policy.last_reviewed, as_of)
        if age >= L.REVIEW_OVERDUE_MONTHS:
            severity = T.HIGH if age >= 36 else T.MEDIUM
            findings.append(_new(
                T.REVIEW_OVERDUE, severity,
                [f"Last reviewed {policy.last_reviewed.isoformat()} "
                 f"({age} months ago)"],
                f"Schedule an immediate review; policy exceeds the "
                f"{L.REVIEW_OVERDUE_MONTHS}-month review cadence "
                f"(ISO 27001 A.5.2).",
                age,
            ))

    # 2. Deprecated technology ---------------------------------------------
    dep_hits = [note for term, note in L.DEPRECATED_TECH.items() if term in lower]
    if dep_hits:
        severity = T.HIGH if len(dep_hits) >= 2 else T.MEDIUM
        findings.append(_new(
            T.DEPRECATED_TECH, severity, dep_hits,
            "Remove references to deprecated technology and align with current "
            "cryptographic and platform baselines.",
            age,
        ))

    # 3. Superseded standards ----------------------------------------------
    std_hits = [note for term, note in L.SUPERSEDED_STANDARDS.items()
                if term in lower]
    if std_hits:
        findings.append(_new(
            T.SUPERSEDED_STANDARD, T.MEDIUM, std_hits,
            "Update references to the current revision of the cited standard.",
            age,
        ))

    # 4. Orphaned owner -----------------------------------------------------
    author = (policy.author or "").lower()
    if any(marker in author for marker in L.ORPHANED_OWNER_MARKERS):
        findings.append(_new(
            T.ORPHANED_OWNER, T.MEDIUM,
            [f"Author '{policy.author}' appears to have left the organization"],
            "Reassign policy ownership to an active accountable owner.",
            age,
        ))

    return findings
