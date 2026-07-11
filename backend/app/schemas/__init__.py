"""Pydantic request models and ORM→contract serializers.

Request bodies are validated by Pydantic v2. Responses are serialized by the
``*_to_dict`` helpers so the JSON exactly matches ``docs/api-contracts.md`` and
``docs/data-dictionary.md`` — the single mapping point between storage and API.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app import models


# --------------------------- request models --------------------------------

class PolicyUploadRequest(BaseModel):
    title: str = Field(..., min_length=1)
    raw_text: str = Field(..., min_length=1)
    owner: str = ""
    author: Optional[str] = None
    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)
    source: str = "upload"


class ConnectorCreateRequest(BaseModel):
    type: str
    name: str
    config: dict[str, Any] = Field(default_factory=dict)


class WebhookRegisterRequest(BaseModel):
    connector_id: str
    event_types: list[str] = Field(default_factory=lambda: ["push"])


class AnalysisRunRequest(BaseModel):
    policy_ids: Optional[list[str]] = None


class AuditReviewRequest(BaseModel):
    reviewer_status: Optional[str] = None   # PENDING | ACKNOWLEDGED | REVIEWED
    resolution_status: Optional[str] = None  # OPEN | IN_PROGRESS | RESOLVED | PREVIEW


class ReportCreateRequest(BaseModel):
    report_type: str = "POLICY_HEALTH"
    format: str = "MARKDOWN"
    generated_by: str = "system"


# --------------------------- serializers -----------------------------------

def _iso(dt) -> Optional[str]:
    return dt.isoformat() if dt else None


def policy_to_dict(p: "models.Policy") -> dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "source": p.source,
        "owner": p.owner,
        "author": p.author,
        "version": p.version,
        "status": p.status,
        "last_reviewed": _iso(p.last_reviewed),
        "created_at": _iso(p.created_at),
        "updated_at": _iso(p.updated_at),
        "tags": p.tags or [],
        "content": p.content,
        "raw_text": p.raw_text,
        "summary": p.summary,
        "health_score": p.health_score,
        "obligation_count": len(p.obligations) if p.obligations is not None else 0,
    }


def obligation_to_dict(o: "models.Obligation") -> dict[str, Any]:
    return {
        "id": o.id,
        "policy_id": o.policy_id,
        "section": o.section,
        "topic": o.topic,
        "action": o.action,
        "scope": o.scope,
        "strength": o.strength,
        "polarity": o.polarity,
        "parameters": o.parameters,
        "evidence_text": o.evidence_text,
        "confidence": o.confidence,
    }


def conflict_to_dict(c: "models.Conflict") -> dict[str, Any]:
    return {
        "id": c.id,
        "policy_a_id": c.policy_a_id,
        "policy_b_id": c.policy_b_id,
        "obligation_a_id": c.obligation_a_id,
        "obligation_b_id": c.obligation_b_id,
        "conflict_type": c.conflict_type,
        "severity": c.severity,
        "explanation": c.explanation,
        "evidence": c.evidence,
        "confidence": c.confidence,
        "scope_analysis": c.scope_analysis,
        "resolution_suggestion": c.resolution_suggestion,
        "compliance_impact": c.compliance_impact or [],
        "risk": c.risk,
    }


def staleness_to_dict(s: "models.StalenessFinding") -> dict[str, Any]:
    return {
        "id": s.id,
        "policy_id": s.policy_id,
        "stale_reason": s.stale_reason,
        "severity": s.severity,
        "evidence": s.evidence or [],
        "recommendation": s.recommendation,
        "age_months": s.age_months,
        "risk": s.risk,
    }


def connector_to_dict(c: "models.Connector") -> dict[str, Any]:
    safe_config = {k: v for k, v in (c.config or {}).items()
                   if "token" not in k.lower() and "secret" not in k.lower()}
    return {
        "id": c.id,
        "type": c.type,
        "name": c.name,
        "status": c.status,
        "last_sync": _iso(c.last_sync),
        "error_message": c.error_message,
        "config": safe_config,
    }


def webhook_to_dict(w: "models.WebhookEvent") -> dict[str, Any]:
    return {
        "id": w.id,
        "source": w.source,
        "event_type": w.event_type,
        "payload": w.payload,
        "received_at": _iso(w.received_at),
        "processed_at": _iso(w.processed_at),
        "status": w.status,
        "detail": w.detail,
    }


def report_to_dict(r: "models.Report") -> dict[str, Any]:
    return {
        "id": r.id,
        "report_type": r.report_type,
        "generated_at": _iso(r.generated_at),
        "generated_by": r.generated_by,
        "file_path": r.file_path,
        "format": r.format,
        "summary": r.summary,
    }


def timeline_to_dict(t: "models.TimelineEvent") -> dict[str, Any]:
    return {
        "id": t.id,
        "at": _iso(t.at),
        "kind": t.kind,
        "policy_id": t.policy_id,
        "title": t.title,
        "detail": t.detail,
    }


def audit_to_dict(a: "models.AuditEvent") -> dict[str, Any]:
    return {
        "id": a.id,
        "created_at": _iso(a.created_at),
        "source": a.source,
        "event_type": a.event_type,
        "repo": a.repo,
        "branch": a.branch,
        "commit_sha": a.commit_sha,
        "commit_url": a.commit_url,
        "author": a.author,
        "pr_number": a.pr_number,
        "pr_url": a.pr_url,
        "policy_file": a.policy_file,
        "policy_id": a.policy_id,
        "change_type": a.change_type,
        "old_hash": a.old_hash,
        "new_hash": a.new_hash,
        "conflict_status": a.conflict_status,
        "duplicate_status": a.duplicate_status,
        "staleness_status": a.staleness_status,
        "compliance_impact": a.compliance_impact or [],
        "risk_score": a.risk_score,
        "reviewer_status": a.reviewer_status,
        "resolution_status": a.resolution_status,
        "detail": a.detail,
    }


def policy_version_to_dict(v: "models.PolicyVersion") -> dict[str, Any]:
    return {
        "id": v.id,
        "policy_id": v.policy_id,
        "version": v.version,
        "content_hash": v.content_hash,
        "created_at": _iso(v.created_at),
        "size": len(v.raw_text or ""),
    }
