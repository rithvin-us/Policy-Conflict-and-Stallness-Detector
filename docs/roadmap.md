# Roadmap — Sentinal

## Now (hackathon build — shipped & runnable)
- Ingestion (GitHub, Local Folder, Upload) + normalization + versioning
- Obligation extraction (strength/polarity/scope/topic/parameters)
- Conflict detection: DIRECT, TEMPORAL, SCOPE, STRENGTH, PARAMETER
- Redundancy / partial-overlap detection
- Staleness: review-age, deprecated-tech, superseded-standard, orphaned-owner
- Risk + governance scoring; policy & obligation graphs
- Explainable findings, compliance mapping (ISO/NIST/GDPR/COBIT)
- Policy-health & conflict-audit reports (MD/HTML/JSON)
- Webhook-in ingestion + compliance-manager notifications
- Operations console (Next.js) + Docker Compose + CI + tests

## Next (Level 2 — Advanced Intelligence)
- **Embeddings upgrade** wired but optional: activate sentence-transformers + FAISS
  for semantic near-duplicate / near-conflict recall (interface already in
  `ai_engine/similarity.py`).
- **Scope-aware resolution** deepening: department/system/geo scope graphs.
- **Policy-change impact analysis**: on update, compute the blast radius of
  affected obligations across the graph.
- **LLM harmonization suggestions**: generate rewrite proposals to resolve a
  conflict (gated behind an opt-in provider config).

## Later (Level 3 — Enterprise)
- **Version-diff analysis**: diff policy versions, detect *introduced* conflicts.
- **Regulatory mapping** to specific GDPR articles / NIST controls / ISO clauses at
  the obligation level (beyond the current finding-level mapping).
- **Org-wide coverage analysis**: which topics have *no* policy coverage.
- **NL query interface**: "Which policies cover encryption?"
- **RBAC/SSO**, multi-tenant, and full audit trail export.

## Connector expansion
GitLab, Bitbucket, Google Drive, OneDrive, SharePoint, Slack, Teams — each is a
`BaseConnector` subclass; the registry and manager already accept them. Priority
order: GitLab → Bitbucket → Google Drive → SharePoint → Slack/Teams.

## Ingestion formats
PDF and DOCX extraction (currently text/markdown only).

## Ops hardening
Alembic migrations (currently `create_all` bootstrap), Prometheus metrics,
rate limiting, and secret-store integration for connector credentials.
