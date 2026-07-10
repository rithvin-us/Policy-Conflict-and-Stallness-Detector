"""Shared fixtures for the test suite.

Analysis runs once per session against the seed corpus with a *fixed* reference
date so every staleness assertion is deterministic and reproducible (SRS NFR-2).
"""
from __future__ import annotations

import datetime
import os
import pathlib

import pytest

# Configure a dedicated, deterministic test environment BEFORE any module that
# reads settings (app.core.config) is imported.
_TEST_DB = pathlib.Path(__file__).resolve().parent / "_test_policyguardian.db"
os.environ.setdefault("ANALYSIS_AS_OF", "2026-07-11")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")
os.environ.setdefault("SEED_ON_STARTUP", "1")

from app.ai_engine import analyze_corpus, parse_policy  # noqa: E402

AS_OF = datetime.date(2026, 7, 11)
CORPUS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "sample_data" / "policies"
)


def _safe_unlink(path: pathlib.Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except PermissionError:  # Windows may briefly hold the sqlite file
        pass


@pytest.fixture(scope="session")
def client():
    _safe_unlink(_TEST_DB)
    from fastapi.testclient import TestClient

    from app.core.db import engine
    from app.main import app

    with TestClient(app) as c:  # triggers lifespan → seed + first analysis
        yield c
    engine.dispose()  # release the sqlite file handle before cleanup
    _safe_unlink(_TEST_DB)


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
