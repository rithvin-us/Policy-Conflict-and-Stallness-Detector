"""Obligation extraction.

Turns a policy's sentences into structured :class:`Obligation` records. The
approach is rule-driven and fully explainable: every field traces to an explicit
lexicon entry (see ``lexicon.py``), which is what lets the UI show *why* a
sentence became an obligation. Regex is the substrate; the semantics are tables.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from . import lexicon as L
from . import types as T
from .parser import split_sections
from .types import Obligation, PolicyInput, Scope

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z/\-]*")


def _detect_strength(sentence_lower: str) -> Optional[str]:
    for phrase, strength in L.STRENGTH_MODALS.items():
        if re.search(rf"\b{re.escape(phrase)}\b", sentence_lower):
            return strength
    return None


def _detect_polarity(sentence_lower: str) -> str:
    for marker in L.NEGATION_MARKERS:
        if marker in sentence_lower:
            return T.NEGATE
    return T.AFFIRM


def _detect_topic(sentence_lower: str) -> str:
    for topic, keywords in L.TOPIC_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"(?<!\w){re.escape(kw)}", sentence_lower):
                return topic
    return T.GENERAL


def _detect_action(sentence_lower: str) -> str:
    """Return the first normalized action lemma present, else ``"comply"``."""
    for token in _WORD_RE.findall(sentence_lower):
        norm = L.ACTION_SYNONYMS.get(token)
        if norm:
            return norm
    return "comply"


def _detect_scope(sentence_lower: str) -> Scope:
    for kind, value, pattern in L.SCOPE_PATTERNS:
        m = re.search(pattern, sentence_lower)
        if m:
            return Scope(kind=kind, value=value, raw=m.group(0))
    return Scope(kind="ALL", value="all", raw="")


def _extract_parameters(sentence: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    dm = L.DURATION_RE.search(sentence)
    if dm:
        qty = int(dm.group(1))
        unit = dm.group(2).lower()
        params["duration_value"] = qty
        params["duration_unit"] = unit
        params["duration_days"] = round(qty * L.DURATION_TO_DAYS[unit])
    ml = L.MIN_LENGTH_RE.search(sentence)
    if ml:
        params["min_length"] = int(ml.group(1))
    cm = L.COUNT_RE.search(sentence)
    if cm:
        params["history_count"] = int(cm.group(1))
    return params


def _confidence(strength: Optional[str], topic: str, action: str) -> float:
    score = 0.55
    if strength == T.MANDATORY:
        score += 0.25
    elif strength == T.RECOMMENDED:
        score += 0.15
    if topic != T.GENERAL:
        score += 0.12
    if action != "comply":
        score += 0.08
    return round(min(score, 0.98), 2)


def extract_obligations(policy: PolicyInput) -> list[Obligation]:
    """Extract all obligations from a policy document."""
    obligations: list[Obligation] = []
    seq = 0
    for section, sentence in split_sections(policy.raw_text):
        lower = sentence.lower()
        strength = _detect_strength(lower)
        if strength is None:
            continue  # no modal verb → not an obligation
        seq += 1
        topic = _detect_topic(lower)
        obligations.append(
            Obligation(
                id=f"obl_{policy.id}_{seq}",
                policy_id=policy.id,
                section=section,
                topic=topic,
                action=_detect_action(lower),
                scope=_detect_scope(lower),
                strength=strength,
                polarity=_detect_polarity(lower),
                parameters=_extract_parameters(sentence),
                evidence_text=sentence,
                confidence=_confidence(strength, topic, _detect_action(lower)),
            )
        )
    return obligations
