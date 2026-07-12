# GitHub Integration — Continuous Policy Governance

This document describes the GitHub monitoring layer that turns Sentinal
from *manual upload* into *continuous governance*. It is an **extension** of the
existing platform — the connector framework, ingestion/versioning pipeline, the
deterministic AI engine, and the dashboard are all reused unchanged. Nothing here
replaces or duplicates existing modules.

---

## 1. Architecture

```
GitHub repo (sample_policies)
   │  push / pull_request  (webhook, HMAC-signed)
   ▼
POST /api/v1/webhooks/github        app/api/routes/sources.py
   │  1. read raw body
   │  2. verify X-Hub-Signature-256  app/services/webhook_security.py
   │  3. record WebhookEvent
   ▼
GitHub event orchestration          app/services/github_sync.py
   ├─ push  → identify changed *policy* files → fetch ONLY those at the commit SHA
   │          via the existing GitHubConnector → ingest_raw_policy() (versioned)
   │          → run_analysis() (existing engine, corpus-wide) → audit rows
   └─ pull_request → in-memory preview via analyze_corpus() (no DB mutation)
                     → conflict/compliance summary + suggested review
   ▼
Existing AI engine (unchanged)      app/ai_engine/*
   obligations · similarity · conflicts · duplicates · staleness · compliance · risk
   ▼
Persistence + surfaces
   ├─ Policy / PolicyVersion          version history
   ├─ Conflict / StalenessFinding      findings
   ├─ AuditEvent                       immutable audit trail (app/services/audit.py)
   └─ SSE broker                       live dashboard (app/services/events.py)
```

### Design principles applied
- **Open/Closed via the connector SPI.** `GitHubConnector` already subclasses
  `BaseConnector`; the webhook path never hardcodes GitHub-specific logic outside
  that connector. GitLab/Bitbucket/Drive slot in the same way (subclass +
  register in `connectors/manager.py`).
- **Single responsibility.** Signature verification, orchestration, audit, and
  live events are each their own small module.
- **Reuse over rewrite.** `ingest_raw_policy`, `run_analysis`, and
  `analyze_corpus` are the *existing* pipeline — the webhook simply feeds them.
- **Targeted, not wholesale.** A push re-downloads only the changed policy files
  (at the pushed commit SHA), not the whole repo.

### GitHub App–ready authentication
Auth is abstracted so migration to a GitHub App is seamless:

| Mode | How | Where |
|------|-----|-------|
| Public repo | no token needed | `GitHubConnector._headers()` |
| Local dev (PAT) | `GITHUB_TOKEN` env var (never persisted) | `settings.GITHUB_TOKEN` |
| Private repo | PAT with `repo` scope | same env var |
| **Future GitHub App** | swap `_headers()` to mint an installation token | single method |

Only `_headers()` changes for the App migration — connector callers, the sync
orchestration, and the webhook handler are untouched.

---

## 2. Webhook flow (push)

1. GitHub sends `POST /api/v1/webhooks/github` with `X-GitHub-Event: push` and
   `X-Hub-Signature-256: sha256=…`.
2. The handler reads the **raw** body and verifies the HMAC-SHA256 signature
   against `GITHUB_WEBHOOK_SECRET`. Invalid → `401`. (Empty secret = local dev,
   verification skipped.)
3. A `WebhookEvent` row is written (`PROCESSING`).
4. `github_sync.process_push`:
   - matches connectors whose configured `repo` equals `repository.full_name`;
   - computes the net changed paths across all commits;
   - keeps only **policy files** inside the connector's `path` (README, code,
     images are ignored via `GitHubConnector.is_policy_path`);
   - downloads each changed file **at the pushed commit SHA**;
   - `ingest_raw_policy` creates a new `PolicyVersion` when content changed
     (idempotent by content hash);
   - `run_analysis` recomputes conflicts / duplicates / staleness / compliance /
     risk (analysis is inherently cross-policy, so it runs once, not per file);
   - one **immutable `AuditEvent`** is appended per changed file with the commit
     provenance and the derived finding statuses.
5. `WebhookEvent` → `PROCESSED`; an SSE `webhook_processed` + `analysis_complete`
   event is published; connected dashboards refresh with no page reload.

`ping` events are acknowledged with a `pong` (no pipeline run).

---

## 3. Pull-request analysis

`pull_request` events (`opened` / `synchronize` / `reopened` / `ready_for_review`)
run a **non-destructive preview**:

- changed policy files are listed via the PR files API and fetched at the PR head
  SHA;
- the existing `analyze_corpus` runs over *current policies overlaid with the PR
  versions* — entirely in memory, the stored corpus is never mutated;
- the response includes a conflict summary, compliance impact, and a suggested
  review verdict (`APPROVE` / `COMMENT` / `CHANGES_REQUESTED`);
- an `AuditEvent` is recorded with `reviewer_status=PENDING`,
  `resolution_status=PREVIEW`.

