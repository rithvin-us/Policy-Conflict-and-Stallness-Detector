"""Explanation payload construction.

Turns a raw finding into the ``ExplanationPayload`` contract (see
``docs/api-contracts.md``) that the UI renders in the side-by-side conflict view:
why it was flagged, the exact trigger terms, highlighted spans in both policies,
the sections involved, the likely resolution, and the compliance references.
"""
from __future__ import annotations

import re
from typing import Any

from app.ai_engine.types import Conflict, StalenessFinding


def _highlight_spans(quote: str, terms: list[str]) -> list[list[int]]:
    spans: list[list[int]] = []
    lower = quote.lower()
    for term in terms:
        if not term:
            continue
        for m in re.finditer(re.escape(term.lower()), lower):
            spans.append([m.start(), m.end()])
    return sorted(spans)


def explain_conflict(c: Conflict) -> dict[str, Any]:
    terms = list(c.evidence.trigger_terms)
    a, b = c.evidence.a, c.evidence.b
    title = f"{c.conflict_type.replace('_', ' ').title()} conflict ({c.severity})"
    why = c.explanation
    if c.scope_analysis:
        why = f"{why} {c.scope_analysis}"
    return {
        "title": title,
        "why_flagged": why,
        "trigger_terms": terms,
        "spans": [
            {"policy_id": a["policy_id"], "section": a.get("section"),
             "quote": a["quote"], "highlight": _highlight_spans(a["quote"], terms)},
            {"policy_id": b["policy_id"], "section": b.get("section"),
             "quote": b["quote"], "highlight": _highlight_spans(b["quote"], terms)},
        ],
        "sections_involved": [s for s in (a.get("section"), b.get("section")) if s],
        "likely_resolution": c.resolution_suggestion,
        "compliance_refs": c.compliance_impact,
        "confidence": c.confidence,
        "confidence_factors": c.confidence_factors,
    }


def explain_staleness(s: StalenessFinding) -> dict[str, Any]:
    return {
        "title": f"{s.stale_reason.replace('_', ' ').title()} ({s.severity})",
        "why_flagged": "; ".join(s.evidence),
        "trigger_terms": [],
        "spans": [],
        "sections_involved": [],
        "likely_resolution": s.recommendation,
        "compliance_refs": ["ISO 27001 A.5.2"],
        "confidence": 0.95,
        "confidence_factors": s.confidence_factors,
    }
