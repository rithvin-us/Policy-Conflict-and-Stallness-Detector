"""Shared fixtures for the test suite.

Analysis runs once per session against the seed corpus with a *fixed* reference
date so every staleness assertion is deterministic and reproducible (SRS NFR-2).
"""
from __future__ import annotations

import datetime
import pathlib

import pytest

from app.ai_engine import analyze_corpus, parse_policy

AS_OF = datetime.date(2026, 7, 11)
CORPUS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "sample_data" / "policies"
)


@pytest.fixture(scope="session")
def policies():
    return [
        parse_policy(f.read_text(encoding="utf-8"), policy_id=f.stem)
        for f in sorted(CORPUS_DIR.glob("*.md"))
    ]


@pytest.fixture(scope="session")
def result(policies):
    return analyze_corpus(policies, as_of=AS_OF)


@pytest.fixture(scope="session")
def by_id(policies):
    return {p.id: p for p in policies}
