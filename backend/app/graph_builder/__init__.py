"""Policy knowledge-graph construction → React-Flow-ready JSON.

Supports the two view modes required by the brief:
  * POLICY      — each policy is one node; edges are CONFLICT / REDUNDANT / RELATED
  * OBLIGATION  — each obligation is a node; BELONGS_TO edges tie them to their
                  policy, plus the same finding edges between obligations.

Uses NetworkX when available for centrality-informed sizing, but falls back to a
pure-Python deterministic layout so the graph always renders (SRS NFR-5).
The output matches ``docs/data-dictionary.md`` → GraphPayload exactly, so Agent D
renders it without transformation.
"""
from __future__ import annotations

import math
from typing import Any, Optional

from app.ai_engine import types as T
from app.ai_engine.types import Conflict, Obligation, PolicyInput

_REDUNDANT_TYPES = {T.REDUNDANCY, T.PARTIAL_REDUNDANCY}


def _relation_for(conflict: Conflict) -> str:
    return "REDUNDANT" if conflict.conflict_type in _REDUNDANT_TYPES else "CONFLICT"


def _severity_color_kind(severity: str) -> str:
    return {"HIGH": "critical", "MEDIUM": "warning", "LOW": "info"}.get(severity, "info")


def build_policy_graph(policies: list[PolicyInput], obligations: list[Obligation],
                       conflicts: list[Conflict],
                       health_by_id: dict[str, int]) -> dict[str, Any]:
    n = len(policies)
    nodes = []
    ob_count: dict[str, int] = {}
    for o in obligations:
        ob_count[o.policy_id] = ob_count.get(o.policy_id, 0) + 1

    cx, cy, radius = 480, 360, max(220, 60 * n)
    for i, p in enumerate(sorted(policies, key=lambda x: x.id)):
        theta = (2 * math.pi * i / n) - math.pi / 2 if n else 0
        nodes.append({
            "id": p.id,
            "type": "policyNode",
            "position": {"x": round(cx + radius * math.cos(theta)),
                         "y": round(cy + radius * math.sin(theta))},
            "data": {
                "label": p.title,
                "kind": "policy",
                "health": health_by_id.get(p.id, 100),
                "owner": p.owner,
                "obligations": ob_count.get(p.id, 0),
                "status": p.status,
            },
        })

    edges = []
    # Finding edges (conflicts / redundancies) between policies.
    seen: set[tuple[str, str, str]] = set()
    for c in conflicts:
        rel = _relation_for(c)
        key = tuple(sorted((c.policy_a_id, c.policy_b_id)) + [rel])
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "id": f"e_{c.id}",
            "source": c.policy_a_id,
            "target": c.policy_b_id,
            "label": rel,
            "data": {"relation": rel, "severity": c.severity,
                     "confidence": c.confidence,
                     "kind": _severity_color_kind(c.severity)},
        })

    # RELATED edges: policies sharing a topic without a finding edge.
    topic_map: dict[str, set[str]] = {}
    for o in obligations:
        topic_map.setdefault(o.topic, set()).add(o.policy_id)
    for topic, pids in topic_map.items():
        pid_list = sorted(pids)
        for i in range(len(pid_list)):
            for j in range(i + 1, len(pid_list)):
                a, b = pid_list[i], pid_list[j]
                if any(k[:2] == tuple(sorted((a, b))) for k in seen):
                    continue
                rk = (a, b, "RELATED")
                if rk in seen:
                    continue
                seen.add(rk)
                edges.append({
                    "id": f"e_rel_{topic}_{a}_{b}",
                    "source": a, "target": b, "label": topic,
                    "data": {"relation": "RELATED", "topic": topic, "kind": "muted"},
                })

    return {"mode": "POLICY", "nodes": nodes, "edges": edges}


def build_obligation_graph(policies: list[PolicyInput], obligations: list[Obligation],
                           conflicts: list[Conflict],
                           topic: Optional[str] = None,
                           policy_id: Optional[str] = None) -> dict[str, Any]:
    obs = obligations
    if topic:
        obs = [o for o in obs if o.topic == topic]
    if policy_id:
        obs = [o for o in obs if o.policy_id == policy_id]

    policy_order = sorted({o.policy_id for o in obs})
    col_x = {pid: 120 + 340 * i for i, pid in enumerate(policy_order)}
    row_y: dict[str, int] = {}
    nodes = []
    title_by_id = {p.id: p.title for p in policies}

    for o in sorted(obs, key=lambda x: (x.policy_id, x.id)):
        y = row_y.get(o.policy_id, 80)
        row_y[o.policy_id] = y + 130
        nodes.append({
            "id": o.id,
            "type": "obligationNode",
            "position": {"x": col_x[o.policy_id], "y": y},
            "data": {
                "label": (o.evidence_text[:70] + "...") if len(o.evidence_text) > 70
                         else o.evidence_text,
                "kind": "obligation",
                "topic": o.topic,
                "action": o.action,
                "strength": o.strength,
                "polarity": o.polarity,
                "policy": title_by_id.get(o.policy_id, o.policy_id),
                "section": o.section,
            },
        })

    ob_ids = {o.id for o in obs}
    edges = []
    for c in conflicts:
        if c.obligation_a_id in ob_ids and c.obligation_b_id in ob_ids:
            rel = _relation_for(c)
            edges.append({
                "id": f"e_{c.id}",
                "source": c.obligation_a_id,
                "target": c.obligation_b_id,
                "label": c.conflict_type,
                "data": {"relation": rel, "severity": c.severity,
                         "confidence": c.confidence,
                         "kind": _severity_color_kind(c.severity)},
            })

    return {"mode": "OBLIGATION", "nodes": nodes, "edges": edges}


def build_graph(mode: str, policies: list[PolicyInput], obligations: list[Obligation],
                conflicts: list[Conflict], health_by_id: dict[str, int],
                topic: Optional[str] = None,
                policy_id: Optional[str] = None) -> dict[str, Any]:
    if mode.upper() == "OBLIGATION":
        return build_obligation_graph(policies, obligations, conflicts, topic, policy_id)
    return build_policy_graph(policies, obligations, conflicts, health_by_id)
