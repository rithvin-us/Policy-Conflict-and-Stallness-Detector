# How to Use Policy Guardian AI

A step-by-step guide to running, exploring, and demoing **Policy Guardian AI** —
the continuous policy conflict, redundancy, and staleness detector.

> Originally built for the *Policy Conflict & Staleness Detector* challenge brief (Société Générale).

> For system design details see `docs/architecture.md`, `docs/SRS.md`, and
> `docs/api-contracts.md`. This file is the practical "how do I run and use it"
> guide.

---

## 1. What this tool does, in one paragraph

Enterprises accumulate dozens of security and compliance policies written by
different teams over many years. They silently contradict each other, duplicate
each other, and go stale. Policy Guardian AI ingests your policy corpus,
extracts every obligation ("must / shall / should ..."), and automatically
detects **conflicts**, **redundancy**, and **staleness** — with an explainable,
evidence-backed reason and a suggested resolution for every finding, plus a
governance score and audit-ready reports.

---

## 2. Prerequisites

- **Docker + Docker Compose** (easiest path), *or*
- **Python 3.11+** and **Node.js 18+** for local dev without Docker.
- No GPU, no API keys, and no model downloads are required — the core AI engine
  is pure Python and fully deterministic.

---

## 3. Running it — Option A: Docker Compose (recommended)

```bash
docker compose up --build
```

This brings up Postgres, Redis, the FastAPI backend, and the Next.js frontend
together. The backend automatically seeds the sample policy corpus
(`sample_data/policies/`) and runs the first analysis on boot, so the dashboard
is populated the moment it's up.

- **Web console:** http://localhost:3000
- **API + interactive docs:** http://localhost:8000/docs

---

## 4. Running it — Option B: Local dev (no Docker)

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Runs at http://localhost:8000 and falls back to a local SQLite file
(`policyguardian.db`) since Postgres isn't required for local dev.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Runs at http://localhost:3000.

**Run the test suite** (37 tests: AI evaluation + API + connectors):

```bash
cd backend && pytest -q
cd frontend && npm run build     # type-checked production build
```

---

## 5. A guided first walkthrough of the console

Once the app is running, visit **http://localhost:3000** and follow this order —
it mirrors how a compliance manager would actually use the tool:

### Step 1 — Governance Overview (`/`)
The landing page. Shows the organization-wide **governance score**, a severity
breakdown (HIGH / MEDIUM / LOW), a recent-activity timeline, and the top items in
the review queue. This is the "state of your policy corpus" at a glance.

### Step 2 — Conflicts & Redundancies (`/conflicts`)
The triage view. Every conflict and redundancy is listed, ranked by risk, with
filters for severity and conflict type (DIRECT / TEMPORAL / SCOPE / STRENGTH /
PARAMETER). Click any row to open the **side-by-side Conflict Compare** view,
which highlights the exact conflicting sentences in both policies and shows the
suggested resolution.

**Try this on the seed data:** open the HIGH conflict between the **Password
Policy** ("all employees must rotate their passwords every 90 days") and the
**Cloud Security Policy** ("password rotation shall not be required for cloud
systems; MFA replaces the need for periodic credential changes"). This is a
real, explainable STRENGTH/DIRECT conflict the engine catches automatically.

### Step 3 — Policy Graph Explorer (`/graph`)
A visual knowledge graph of the whole corpus. Toggle between **whole-policy**
mode (nodes = policies, edges = conflicts/redundancy/shared topics) and
**obligation-level** mode (nodes = individual obligations). Useful for spotting
clusters of policies that all touch the same topic (e.g. authentication) and
therefore need coordinated review.

### Step 4 — Policy Library (`/policies`)
Every ingested policy with its health score, owner, version, and last-reviewed
date, sorted worst-health-first. Click a policy to see its full text, extracted
obligations, and every finding that references it. Use **+ Upload policy** to
add a new one and watch it get analyzed immediately (see §6).

### Step 5 — Staleness Surveillance (`/staleness`)
Everything flagged as review-overdue, referencing deprecated technology (e.g.
SHA-1, TLS 1.0), referencing a superseded standard, or with an orphaned owner.
Each row shows the age, the evidence, and a recommendation.

### Step 6 — Compliance Mapping (`/compliance`)
Coverage against ISO 27001, NIST SP 800-53, GDPR, and COBIT 2019 — which
clauses are covered by an active, reviewed policy and which have open findings.
This is the audit-evidence view.

### Step 7 — Sources & Webhooks (`/connectors`)
Configure where policies come from: **Local Folder**, **GitHub**, or manual
**Upload** are fully implemented (7 more — GitLab, Bitbucket, Google Drive,
OneDrive, SharePoint, Slack, Teams — are registered stubs behind the same
interface, ready to be built out). Register a GitHub webhook here so a policy
push automatically re-triggers analysis.

### Step 8 — Reports (`/reports`)
Generate audit-ready **Policy Health**, **Conflict Audit**, **Staleness**, or
**Compliance Coverage** reports as Markdown, HTML, or JSON — ready to attach to
an audit file.

---

## 6. Adding your own policies (4 ways)

**a) Manual upload via UI** — `Policies → + Upload policy` → paste title, owner,
and policy text → **Ingest & analyze**. Re-analyzes the whole corpus immediately.

