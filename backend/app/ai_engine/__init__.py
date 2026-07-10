"""Policy Guardian AI — policy intelligence engine.

Deterministic, standard-library-only core. Optional ML (sentence-transformers /
spaCy / FAISS / scikit-learn) upgrades similarity when installed and enabled, but
is never a hard dependency (see ``similarity.py``).
"""
from __future__ import annotations

from .conflicts import detect_conflicts
from .engine import analyze_corpus
from .obligations import extract_obligations
from .parser import parse_policy, split_sections
from .staleness import detect_staleness
from .types import (
    AnalysisResult,
    Conflict,
    Obligation,
    PolicyInput,
    Scope,
    StalenessFinding,
)

__all__ = [
    "analyze_corpus",
    "detect_conflicts",
    "extract_obligations",
    "detect_staleness",
    "parse_policy",
    "split_sections",
    "AnalysisResult",
    "Conflict",
    "Obligation",
    "PolicyInput",
    "Scope",
    "StalenessFinding",
]