**Future-ready:** `github_sync.maybe_comment_on_pr` is the single hook to enable
automatic PR review comments — it only needs a token/App with
`pull_requests: write` and `config["pr_comments"] = true`. The call site already
passes the full summary.

---

## 4. Audit trail

Every change writes an append-only `AuditEvent` (`app/models/__init__.py`).
Fields: repository, branch, commit SHA + URL, policy file, policy id, author,
timestamp, old/new content hash, conflict status, duplicate status, staleness
status, compliance impact, risk score, reviewer status, resolution status.

- **Search:** `GET /api/v1/audit?search=…&repo=…&author=…&conflict_status=…&reviewer_status=…`
- **Workflow only:** `PATCH /api/v1/audit/{id}` advances `reviewer_status` /
  `resolution_status`. Provenance fields (commit, hashes) are never mutable — the
  trail is tamper-evident.

---

## 5. Live updates (SSE)

`GET /api/v1/events/stream` is a Server-Sent Events endpoint. The Governance page
opens one `EventSource` and receives an event on every governance change
(`push_processed`, `pr_analyzed`, `analysis_complete`, `webhook_processed`,
`audit_updated`). The broker (`app/services/events.py`) is a zero-dependency
in-process pub/sub; for multi-worker production, swap its queue set for Redis
pub/sub behind the same `publish`/`subscribe` surface.

---

## 6. Localhost setup

```bash
# 1) Backend
cd backend
python -m pip install -r requirements.txt
cp .env.example .env            # then set GITHUB_WEBHOOK_SECRET (see below)
uvicorn app.main:app --reload --port 8000

# 2) Frontend (separate terminal)
cd frontend
npm install
npm run dev                     # http://localhost:3000  → Governance page
```

The backend seeds the existing `sample_data/policies` corpus on first boot, so
the dashboard is populated immediately.

### Environment (`backend/.env`)
```ini
GITHUB_WEBHOOK_SECRET=<a long random string>   # same value used in GitHub
GITHUB_TOKEN=ghp_xxx                            # optional; private repos / rate limits
ANALYSIS_AS_OF=2026-07-11                       # deterministic staleness
```

---

## 7. Exposing localhost to GitHub

GitHub must reach your machine. Use either tunnel.

### Cloudflare Tunnel
```bash
# install cloudflared, then:
cloudflared tunnel --url http://localhost:8000
# → https://<random>.trycloudflare.com
# Webhook Payload URL: https://<random>.trycloudflare.com/api/v1/webhooks/github
```

### ngrok
```bash
ngrok http 8000
# → Forwarding https://<random>.ngrok-free.app -> http://localhost:8000
# Webhook Payload URL: https://<random>.ngrok-free.app/api/v1/webhooks/github
```

---

## 8. GitHub configuration

1. In the platform, open **Sources & Webhooks**, add a **GITHUB** connector:
   `repo = owner/sample_policies`, `branch = main`, `path = policies` (or blank if
   the policies are at the repo root). Click **Register webhook** to mark it.
2. In the GitHub repo → **Settings → Webhooks → Add webhook**:
   - **Payload URL:** `https://<tunnel>/api/v1/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** the same value as `GITHUB_WEBHOOK_SECRET`
   - **Events:** *Let me select individual events* → **Pushes** and **Pull requests**
3. Save. GitHub sends a `ping`; you should see a `pong` and a `PROCESSED` event
   under **Sources & Webhooks → Webhook Events**.

---

## 9. Testing

- **Unit + integration:** `cd backend && python -m pytest` (see
  `app/tests/test_webhooks.py` — signature, targeting, PR preview, audit, versions).
- **No-GitHub local simulation:** `backend/scripts/simulate_webhook.py` signs and
  posts a payload exactly as GitHub would.
- **Full end-to-end walkthrough:** see [`../TESTING_THE_PIPELINE.md`](../TESTING_THE_PIPELINE.md).

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `401 Invalid webhook signature` | secret mismatch | make `GITHUB_WEBHOOK_SECRET` == GitHub webhook secret; restart backend |
| Webhook delivered, `changed_policies: 0` | connector `repo`/`path` doesn't match | ensure connector `repo` equals `repository.full_name` and files are under `path` |
| `matched_connectors: 0` | no GitHub connector for that repo | add the connector on Sources & Webhooks |
| Dashboard not updating live | SSE blocked by proxy | Cloudflare/ngrok pass SSE fine; corporate proxies may buffer — check `/api/v1/github/status` `live_subscribers` |
| `latest_commit: null` in status | private repo without token, or rate-limited | set `GITHUB_TOKEN` |
| GitHub "We couldn't deliver" | tunnel down / wrong URL | re-check tunnel URL ends in `/api/v1/webhooks/github` |
| Duplicate policy instead of new version | edited file lost its frontmatter `id:` | keep the `id:` field in each policy's frontmatter (the stable identity) |
