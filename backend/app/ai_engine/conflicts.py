"""Conflict and redundancy detection over extracted obligations.

Precision-first (SRS NFR-1, FPR < 20%). Findings are only emitted on explicit
rule matches; merely "related" obligations become graph edges, not conflicts.
The severity matrix intentionally mirrors the challenge brief's worked examples:

  * password "rotate" vs cloud "shall-not rotate"  -> DIRECT / HIGH
    (same action, opposite polarity, both mandatory over an overlapping
    population — a true contradiction even though scopes differ)
  * "all employees must use VPN" vs "developers may bypass VPN" -> SCOPE / LOW
    (opposing actions, but the narrower scope is an explicit *permitted*
    exception — intentional, low risk)
  * "retain 7 years" vs "delete personal data on request" -> TEMPORAL / MEDIUM
    (opposing actions across different data classes — reconcilable, flag for
    review rather than raise a false HIGH alarm)
"""
from __future__ import annotations

from itertools import combinations
from typing import Optional

from . import lexicon as L
from . import types as T
from .similarity import semantic_similarity
from .types import Conflict, Evidence, Obligation, PolicyInput, Scope

# Different surface actions that are semantically opposed.
_OPPOSING_ACTIONS = [
    frozenset({"retain", "delete"}),
    frozenset({"use", "bypass"}),
    frozenset({"enforce", "bypass"}),
    frozenset({"rotate", "bypass"}),
]

_SIM_REDUNDANT = 0.50   # min text similarity to call two obligations redundant


def _scope_relation(a: Scope, b: Scope) -> str:
    if a.value == b.value:
        return "SAME"
    if a.kind == "ALL" or b.kind == "ALL":
        return "EXCEPTION"      # one blanket, one carve-out
    return "DIFFERENT"          # two distinct specific scopes


def _narrower(a: Obligation, b: Obligation) -> Obligation:
    """The obligation with the more specific (non-ALL) scope."""
    if a.scope.kind == "ALL" and b.scope.kind != "ALL":
        return b
    if b.scope.kind == "ALL" and a.scope.kind != "ALL":
        return a
    return b


def _is_polarity_contradiction(a: Obligation, b: Obligation) -> bool:
    return a.action == b.action and a.action != "comply" and a.polarity != b.polarity


def _is_action_contradiction(a: Obligation, b: Obligation) -> bool:
    pair = frozenset({a.action, b.action})
    return pair in _OPPOSING_ACTIONS


def _params_differ(a: Obligation, b: Obligation) -> bool:
    da, db = a.parameters.get("duration_days"), b.parameters.get("duration_days")
    if da is not None and db is not None and da != db:
        return True
    la, lb = a.parameters.get("min_length"), b.parameters.get("min_length")
    if la is not None and lb is not None and la != lb:
        return True
    return False


def _evidence(a: Obligation, b: Obligation, triggers: list[str]) -> Evidence:
    return Evidence(
        a={"policy_id": a.policy_id, "section": a.section, "quote": a.evidence_text},
        b={"policy_id": b.policy_id, "section": b.section, "quote": b.evidence_text},
        trigger_terms=triggers,
    )


def _compliance(topic: str) -> list[str]:
    return L.COMPLIANCE_BY_TOPIC.get(topic, L.COMPLIANCE_BY_TOPIC[T.GENERAL])


def _mk(cid: str, a: Obligation, b: Obligation, ctype: str, severity: str,
        explanation: str, confidence: float, resolution: str,
        triggers: list[str], scope_analysis: Optional[str]) -> Conflict:
    return Conflict(
        id=cid,
        policy_a_id=a.policy_id,
        policy_b_id=b.policy_id,
        obligation_a_id=a.id,
        obligation_b_id=b.id,
        conflict_type=ctype,
        severity=severity,
        explanation=explanation,
        evidence=_evidence(a, b, triggers),
        confidence=round(confidence, 2),
        scope_analysis=scope_analysis,
        resolution_suggestion=resolution,
        compliance_impact=_compliance(a.topic),
    )


