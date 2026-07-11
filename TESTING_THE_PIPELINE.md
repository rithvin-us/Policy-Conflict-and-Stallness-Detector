# Testing the Continuous Governance Pipeline (end to end)

This guide walks the **entire** GitHub → AI → dashboard pipeline, using the
policy files that already exist in the repo (`sample_data/policies`). Two tracks:

- **Track A — Local simulation** (fastest, no GitHub account, no tunnel).
- **Track B — Real GitHub** (push a commit to `sample_policies`, receive a real
  webhook).

Both exercise the same code path: verify signature → download only the changed
policy → existing AI engine re-analyzes → audit + version history → live
dashboard update.

---

## 0. Prerequisites

```bash
# Backend
cd backend
python -m pip install -r requirements.txt

# Frontend (separate terminal)
cd frontend
npm install
```

---

## 1. Automated tests (proves the pipeline logic)

```bash
cd backend
python -m pytest -q
```

Expect **all tests green**, including `app/tests/test_webhooks.py`:
- `test_webhook_rejects_bad_signature_when_secret_set` — HMAC enforcement
- `test_push_ingests_only_policy_files_and_audits` — targeted ingest + audit
- `test_push_creates_new_policy_version` — version history
- `test_pull_request_preview_produces_verdict` — PR analysis
- `test_audit_review_transition` — audit workflow

---

## Track A — Local simulation (no GitHub)

### A1. Start the backend
```bash
cd backend
export GITHUB_WEBHOOK_SECRET="test-secret-123"     # PowerShell: $env:GITHUB_WEBHOOK_SECRET="test-secret-123"
uvicorn app.main:app --reload --port 8000
```
On first boot it seeds the 10 existing sample policies and runs the first
analysis. Sanity check:
```bash
curl -s http://localhost:8000/api/v1/dashboard/overview | python -m json.tool
```

### A2. Start the frontend and open the Governance page
```bash
cd frontend
npm run dev
# open http://localhost:3000/governance
```
The **Live Governance Feed** shows a pulsing “live” indicator (SSE connected).

### A3. Connect the sample repo
On **Sources & Webhooks**, add a **GITHUB** connector:
- repo: `rithvin-us/sample_policies`
- branch: `main`
- path: `policies` (leave blank if the files sit at the repo root)

Then click **Register webhook** on that connector. Confirm on the Governance
page → **Repository Health** that the repo appears (a `GITHUB_TOKEN` is only
needed for private repos / higher rate limits).

### A4. Fire a simulated push
The simulator signs the payload exactly like GitHub and names an **existing**
policy file (the backend downloads the real file from the connected repo):

```bash
cd backend
export GITHUB_WEBHOOK_SECRET="test-secret-123"
python scripts/simulate_webhook.py push \
    --repo rithvin-us/sample_policies \
    --file policies/password_policy.md \
    --author "you@example.com"
```

Expected response:
```json
{ "received": true, "matched_connectors": 1, "changed_policies": 1,
  "files": ["policies/password_policy.md"] }
```

### A5. Watch it land — no page refresh
On the Governance page, **within a second**:
- **Live Governance Feed** gains `Push analyzed` and `Re-analysis` entries;
- **Audit Timeline** gains a row for `policies/password_policy.md` with the
  commit, author, finding badges (conflict/dup/stale), risk score, and a review
  dropdown;
- **Repository Health** updates “Last sync”.

Verify via API too:
```bash
curl -s "http://localhost:8000/api/v1/audit?search=password_policy" | python -m json.tool
curl -s "http://localhost:8000/api/v1/policies/POL-PWD-001/versions" | python -m json.tool
curl -s "http://localhost:8000/api/v1/github/status" | python -m json.tool
```

### A6. Simulate a pull request (preview, no corpus change)
```bash
python scripts/simulate_webhook.py pr \
    --repo rithvin-us/sample_policies \
    --number 1 --file policies/password_policy.md
```
Response includes `"suggested_review": "APPROVE" | "COMMENT" | "CHANGES_REQUESTED"`
and a conflict/compliance summary. The stored corpus is untouched; a `PENDING`
audit row (resolution `PREVIEW`) is added.

---

## Track B — Real GitHub webhook

### B1. Expose localhost
```bash
cloudflared tunnel --url http://localhost:8000
#   or
ngrok http 8000
```
Copy the public HTTPS URL.

### B2. Configure the GitHub webhook
In `rithvin-us/sample_policies` → **Settings → Webhooks → Add webhook**:
- **Payload URL:** `https://<tunnel>/api/v1/webhooks/github`
- **Content type:** `application/json`
- **Secret:** same as `GITHUB_WEBHOOK_SECRET`
- **Events:** Pushes **and** Pull requests

Save → GitHub sends `ping` → the platform replies `pong` and a `PROCESSED`
event appears under **Webhook Events**.

### B3. Edit an existing policy and push
```bash
git clone https://github.com/rithvin-us/sample_policies.git
cd sample_policies
# edit an EXISTING file, e.g. tighten a rule in policies/password_policy.md
git commit -am "Tighten password rotation to 14 days"
git push origin main
```

### B4. Observe the full chain
GitHub delivers the webhook → backend verifies the signature → downloads **only**
`password_policy.md` at the pushed commit → the existing engine re-analyzes →
audit + new version written → the Governance dashboard updates live. Confirm on
`http://localhost:3000/governance` and in GitHub → webhook **Recent Deliveries**
(a `200` with the `changed_policies` body).

---

## Verification checklist (maps to the requirement's 14 steps)

| # | Expectation | Where to confirm |
|---|-------------|------------------|
| 1 | FastAPI runs locally | `curl :8000/health` |
| 2 | Tunnel exposes localhost | cloudflared/ngrok URL |
| 3 | GitHub webhook configured | GitHub → Webhooks |
| 4–6 | Edit existing policy, commit, push | `git push` |
| 7–8 | GitHub → webhook received | Webhook Events table / GitHub deliveries |
| 9 | Signature verified | bad secret ⇒ `401`; good ⇒ `200` |
| 10 | Only changed policy downloaded | response `files` = just the edited file |
| 11 | Fed to existing AI engine | logs `analysis complete`; overview counts change |
| 12 | conflicts/dupes/stale/similarity/graph/audit/compliance updated | Conflicts, Staleness, Graph, Compliance, Audit pages |
| 13 | Dashboard updates automatically | Live Governance Feed (no refresh) |
| 14 | Compliance manager sees finding immediately | Audit Timeline row + HIGH-conflict notification |

---

## Troubleshooting
See **[docs/github_integration.md §10](docs/github_integration.md#10-troubleshooting)**.
Most common: the webhook **Secret** must exactly equal `GITHUB_WEBHOOK_SECRET`,
and the connector `repo` must equal the repo's `owner/name`.
