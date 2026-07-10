"""Core value types for the Policy Guardian AI engine.

Pure standard-library dataclasses that mirror ``docs/data-dictionary.md``. The
engine never imports FastAPI, SQLAlchemy, or any ML library at module load time,
so these types (and every detector that uses them) run and test with zero
optional dependencies on Python 3.11–3.14.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Enumerated string constants (kept as plain str for JSON-transparent payloads)
# ---------------------------------------------------------------------------

# Topic
PASSWORD = "PASSWORD"
ENCRYPTION = "ENCRYPTION"
ACCESS_CONTROL = "ACCESS_CONTROL"
AUTHENTICATION = "AUTHENTICATION"
DATA_RETENTION = "DATA_RETENTION"
DATA_CLASSIFICATION = "DATA_CLASSIFICATION"
NETWORK = "NETWORK"
LOGGING = "LOGGING"
BACKUP = "BACKUP"
INCIDENT_RESPONSE = "INCIDENT_RESPONSE"
GENERAL = "GENERAL"

# Strength
MANDATORY = "MANDATORY"
RECOMMENDED = "RECOMMENDED"
OPTIONAL = "OPTIONAL"

# Polarity
AFFIRM = "AFFIRM"
NEGATE = "NEGATE"

# Conflict type
DIRECT = "DIRECT"
TEMPORAL = "TEMPORAL"
SCOPE = "SCOPE"
STRENGTH = "STRENGTH"
PARAMETER = "PARAMETER"
PARTIAL_REDUNDANCY = "PARTIAL_REDUNDANCY"
REDUNDANCY = "REDUNDANCY"

# Severity
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

# Staleness reason
REVIEW_OVERDUE = "REVIEW_OVERDUE"
DEPRECATED_TECH = "DEPRECATED_TECH"
SUPERSEDED_STANDARD = "SUPERSEDED_STANDARD"
ORPHANED_OWNER = "ORPHANED_OWNER"
NO_VERSION_HISTORY = "NO_VERSION_HISTORY"


@dataclass
class PolicyInput:
    """Normalized policy handed to the engine (produced by the parser or the
    backend ingestion service)."""

    id: str
    title: str
    raw_text: str
    owner: str = ""
    author: Optional[str] = None
    version: str = "1.0"
    status: str = "ACTIVE"
    source: str = "local:seed"
    last_reviewed: Optional[date] = None
    created_at: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class Scope:
    kind: str = "ALL"          # ALL | ROLE | SYSTEM | GEO | SERVICE
    value: str = "all"         # normalized token
    raw: str = ""              # source phrase

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Obligation:
    id: str
    policy_id: str
    section: Optional[str]
    topic: str
    action: str
    scope: Scope
    strength: str
    polarity: str
    parameters: dict[str, Any]
    evidence_text: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["scope"] = self.scope.to_dict()
        return d


@dataclass
class Evidence:
    a: dict[str, Any]
    b: dict[str, Any]
    trigger_terms: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Conflict:
    id: str
    policy_a_id: str
    policy_b_id: str
    obligation_a_id: Optional[str]
    obligation_b_id: Optional[str]
    conflict_type: str
    severity: str
    explanation: str
    evidence: Evidence
    confidence: float
    scope_analysis: Optional[str]
    resolution_suggestion: str
    compliance_impact: list[str]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence"] = self.evidence.to_dict()
        return d


@dataclass
class StalenessFinding:
    id: str
    policy_id: str
    stale_reason: str
    severity: str
    evidence: list[str]
    recommendation: str
    age_months: Optional[int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    """Everything the engine produces for a corpus in one pass."""

    obligations: list[Obligation]
    conflicts: list[Conflict]
    staleness: list[StalenessFinding]
    policy_health: dict[str, int]          # policy_id -> 0..100
    governance: dict[str, Any]             # GovernanceScore payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligations": [o.to_dict() for o in self.obligations],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "staleness": [s.to_dict() for s in self.staleness],
            "policy_health": self.policy_health,
            "governance": self.governance,
        }