def _classify_contradiction(cid: str, a: Obligation, b: Obligation,
                            kind: str) -> Conflict:
    """kind is 'POLARITY' or 'ACTION'. Applies the severity matrix."""
    rel = _scope_relation(a.scope, b.scope)
    temporal = (a.topic == T.DATA_RETENTION
                and "duration_days" in a.parameters
                and "duration_days" in b.parameters)
    triggers = sorted({a.action, b.action})
    base_conf = 0.9 if kind == "POLARITY" else 0.82

    if rel == "SAME":
        ctype = T.TEMPORAL if temporal else T.DIRECT
        sev = T.HIGH
        scope_note = None
        expl = (f"Both policies govern '{a.action}' on {a.topic.lower()} for the "
                f"same scope but state opposing requirements.")
        res = ("Reconcile the two obligations into a single authoritative rule, "
               "or add an explicit precedence clause.")
        return _mk(cid, a, b, ctype, sev, expl, base_conf, res, triggers, scope_note)

    # Scoped (EXCEPTION or DIFFERENT)
    narrow = _narrower(a, b)
    intentional_exception = narrow.strength == T.OPTIONAL

    if intentional_exception:
        sev = T.LOW
        ctype = T.SCOPE
        conf = 0.7
        scope_note = (f"'{narrow.scope.value}' is an explicitly permitted exception "
                      f"to the general rule — likely intentional, low risk.")
        expl = (f"{a.topic.title()} obligations differ, but the narrower scope "
                f"'{narrow.scope.value}' is a permitted carve-out, not a contradiction.")
        res = ("Cross-reference the exception from the general policy so owners "
               "see it is deliberate.")
        return _mk(cid, a, b, ctype, sev, expl, conf, res, triggers, scope_note)

    both_mandatory = a.strength == T.MANDATORY and b.strength == T.MANDATORY
    if kind == "POLARITY" and both_mandatory:
        # True contradiction over an overlapping population (e.g. cloud passwords).
        ctype = T.TEMPORAL if temporal else T.DIRECT
        sev = T.HIGH
        scope_note = (f"Scopes '{a.scope.value}' and '{b.scope.value}' overlap "
                      f"(the narrower systems are a subset of the general population), "
                      f"so the contradiction is live for that overlap.")
        expl = (f"One policy mandates '{a.action}' while the other mandates the "
                f"opposite for {a.topic.lower()}; the scopes overlap, so both cannot "
                f"be satisfied simultaneously.")
        res = ("Harmonize: exempt the narrower scope in the general policy, or align "
               "the narrower policy with the general control as defense-in-depth.")
        return _mk(cid, a, b, ctype, sev, expl, 0.88, res, triggers, scope_note)

    # Opposing actions across different scopes/data-classes -> flag, don't alarm.
    ctype = T.TEMPORAL if temporal else T.SCOPE
    sev = T.MEDIUM
    scope_note = (f"Obligations apply to different scopes ('{a.scope.value}' vs "
                  f"'{b.scope.value}'); they may be reconcilable rather than a hard "
                  f"conflict — review whether the scopes truly overlap.")
    expl = (f"{a.topic.title()} obligations point in opposite directions for "
            f"different scopes; verify whether a real population is caught by both.")
    res = ("Clarify scope boundaries and add explicit precedence so the two rules "
           "cannot both apply to the same records.")
    return _mk(cid, a, b, ctype, sev, expl, 0.68, res, triggers, scope_note)


def _detect_redundancy(cid: str, a: Obligation, b: Obligation) -> Optional[Conflict]:
    if a.action != b.action or a.polarity != b.polarity or a.action == "comply":
        return None
    if _params_differ(a, b):
        return None
    sim = semantic_similarity(a.evidence_text, b.evidence_text)
    if sim < _SIM_REDUNDANT:
        return None
    rel = _scope_relation(a.scope, b.scope)
    partial = rel != "SAME"
    ctype = T.PARTIAL_REDUNDANCY if partial else T.REDUNDANCY
    sev = T.LOW
    conf = round(0.5 + 0.4 * sim, 2)
    if partial:
        expl = (f"Both policies impose the same '{a.action}' rule on "
                f"{a.topic.lower()} but for overlapping scopes — partial duplication "
                f"of governance.")
        res = "Consolidate into one policy or cross-reference to remove overlap."
        scope_note = f"Overlapping scopes '{a.scope.value}' / '{b.scope.value}'."
    else:
        expl = (f"Both policies state the same '{a.action}' obligation on "
                f"{a.topic.lower()} (similarity {sim:.0%}) - redundant governance "
                f"that increases maintenance burden.")
        res = "Retire one copy and keep a single authoritative statement."
        scope_note = None
    return _mk(cid, a, b, ctype, sev, expl, conf, res,
               sorted({a.action, b.action}), scope_note)


