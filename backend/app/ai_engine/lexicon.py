"""Domain lexicon for obligation extraction and detection.

Centralizes every keyword table so the intelligence is auditable in one place.
Regex is used only as the extraction *substrate*; the semantics (strength,
polarity, topic, scope, action normalization) live here as explicit, reviewable
mappings — which is what makes findings explainable to a policy owner.
"""
from __future__ import annotations

import re

from . import types as T

# --- Obligation strength (RFC-2119-style modal verbs) ----------------------
# Order matters: longer phrases checked first in the extractor.
STRENGTH_MODALS: dict[str, str] = {
    "must not": T.MANDATORY,
    "shall not": T.MANDATORY,
    "may not": T.MANDATORY,
    "is prohibited": T.MANDATORY,
    "are prohibited": T.MANDATORY,
    "prohibited": T.MANDATORY,
    "required to": T.MANDATORY,
    "is required": T.MANDATORY,
    "are required": T.MANDATORY,
    "must": T.MANDATORY,
    "shall": T.MANDATORY,
    "required": T.MANDATORY,
    "should not": T.RECOMMENDED,
    "should": T.RECOMMENDED,
    "recommended": T.RECOMMENDED,
    "expected to": T.RECOMMENDED,
    "may": T.OPTIONAL,
    "encouraged": T.OPTIONAL,
    "permitted": T.OPTIONAL,
    "are permitted": T.OPTIONAL,
}

# Phrases that flip polarity to NEGATE ("do not do X").
NEGATION_MARKERS = (
    "must not",
    "shall not",
    "may not",
    "should not",
    "not be required",
    "not required",
    "prohibited",
    "no longer",
    "never",
    "without",
    "exempt",
    "bypass",
    "do not",
    "does not",
    "cannot",
)

# Action pairs that mean the opposite of each other. Used both to classify
# action-contradictions and to resolve double negatives during extraction
# (a negated action == an affirmation of its opposite, e.g. "not deleted" ==
# "retained").
OPPOSING_ACTIONS = [
    frozenset({"retain", "delete"}),
    frozenset({"use", "bypass"}),
    frozenset({"enforce", "bypass"}),
    frozenset({"rotate", "bypass"}),
]

# --- Topic classification --------------------------------------------------
# First matching topic (in dict order) wins; keys are compiled to word-boundary
# regexes for precision.
TOPIC_KEYWORDS: dict[str, list[str]] = {
    T.PASSWORD: ["password", "passphrase", "credential", "credentials"],
    T.AUTHENTICATION: ["mfa", "multi-factor", "multifactor", "2fa",
                       "two-factor", "authentication", "api key", "api keys"],
    T.IDENTITY: ["identity", "iam", "account", "accounts", "user", "users", "privileged"],
    T.ENCRYPTION: ["encrypt", "encryption", "encrypted", "cipher", "tls",
                   "ssl", "cryptograph", "hash", "hashed", "at rest",
                   "in transit"],
    T.DATA_RETENTION: ["retain", "retention", "retained", "delete", "deleted",
                       "deletion", "erasure", "purge", "archive", "archives",
                       "keep for", "stored for"],
    T.DATA_CLASSIFICATION: ["classification", "classify", "confidential",
                            "sensitive data", "data label", "labelling"],
    T.NETWORK: ["vpn", "network", "firewall", "remote connection", "remote access",
                "ci/cd", "pipeline", "internal system", "internal systems"],
    T.ACCESS_CONTROL: ["access control", "least privilege", "privilege",
                       "rbac", "role-based", "authorization", "permission",
                       "grant access", "access to"],
    T.LOGGING: ["log", "logs", "logged", "logging", "audit trail", "audit log",
                "monitoring"],
    T.BACKUP: ["backup", "backups", "restore", "disaster recovery"],
    T.INCIDENT_RESPONSE: ["incident", "breach", "response plan"],
}

