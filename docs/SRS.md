# Software Requirements Specification
## Policy Guardian AI — Continuous Policy Governance & Compliance Intelligence Platform

**Document version:** 1.0
**Standard:** IEEE 830-1998 (adapted)
**Author:** Agent A — Architect / SRS Lead
**Status:** Baseline for the hackathon build

---

## 1. Introduction

### 1.1 Purpose
This SRS specifies the requirements for **Policy Guardian AI**, a platform that
continuously ingests enterprise security and compliance policies, extracts the
obligations they contain, and detects **conflicts, redundancies, staleness, and
compliance-coverage gaps** across the entire policy corpus. It is written for
engineers building the system, compliance managers who operate it, and auditors
who consume its reports.

### 1.2 Scope
Enterprises accumulate dozens of policies authored by different teams across many
years. Contradictions ("rotate passwords every 90 days" vs "do not rotate
passwords; enforce MFA"), silent redundancy, and stale references to deprecated
technology (TLS 1.0, SHA-1, Windows Server 2012) create real audit and legal
exposure. Today these are found by auditors, not before them.

Policy Guardian AI closes that gap. It provides:
- Automated, explainable detection of policy conflicts and overlaps.
- Staleness surveillance tied to review cadence and deprecated-tech references.
- A policy knowledge graph (whole-policy and obligation-level views).
- Governance health scoring and prioritized, audit-ready findings.
- Continuous sync from policy sources (GitHub, local folders) plus webhook-driven
  re-analysis when policies change.
- Compliance-framework mapping (ISO 27001, NIST 800-53, GDPR, COBIT).

### 1.3 Definitions
See `docs/data-dictionary.md` for the frozen entity contract. Key terms:
**Policy**, **Obligation**, **Conflict**, **Redundancy**, **StalenessFinding**,
**Connector**, **WebhookEvent**, **Report**, **GovernanceScore**.

### 1.4 References
- ISO/IEC 27001:2022 §5.1, §5.2 — Policies for Information Security; Review of Policies
- NIST SP 800-53 Rev 5 — PL-1, PM-1, IA-5
- NIST SP 800-63B — Digital Identity Guidelines (password rotation guidance)
- EU GDPR Articles 5, 17, 24
- COBIT 2019 — APO01 Maintain Policy Framework
- Source challenge brief: *Policy Conflict & Staleness Detector* (Société Générale)

---

## 2. Overall Description

### 2.1 Product Perspective
Policy Guardian AI is a self-contained web platform composed of four tiers:

```
 Sources ──► Connector Framework ──► Ingestion & Normalization ──► Policy Store
                                                                      │
                                              AI Policy Intelligence ◄┘
                                              (obligations, similarity,
                                               conflict / redundancy /
                                               staleness, graph, risk)
                                                        │
                        Findings + Graph + Scores + Reports (REST API)
                                                        │
                                Operations Console (Next.js dashboard)
                                                        │
                                   Compliance managers & auditors
```

Change events arrive two ways: **scheduled sync** (Celery beat / manual trigger)
and **webhooks** (e.g. GitHub push). Both funnel into the same ingestion →
analysis pipeline, so results are identical regardless of trigger.

### 2.2 Product Functions (summary)
1. Ingest policies from connectors and manual upload.
2. Normalize and version policy documents; retain change history.
3. Extract obligations with strength, polarity, scope, topic, parameters.
4. Detect conflicts (direct, temporal, scope, strength, parameter).
5. Detect redundancy and partial overlap.
6. Detect staleness (review overdue, deprecated tech, superseded standards).
7. Score policy health and organization-wide governance.
8. Build and serve the policy knowledge graph.
9. Generate explainable findings with evidence and resolution suggestions.
10. Produce audit reports (Markdown / JSON / HTML).
11. Notify compliance managers via webhook-out / integration hooks.

### 2.3 User Classes
| Class | Goal | Primary views |
|---|---|---|
| Compliance Manager | Triage findings, drive remediation | Overview, Review Queue, Conflicts |
| Security/Policy Owner | Fix flagged obligations in their policies | Policy Detail, Conflict Compare |
| Auditor | Evidence of consistent, reviewed policies | Reports, Compliance Mapping |
| Platform Engineer | Operate connectors and webhooks | Connectors, Webhook Status |

### 2.4 Operating Environment
- Backend: Python 3.11+ (validated on 3.14), FastAPI, SQLAlchemy 2.x,
  PostgreSQL 15 (SQLite for local/dev), Redis + Celery.
- AI: pure-Python deterministic core; optional sentence-transformers / spaCy /
  FAISS / scikit-learn upgrade layer.
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind, Framer Motion,
  React Flow, Recharts.
- Packaging: Docker + Docker Compose; CI via GitHub Actions.

### 2.5 Design Constraints
- **Precision-first.** False conflict alerts erode trust with policy owners
  (SRS §5, FPR target < 20%). Detectors emit confidence and prefer to downgrade
  severity (e.g. scope exceptions) over crying wolf.
- **Explainability over model complexity.** Every finding must cite the exact
  triggering text and offer a resolution.
- **Runs without a GPU or model download.** The deterministic core must pass all
  detection tests offline; ML is an enhancement, never a hard dependency.

### 2.6 Assumptions & Dependencies
- Policies are text/markdown. Binary formats (PDF/DOCX) are future work.
- Notifications target compliance managers, never rank-and-file employees.
- Connector secrets are provided via environment/secret store, never persisted
  in plaintext or returned by the API.

---

## 3. External Interface Requirements

### 3.1 User Interfaces
A dark, high-density "policy operations console" (not a generic SaaS dashboard):
governance score header, findings triage, React Flow graph explorer, side-by-side
conflict comparison, timeline of policy changes, connector + webhook status,
report downloads. Full field-level contract in `docs/api-contracts.md`.

### 3.2 Software Interfaces
- **REST API** `/, /api/v1/*` — JSON, documented via OpenAPI at `/docs`.
- **Webhook-in** `/api/v1/webhooks/{connector}` — signed event ingestion.
- **Connector SPI** — `BaseConnector` interface (list/fetch/verify).

### 3.3 Communication Interfaces
HTTPS/JSON. Webhook signature verification (HMAC) where the source supports it.

---

## 4. System Features (functional requirements)

Each requirement is testable and traced to acceptance criteria in §6.

- **FR-1 Ingestion.** The system SHALL ingest policies from configured connectors
  and manual upload, storing `raw_text`, normalized `content`, and metadata.
- **FR-2 Versioning.** On re-ingest of a changed policy, the system SHALL create a
  new version and preserve prior versions for diffing (Roadmap: version-diff).
- **FR-3 Obligation extraction.** The system SHALL extract obligations with
  `topic`, `action`, `strength`, `polarity`, `scope`, `parameters`, and evidence,
  at ≥ 80% accuracy on the labeled sample set.
- **FR-4 Conflict detection.** The system SHALL detect DIRECT, TEMPORAL, SCOPE,
  STRENGTH, and PARAMETER conflicts between obligations on the same topic, with
  severity, confidence, explanation, evidence, and resolution.
- **FR-5 Redundancy detection.** The system SHALL flag redundant and partially
  overlapping obligations.
- **FR-6 Staleness detection.** The system SHALL flag policies overdue for review
  (> 18 months), referencing deprecated technologies, or referencing superseded
  standards.
- **FR-7 Risk & health scoring.** The system SHALL compute per-policy health and an
  organization-wide governance score from severity, confidence, scope, staleness,
  duplication, and compliance impact.
- **FR-8 Graph.** The system SHALL build a policy knowledge graph in both
  whole-policy and obligation-level modes and serve it as React-Flow-ready JSON.
- **FR-9 Explainability.** Every finding SHALL include why it was flagged, the
  trigger text, the sections involved, and a likely resolution.
- **FR-10 Reports.** The system SHALL generate policy-health and conflict-audit
  reports as Markdown/JSON/HTML artifacts.
- **FR-11 Webhooks-in.** The system SHALL register webhooks and ingest events,
  re-running analysis for affected policies.
- **FR-12 Notifications.** The system SHALL notify compliance managers (not
  employees) when new HIGH findings appear (webhook-out / integration hook).
- **FR-13 Connectors.** The system SHALL expose a `BaseConnector` SPI and a
  `ConnectorManager`, with GitHub and Local Folder fully implemented.
- **FR-14 Compliance mapping.** Findings SHALL carry `compliance_impact` mapping to
  ISO/NIST/GDPR/COBIT clauses.

## 5. Non-Functional Requirements
- **NFR-1 Precision.** False-positive rate < 20% on the sample corpus.
- **NFR-2 Determinism.** The core detection path SHALL be deterministic and
  reproducible across runs (no network, no model randomness).
- **NFR-3 Performance.** Analysis of a 30-policy corpus completes in < 10 s on the
  deterministic path on commodity hardware.
- **NFR-4 Observability.** Structured JSON logging, `/health` and `/ready`
  endpoints, request IDs on every response.
- **NFR-5 Portability.** `docker compose up` brings up the full stack; the backend
  degrades to SQLite + in-process analysis without Postgres/Redis.
- **NFR-6 Security.** No secret is persisted in plaintext or returned by the API;
  webhook signatures verified when available.
- **NFR-7 Maintainability.** Modular packages, typed schemas, ≥ core-path test
  coverage; a new engineer can run the system on day one from the README.

---

## 6. Success Metrics & Acceptance Criteria

| Metric | Target | Acceptance test |
|---|---|---|
| Conflict detection rate | > 75% | `tests/ai/test_conflicts.py` on labeled pairs |
| Redundancy detection | > 70% | `tests/ai/test_redundancy.py` |
| Staleness detection | > 90% | `tests/ai/test_staleness.py` |
| False-positive rate | < 20% | `tests/ai/test_precision.py` (no false conflict on scoped/unrelated pairs) |
| Obligation extraction accuracy | > 80% | `tests/ai/test_obligations.py` |
| End-to-end run | passes | `POST /api/v1/analysis/run` returns findings + score |

**Definition of done for a phase:** the phase is usable end-to-end (endpoints
respond, tests pass, UI renders real data), not merely code-complete.

---

## 7. Information Flow (end-to-end)

1. **Configure** a connector (GitHub repo or local folder).
2. **Sync** pulls policy files → ingestion normalizes → Policy + versions stored.
3. **Analyze** runs the AI pipeline: obligations → similarity index → conflict /
   redundancy / staleness detectors → graph → risk/health scoring.
4. **Persist** findings, graph, and governance score.
5. **Serve** the operations console via REST; render graph, findings, timeline.
6. **Report** on demand → Markdown/HTML/JSON artifact.
7. **Notify** compliance managers on new HIGH findings.
8. **Re-trigger** automatically on webhook events (e.g. GitHub push) → back to (2).

---

## 8. In Scope vs Deferred (hackathon build)

**In scope (built & runnable):** ingestion; obligation extraction; direct /
temporal / scope / strength / parameter conflict detection; redundancy; staleness
(review-age, deprecated-tech, superseded-standard, orphaned-owner); risk & health
scoring; policy + obligation graph; explainable findings; policy-health and
conflict-audit reports; GitHub + Local Folder + Upload connectors; webhook-in
ingestion; compliance mapping; dashboard console; Docker + CI + tests.

**Deferred (roadmap):** PDF/DOCX ingestion; embeddings/LLM upgrade path wired but
optional; the 8 additional connectors (registered stubs); version-diff conflict
introduction analysis; NL query interface; automated LLM harmonization rewrites;
RBAC/SSO. See `docs/roadmap.md`.

---

## 9. Compliance-Manager Workflows

**Technical workflow:** connect source → run analysis → open Review Queue → sort by
severity × confidence → open Conflict Compare (side-by-side highlighted sections)
→ accept resolution suggestion or reassign to policy owner → export audit report.

**Legal/audit workflow:** open Compliance Mapping → confirm every active policy
maps to ISO 27001 §5.1/§5.2 review cadence → export Compliance Coverage report as
evidence that policies are consistent and reviewed → attach to audit file. The
platform's value is measurable **audit-overhead reduction**: the 20+ hours/quarter
spent manually reconciling policies collapses to reviewing a ranked, evidenced
findings list.

---

## 10. Roadmap
See `docs/roadmap.md` for the phased post-hackathon plan (embeddings upgrade,
remaining connectors, version-diff, NL query, harmonization, RBAC/SSO, multi-tenant).
