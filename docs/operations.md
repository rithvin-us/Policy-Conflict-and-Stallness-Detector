# Operations Runbook — verify, reset, and add policies

## 1. Reset all data (remove stale runtime state)

All findings, conflicts, obligations, connectors, and analysis runs live in the
database. "Removing stale data" = deleting the DB; it re-seeds fresh on next boot.

```bash
# SQLite (local dev): just delete the file, then restart the API.
rm -f backend/policyguardian.db
uvicorn app.main:app --reload      # re-seeds sample_data/policies + re-analyzes

# Docker Compose (Postgres): drop the volume.
docker compose down -v && docker compose up --build
```

To re-run analysis without wiping data (e.g. after editing policies):

```bash
curl -X POST http://localhost:8000/api/v1/analysis/run -H "Content-Type: application/json" -d '{}'
```

## 2. Verify it works — step by step

```bash
# A) Backend unit + integration + AI evaluation tests (deterministic)
cd backend
ANALYSIS_AS_OF=2026-07-11 pytest -q          # expect: 38 passed

# B) Boot the API and confirm it seeds + analyzes
rm -f policyguardian.db
ANALYSIS_AS_OF=2026-07-11 uvicorn app.main:app --port 8000
#   logs show: "seed complete" (10 policies), "analysis complete", "notified compliance managers"

# C) Hit the endpoints (new terminal)
curl -s localhost:8000/health
curl -s localhost:8000/api/v1/dashboard/overview        # governance score + counts
curl -s localhost:8000/api/v1/conflicts                 # ranked findings
curl -s "localhost:8000/api/v1/graph?mode=POLICY"       # graph JSON
open  localhost:8000/docs                                # interactive OpenAPI

# D) Frontend
cd frontend && npm install && npm run build && npm run dev
open http://localhost:3000
```

**Expected on the seed corpus (as of 2026-07-11):** 10 policies · 7 conflicts
(2 HIGH: password↔cloud rotation, retention↔GDPR erasure) · 4 redundancies ·
7 stale policies · 88% topic coverage · governance ≈ 69.

**What each success metric maps to (all enforced by tests):**
`test_conflicts.py` (>75% detection), `test_redundancy.py` (>70%),
`test_staleness.py` (>90%), `test_precision.py` (<20% FPR — asserts *only* the two
true HIGH pairs exist), `test_obligations.py` (>80% extraction).

## 3. Add / create new policies — four ways

### a) Manual upload (UI)
`Policies → + Upload policy` → paste title, owner, and policy text → **Ingest &
analyze**. The corpus is re-analyzed immediately and the new policy appears with
its health score and any conflicts.

### b) Manual upload (API)
```bash
curl -X POST http://localhost:8000/api/v1/policies/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Remote Access Policy",
    "owner": "Infrastructure",
    "raw_text": "Section 1: All employees must rotate their passwords every 60 days."
  }'
```
(This example creates a PARAMETER conflict with the Password Policy's 90-day rule.)

### c) Drop a file in the local corpus, then sync
1. Add a `.md` (or `.txt`) file to `sample_data/policies/` — optionally with the
   frontmatter block used by the seed files (`id`, `title`, `owner`,
   `last_reviewed`, `tags`). A bare `Section X: ... must ...` body also works.
2. Trigger the Local Folder connector to re-ingest:
   ```bash
   # find the connector id
   curl -s localhost:8000/api/v1/connectors
   curl -X POST localhost:8000/api/v1/connectors/<connector_id>/sync
   ```
   Or in the UI: `Sources & Webhooks → Sync now`.

### d) Connect a GitHub repository
`Sources & Webhooks → Add a source → GITHUB`, config `owner/repo` + path
(e.g. `policies`) → **Add connector** → **Sync now**. Register a push webhook so
changes re-analyze automatically:
```bash
curl -X POST localhost:8000/api/v1/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{"connector_id":"<id>","event_types":["push"]}'
# GitHub then POSTs to /api/v1/webhooks/github on each push → auto re-analysis.
```

## 4. Policy authoring tips (so the engine extracts well)

- Use obligation verbs: **must / shall / required / prohibited / should / may**.
- Keep one obligation per sentence; put the number + unit inline
  ("every 90 days", "for 7 years", "at least 12 characters").
- Name the scope explicitly ("all employees", "cloud systems", "developers",
  "EU residents") so scope-aware severity works.
- Include `last_reviewed` in frontmatter so staleness can be computed.