# --- Action normalization --------------------------------------------------
# Maps many surface verbs to one canonical action lemma so "rotate",
# "refresh", "cycle" collapse to the same action for conflict comparison.
ACTION_SYNONYMS: dict[str, str] = {
    "rotate": "rotate", "rotated": "rotate", "rotates": "rotate",
    "rotation": "rotate", "refresh": "rotate", "refreshed": "rotate",
    "cycle": "rotate", "cycled": "rotate", "change": "rotate",
    "changes": "rotate", "changed": "rotate",
    "encrypt": "encrypt", "encrypted": "encrypt", "encrypting": "encrypt",
    "encryption": "encrypt",
    "retain": "retain", "retained": "retain", "retaining": "retain",
    "retention": "retain", "keep": "retain", "kept": "retain",
    "store": "retain", "stored": "retain", "storing": "retain",
    "delete": "delete", "deleted": "delete", "deleting": "delete",
    "deletion": "delete", "erase": "delete", "erased": "delete",
    "purge": "delete", "purged": "delete", "remove": "delete",
    "removed": "delete",
    "enforce": "enforce", "enforced": "enforce", "enforcing": "enforce",
    "require": "enforce", "required": "enforce",
    "use": "use", "used": "use", "using": "use",
    "enable": "use", "enabled": "use",
    "review": "review", "reviewed": "review", "reviewing": "review",
    "reuse": "reuse", "reused": "reuse",
    "bypass": "bypass", "bypassed": "bypass", "exempt": "bypass",
    "exempted": "bypass", "skip": "bypass",
    "log": "log", "logged": "log", "logging": "log",
    "monitor": "log", "monitored": "log",
    "backup": "backup", "back": "backup", "backed": "backup",
    "apply": "apply", "applied": "apply", "applying": "apply",
    "classify": "classify", "classified": "classify", "label": "classify",
}

# --- Scope detection -------------------------------------------------------
# (kind, normalized value, regex) — first match wins; more specific first.
SCOPE_PATTERNS: list[tuple[str, str, str]] = [
    ("ROLE", "developers", r"\bdevelopers?\b"),
    ("ROLE", "administrators", r"\badministrators?\b|\badmins?\b"),
    ("SERVICE", "service_accounts", r"\bservice accounts?\b"),
    ("SYSTEM", "cloud", r"\bcloud[- ]?hosted\b|\bcloud systems?\b|\bcloud\b"),
    ("SYSTEM", "ci_cd", r"\bci/cd\b|\bpipelines?\b|\bbuild network\b"),
    ("SYSTEM", "legacy", r"\blegacy systems?\b|\bon-?prem\b"),
    ("GEO", "eu", r"\beu (data|residents?|subjects?)\b|\bgdpr\b|\beuropean\b"),
    ("SYSTEM", "personal_data", r"\bpersonal data\b"),
    ("SYSTEM", "databases", r"\bdatabases?\b"),
    ("SYSTEM", "backup_media", r"\bbackup (media|archives?)\b"),
    ("ALL", "all_employees", r"\ball employees\b|\ball users?\b|\ball staff\b"),
    ("ALL", "all_systems", r"\ball (cloud-?hosted )?systems?\b|\ball corporate\b"),
]

# --- Parameter extraction --------------------------------------------------
DURATION_RE = re.compile(
    r"(\d+)\s*(day|days|month|months|year|years|hour|hours)\b", re.I
)
MIN_LENGTH_RE = re.compile(r"(?:at least|minimum of|length)\s+(\d+)\s+characters?", re.I)
COUNT_RE = re.compile(r"(?:previous|history)\s+(\d+)", re.I)
ALGO_RE = re.compile(r"\b(AES-128|AES-256|RSA-2048|RSA-4096|SHA-1|SHA-256)\b", re.I)
TLS_RE = re.compile(r"\b(TLS\s*1\.[0-3])\b", re.I)
TIMEOUT_RE = re.compile(r"(?:timeout|expires?|idle).{0,20}?(\d+)\s*(minute|minutes|hour|hours)\b", re.I)
PORT_RE = re.compile(r"\bport\s+(\d+)\b", re.I)
KEY_SIZE_RE = re.compile(r"\b(\d{3,4})[- ]?bit\b", re.I)

DURATION_TO_DAYS = {
    "hour": 1 / 24, "hours": 1 / 24,
    "day": 1, "days": 1,
    "month": 30, "months": 30,
    "year": 365, "years": 365,
}

