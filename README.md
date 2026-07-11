<div align="center">

# 🛡️ Policy Guardian AI
### Continuous Policy Governance & Compliance Intelligence Platform

Detects **conflicts, redundancy, and staleness** across an enterprise policy
corpus — with explainable, evidence-backed findings, a policy knowledge graph,
governance scoring, and audit-ready reports.

</div>

---

## The problem

Enterprises accumulate dozens of security & compliance policies written by
different teams over many years. They silently contradict each other — one policy
says *"rotate passwords every 90 days"*, another says *"do not rotate passwords;
enforce MFA"* — and nobody notices until an auditor does. Policy Guardian AI finds
those conflicts **before** the auditor, continuously.

## What it does

- **Ingests** policies from GitHub, local folders, or manual upload (extensible
  connector framework for 10 source types).
- **Extracts obligations** (must/shall/should + action + scope + parameters) with
  an explainable, rule-driven NLP engine.
- **Detects** direct / temporal / scope / strength / parameter **conflicts**,
  **redundancy**, and **staleness** (review-overdue, deprecated tech, superseded
  standards, orphaned owners).
- **Explains** every finding: the exact triggering text, the sections involved,
  the likely resolution, and the compliance clauses impacted (ISO 27001, NIST
  800-53, GDPR, COBIT).
- **Scores** per-policy health and an organization-wide governance score.
- **Visualizes** a policy knowledge graph (whole-policy and obligation-level).
- **Reports** audit-ready Markdown / HTML / JSON, and **notifies** compliance
  managers on new HIGH conflicts via webhook.
- **Re-analyzes** automatically on webhook events (e.g. GitHub push).

## Architecture

```
Sources ─▶ Connectors ─▶ Ingestion + Versioning ─▶ Policy Store (Postgres/SQLite)
                                                          │
                            Deterministic AI Engine ◀─────┘
              obligations · conflicts · redundancy · staleness · graph · risk
                                                          │
                     REST API (FastAPI) ─▶ Next.js Operations Console
```

Full detail in [`docs/architecture.md`](docs/architecture.md). Requirements in
[`docs/SRS.md`](docs/SRS.md). Frozen contracts in
[`docs/data-dictionary.md`](docs/data-dictionary.md) and
[`docs/api-contracts.md`](docs/api-contracts.md).

**Tech:** FastAPI · SQLAlchemy 2 · Pydantic v2 · Next.js 14 · TypeScript ·
Tailwind · Framer Motion · React Flow · Recharts · Docker · GitHub Actions.

> **Design choice that matters:** the AI engine is **pure-Python and
> deterministic** — it runs and passes every detection test with *zero* model
> downloads (works on Python 3.11–3.14). Sentence-Transformers / spaCy / FAISS /
> scikit-learn are an **optional** semantic-upgrade layer, never a hard
> dependency. This guarantees the code actually runs, and keeps precision high.

---

## Run it

### Option A — Docker Compose (full stack: Postgres + Redis + API + Web)

```bash
docker compose up --build
# Web  → http://localhost:3000
# API  → http://localhost:8000/docs
```

The backend seeds the sample policy corpus and runs the first analysis on boot,
so the dashboard is populated immediately.

### Option B — Local dev (no Docker, no ML deps)

```bash
# 1) Backend  (http://localhost:8000)
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 2) Frontend (http://localhost:3000)
cd frontend
npm install
npm run dev
```

### Test

```bash
cd backend && pytest -q          # 37 tests: AI evaluation + API + connectors
cd frontend && npm run build     # type-checked production build
```

---

## What's implemented / stubbed / future

**Implemented & runnable:** obligation extraction; direct/temporal/scope/strength/
parameter conflict detection; redundancy; staleness (4 signals); risk + governance
scoring; policy & obligation graphs; explainable findings; compliance mapping;
policy-health / conflict-audit / staleness / coverage reports (MD/HTML/JSON);
GitHub + Local Folder + Upload connectors; webhook ingestion + re-analysis;
compliance-manager notifications; full dashboard console; Docker + CI + 37 tests.

**Stubbed (registered behind the same `BaseConnector` interface):** GitLab,
Bitbucket, Google Drive, OneDrive, SharePoint, Slack, Teams connectors —
`NOT_CONFIGURED` until implemented.

**Future (see [`docs/roadmap.md`](docs/roadmap.md)):** embeddings/LLM upgrade
(interface wired, opt-in), version-diff conflict introduction, NL policy query,
automated harmonization rewrites, PDF/DOCX ingestion, RBAC/SSO, multi-tenant.

---

## Success metrics (from the challenge brief)

| Metric | Target | Status |
|---|---|---|
| Conflict detection rate | > 75% | ✅ enforced by `tests/ai/test_conflicts.py` |
| Redundancy detection | > 70% | ✅ `test_redundancy.py` |
| Staleness detection | > 90% | ✅ `test_staleness.py` |
| False-positive rate | < 20% | ✅ `test_precision.py` (0% on curated corpus) |
| Obligation extraction accuracy | > 80% | ✅ `test_obligations.py` |

---

## Executive summary

Policy Guardian AI turns a pile of contradictory, aging policies into a ranked,
evidenced findings list a compliance manager can act on in minutes — collapsing
the ~20 hours/quarter spent manually reconciling policies, and eliminating the
"conflicting policy" audit finding before the auditor arrives. Every alert is
explainable and cites the exact policy text, so owners trust it and fix it fast.

## Technical summary

A deterministic, rule-driven NLP engine extracts obligations and classifies
cross-policy relationships with an explicit, auditable severity matrix tuned for
precision. It is wrapped by a modular FastAPI backend (connector framework,
webhook ingestion, content-hash versioning, report generation, structured
logging) and a Next.js operations console (governance scoring, React Flow graph,
side-by-side conflict comparison). It degrades gracefully to SQLite + synchronous
execution + lexical similarity, so it runs anywhere with no GPU and no model
download — while exposing an opt-in embeddings path for higher semantic recall.

## Repository layout

```
docs/            SRS, architecture, API + data contracts, roadmap
sample_data/     seed policy corpus (the shared test fixtures)
backend/         FastAPI app: ai_engine, risk_scoring, graph_builder,
                 explainability, models, schemas, api, connectors, services, tests
frontend/        Next.js console: app/ pages, components/, lib/ client
docker-compose.yml · .github/workflows/ci.yml
```
