"""Obligation extraction accuracy (SRS success metric: > 80%)."""
from __future__ import annotations

from app.ai_engine import types as T
from app.ai_engine.obligations import extract_obligations
from app.ai_engine.parser import parse_policy


def _find(obligations, **crit):
    for o in obligations:
        if all(getattr(o, k) == v for k, v in crit.items()):
            return o
    return None


def test_password_rotation_obligation_is_mandatory(by_id):
    obs = extract_obligations(by_id["POL-PWD-001"])
    rot = _find(obs, topic=T.PASSWORD, action="rotate")
    assert rot is not None
    assert rot.strength == T.MANDATORY
    assert rot.polarity == T.AFFIRM
    assert rot.parameters.get("duration_days") == 90


def test_cloud_negates_rotation(by_id):
    obs = extract_obligations(by_id["POL-CLD-002"])
    rot = _find(obs, topic=T.PASSWORD, action="rotate")
    assert rot is not None
    assert rot.polarity == T.NEGATE  # "shall not be required"


def test_wrapped_section_keeps_its_parameter(by_id):
    # §4.1 of the privacy policy wraps across two physical lines; the "30 days"
    # duration must survive line-rejoining (regression guard for the parser fix).
    obs = extract_obligations(by_id["POL-PRV-004"])
    delete = _find(obs, action="delete")
    assert delete is not None
    assert delete.parameters.get("duration_days") == 30


def test_should_maps_to_recommended():
    text = "Section 1: Administrators should review the lockout report weekly."
    p = parse_policy(text, policy_id="tmp")
    obs = extract_obligations(p)
    assert obs and obs[0].strength == T.RECOMMENDED


def test_extraction_accuracy_over_corpus(result):
    # Every seed policy contains at least one modal obligation; a healthy
    # extractor pulls a substantial, non-trivial set.
    assert len(result.obligations) >= 18
    assert all(o.evidence_text for o in result.obligations)
    typed = [o for o in result.obligations if o.topic != T.GENERAL]
    assert len(typed) / len(result.obligations) >= 0.8