# --- Staleness knowledge ---------------------------------------------------
DEPRECATED_TECH: dict[str, str] = {
    "tls 1.0": "TLS 1.0 is deprecated (RFC 8996); require TLS 1.2+.",
    "tls 1.1": "TLS 1.1 is deprecated (RFC 8996); require TLS 1.2+.",
    "sslv3": "SSLv3 is broken (POODLE); require TLS 1.2+.",
    "ssl 3": "SSLv3 is broken (POODLE); require TLS 1.2+.",
    "sha-1": "SHA-1 is cryptographically broken; use SHA-256+.",
    "sha1": "SHA-1 is cryptographically broken; use SHA-256+.",
    "md5": "MD5 is insecure for security use; use SHA-256+.",
    "3des": "3DES is deprecated (NIST SP 800-131A); use AES.",
    "des ": "DES is obsolete; use AES.",
    "wep": "WEP is insecure; use WPA2/WPA3.",
    "windows server 2012": "Windows Server 2012 is end-of-life (Oct 2023).",
    "windows server 2008": "Windows Server 2008 is end-of-life.",
    "windows 7": "Windows 7 is end-of-life.",
}

SUPERSEDED_STANDARDS: dict[str, str] = {
    "nist sp 800-53 rev 4": "NIST SP 800-53 Rev 4 superseded by Rev 5 (2020).",
    "nist 800-53 rev 4": "NIST SP 800-53 Rev 4 superseded by Rev 5 (2020).",
    "pci dss 3": "PCI DSS v3.x superseded by v4.0.",
    "iso 27001:2013": "ISO/IEC 27001:2013 superseded by the 2022 revision.",
}

ORPHANED_OWNER_MARKERS = ("former.employee", "unknown", "n/a", "vacant", "tbd")

REVIEW_OVERDUE_MONTHS = 18

# --- Compliance mapping (finding-level) ------------------------------------
# topic -> framework clauses touched, used to populate compliance_impact.
COMPLIANCE_BY_TOPIC: dict[str, list[str]] = {
    T.PASSWORD: ["ISO 27001 A.5.1", "NIST IA-5", "NIST 800-63B"],
    T.AUTHENTICATION: ["ISO 27001 A.5.1", "NIST IA-2"],
    T.IDENTITY: ["ISO 27001 A.5.1", "NIST AC-2"],
    T.ENCRYPTION: ["ISO 27001 A.8.24", "NIST SC-13"],
    T.DATA_RETENTION: ["GDPR Art.5", "GDPR Art.17", "SOX", "ISO 27001 A.5.34"],
    T.DATA_CLASSIFICATION: ["ISO 27001 A.5.12", "NIST RA-2"],
    T.NETWORK: ["ISO 27001 A.8.20", "NIST AC-17"],
    T.ACCESS_CONTROL: ["ISO 27001 A.5.15", "NIST AC-6"],
    T.LOGGING: ["ISO 27001 A.8.15", "NIST AU-2"],
    T.BACKUP: ["ISO 27001 A.8.13", "NIST CP-9"],
    T.GENERAL: ["ISO 27001 A.5.1"],
}

# Framework catalogue used by the compliance-coverage endpoint.
FRAMEWORK_CLAUSES = {
    "ISO 27001": {
        "A.5.1": "Policies for information security",
        "A.5.2": "Review of the policies",
        "A.5.15": "Access control",
        "A.8.24": "Use of cryptography",
    },
    "NIST SP 800-53": {
        "PL-1": "Policy and procedures",
        "PM-1": "Information security program plan",
        "IA-5": "Authenticator management",
        "AC-6": "Least privilege",
    },
    "GDPR": {
        "Art.5": "Principles of processing",
        "Art.17": "Right to erasure",
        "Art.24": "Responsibility of the controller",
    },
    "COBIT 2019": {
        "APO01": "Maintain a policy framework",
    },
}


def normalize_action(word: str) -> str:
    return ACTION_SYNONYMS.get(word.lower().strip(".,;:"), word.lower().strip(".,;:"))
