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

# Modal verbs separate the subject ("Backups") from the predicate verb
# ("encrypted"). Action detection scans *after* the modal so a leading subject
# noun that happens to be an action word cannot hijack the obligation's action.
_MODAL_ANCHORS = {
    "must", "shall", "should", "may", "required", "prohibited", "recommended",
    "expected", "encouraged", "permitted", "need", "needs", "will",
}

# Specific content verbs outrank generic/means verbs so "encrypted using AES"
# resolves to `encrypt`, not `use`, and "shall not be required ... changes"
# resolves to `rotate`, not the auxiliary `enforce`.
_SPECIFIC_ACTIONS = {
    "rotate", "encrypt", "retain", "delete", "reuse", "classify", "bypass",
    "backup",
}


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


def _detect_topics(sentence_lower: str) -> list[str]:
    found = []
    for topic, keywords in L.TOPIC_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"(?<!\w){re.escape(kw)}", sentence_lower):
                if topic not in found:
                    found.append(topic)
                break  # Go to next topic
    return found if found else [T.GENERAL]


def _detect_action(sentence_lower: str) -> str:
    """Return the normalized predicate action lemma, else ``"comply"``.

    Takes the last action lemma *after* the first modal verb — which lands on the
    real predicate across both active ("must rotate passwords") and passive
    ("Backups must be encrypted", "rotation shall not be required ... changes")
    voice, without a leading subject noun overriding it.
    """
    tokens = _WORD_RE.findall(sentence_lower)
    anchor = next((i for i, t in enumerate(tokens) if t in _MODAL_ANCHORS), -1)
    after = tokens[anchor + 1:] if anchor >= 0 else tokens

    def _pick(cands: list[str]) -> Optional[str]:
        if not cands:
            return None
        specific = [c for c in cands if c in _SPECIFIC_ACTIONS]
        return (specific or cands)[-1]

    action = _pick([L.ACTION_SYNONYMS[t] for t in after if t in L.ACTION_SYNONYMS])
    if action:
        return action
    # Fallback: passive subject-only phrasing where the action precedes the modal.
    action = _pick([L.ACTION_SYNONYMS[t] for t in tokens if t in L.ACTION_SYNONYMS])
    return action or "comply"


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
    algo = L.ALGO_RE.search(sentence)
    if algo:
        params["algorithm"] = algo.group(1).upper()
    tls = L.TLS_RE.search(sentence)
    if tls:
        params["tls_version"] = tls.group(1).upper().replace(" ", "")
    timeout = L.TIMEOUT_RE.search(sentence)
    if timeout:
        qty = int(timeout.group(1))
        unit = timeout.group(2).lower()
        params["timeout_value"] = qty
        params["timeout_unit"] = unit
        params["timeout_minutes"] = round(qty * (60 if "hour" in unit else 1))
    port = L.PORT_RE.search(sentence)
    if port:
        params["port"] = int(port.group(1))
    keysize = L.KEY_SIZE_RE.search(sentence)
    if keysize:
        params["key_size"] = int(keysize.group(1))
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
        topics = _detect_topics(lower)
        action = _detect_action(lower)
        obligations.append(
            Obligation(
                id=f"obl_{policy.id}_{seq}",
                policy_id=policy.id,
                section=section,
                topic=topics[0],
                topics=topics,
                action=action,
                scope=_detect_scope(lower),
                strength=strength,
                polarity=_detect_polarity(lower),
                parameters=_extract_parameters(sentence),
                evidence_text=sentence,
                confidence=_confidence(strength, topics[0], action),
            )
        )
    return obligations