**b) Manual upload via API:**

```bash
curl -X POST http://localhost:8000/api/v1/policies/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Remote Access Policy",
    "owner": "Infrastructure",
    "raw_text": "Section 1: All employees must rotate their passwords every 60 days."
  }'
```

This example deliberately creates a PARAMETER conflict with the seeded Password
Policy's 90-day rule — a good way to see conflict detection fire live.

**c) Drop a file in `sample_data/policies/`, then sync** the Local Folder
connector (`Sources & Webhooks → Sync now`, or `POST /api/v1/connectors/<id>/sync`).

**d) Connect a GitHub repository** — `Sources & Webhooks → Add a source →
GITHUB`, set `owner/repo` + path, **Add connector → Sync now**, then register a
push webhook so future commits auto-analyze.

**Writing tips for good extraction:** use obligation verbs (must / shall /
required / prohibited / should / may), keep one obligation per sentence, put the
number + unit inline ("every 90 days"), name the scope explicitly ("all
employees", "cloud systems"), and include `last_reviewed` in frontmatter so
staleness can be computed.

---

## 7. Resetting / verifying the environment

```bash
# Reset local SQLite state and re-seed
rm -f backend/policyguardian.db
uvicorn app.main:app --reload

# Reset the full Docker stack (Postgres volume)
docker compose down -v && docker compose up --build

# Re-run analysis without wiping data
curl -X POST http://localhost:8000/api/v1/analysis/run -H "Content-Type: application/json" -d '{}'
```

**Expected result on the seed corpus:** 10 policies · 7 conflicts (2 HIGH) · 4
redundancies · 7 stale policies · 88% topic coverage · governance score ≈ 69.

---

## 8. Quick API tour (for judges/reviewers who want to skip the UI)

```bash
curl -s localhost:8000/health                              # liveness
curl -s localhost:8000/api/v1/dashboard/overview            # governance score + counts
curl -s localhost:8000/api/v1/conflicts                     # ranked findings
curl -s "localhost:8000/api/v1/graph?mode=POLICY"            # graph JSON
open  localhost:8000/docs                                    # interactive OpenAPI (Swagger)
```

---

## 9. What's implemented vs. future work

| Status | Items |
|---|---|
| **Implemented & runnable** | Obligation extraction; DIRECT/TEMPORAL/SCOPE/STRENGTH/PARAMETER conflict detection; redundancy; staleness (4 signals); risk + governance scoring; policy & obligation graphs; explainable findings; compliance mapping; MD/HTML/JSON reports; GitHub + Local Folder + Upload connectors; webhook ingestion + re-analysis; compliance-manager notifications; full dashboard console; Docker + CI + 37 tests |
| **Stubbed (same interface, `NOT_CONFIGURED`)** | GitLab, Bitbucket, Google Drive, OneDrive, SharePoint, Slack, Teams connectors |
| **Roadmap** | Embeddings/LLM semantic upgrade (interface already wired, opt-in); version-diff conflict introduction; natural-language policy query; automated harmonization rewrites; PDF/DOCX ingestion; RBAC/SSO; multi-tenant |

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Dashboard shows no data | Backend hasn't seeded/analyzed yet — check backend logs for "seed complete" / "analysis complete", or `POST /api/v1/analysis/run` |
| `docker compose up` fails on ports 3000/8000 | Another process is using the port — stop it or edit `docker-compose.yml` port mappings |
| Frontend can't reach API | Confirm `NEXT_PUBLIC_API_URL` (or equivalent env var) points at `http://localhost:8000` |
| Tests fail with date-dependent assertions | Set `ANALYSIS_AS_OF=2026-07-11` before running `pytest` to match the seed corpus's expected staleness window |

---

*Policy Guardian AI* — Continuous policy governance and compliance intelligence platform. See `README.md` for the executive/technical summary and `docs/roadmap.md` for what's next. Originally developed for the Policy Conflict & Staleness Detector challenge brief.