def _detect_parameter(cid: str, a: Obligation, b: Obligation) -> Optional[Conflict]:
    if a.action != b.action or a.polarity != b.polarity or a.action == "comply":
        return None
    if not _params_differ(a, b):
        return None
    sev = T.MEDIUM if (a.strength == T.MANDATORY and b.strength == T.MANDATORY) else T.LOW
    da = a.parameters.get("duration_days")
    db = b.parameters.get("duration_days")
    detail = f" ({da} vs {db} days)" if da and db else ""
    expl = (f"Both policies require '{a.action}' on {a.topic.lower()} but with "
            f"different parameters{detail} — a potential conflict.")
    res = "Agree a single parameter value or define which policy takes precedence."
    return _mk(cid, a, b, T.PARAMETER, sev, expl, 0.6, res,
               sorted({a.action}), None)


def _detect_strength(cid: str, a: Obligation, b: Obligation) -> Optional[Conflict]:
    if a.action != b.action or a.polarity != b.polarity or a.action == "comply":
        return None
    if a.strength == b.strength or _params_differ(a, b):
        return None
    if T.MANDATORY not in (a.strength, b.strength):
        return None
    expl = (f"The same '{a.action}' obligation on {a.topic.lower()} is stated with "
            f"different strengths ({a.strength} vs {b.strength}); intent is unclear "
            f"about which takes precedence.")
    res = "Standardize the modal verb (prefer the stronger control) across policies."
    return _mk(cid, a, b, T.STRENGTH, T.LOW, expl, 0.55, res,
               sorted({a.strength, b.strength}), None)


def _dedupe(findings: list[Conflict]) -> list[Conflict]:
    """Collapse findings that describe the same rule pair.

    A policy that repeats an obligation (e.g. "retain 7 years" in §2.1 and §2.2)
    would otherwise raise the same conflict twice. We keep one representative per
    (policy_a, policy_b, conflict_type, trigger_terms), preferring the highest
    confidence — this directly protects the false-positive-rate target (NFR-1).
    """
    best: dict[tuple, Conflict] = {}
    for c in findings:
        key = (
            tuple(sorted((c.policy_a_id, c.policy_b_id))),
            c.conflict_type,
            tuple(sorted(c.evidence.trigger_terms)),
        )
        cur = best.get(key)
        if cur is None or c.confidence > cur.confidence:
            best[key] = c
    return list(best.values())


def detect_conflicts(obligations: list[Obligation]) -> list[Conflict]:
    """Compare every cross-policy obligation pair on the same topic."""
    findings: list[Conflict] = []
    counter = 0

    # Deterministic order.
    obs = sorted(obligations, key=lambda o: (o.policy_id, o.id))
    for a, b in combinations(obs, 2):
        if a.policy_id == b.policy_id:
            continue
        if a.topic != b.topic or a.topic == T.GENERAL:
            continue

        counter += 1
        cid = f"cfl_{counter:04d}"

        if _is_polarity_contradiction(a, b):
            findings.append(_classify_contradiction(cid, a, b, "POLARITY"))
            continue
        if _is_action_contradiction(a, b):
            findings.append(_classify_contradiction(cid, a, b, "ACTION"))
            continue

        red = _detect_redundancy(cid, a, b)
        if red:
            findings.append(red)
            continue
        par = _detect_parameter(cid, a, b)
        if par:
            findings.append(par)
            continue
        strn = _detect_strength(cid, a, b)
        if strn:
            findings.append(strn)

    # Dedupe, then renumber deterministically for stable IDs.
    deduped = _dedupe(findings)
    deduped.sort(key=lambda c: (c.policy_a_id, c.policy_b_id, c.conflict_type))
    for i, c in enumerate(deduped, 1):
        c.id = f"cfl_{i:04d}"
    return deduped
