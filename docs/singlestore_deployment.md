# Deployment: Vercel (frontend) → Render (backend) → SingleStore (database)

Topology for the Policy Conflict & Staleness Detector (PCSD):

```
 Browser ──▶ Vercel (Next.js frontend) ──▶ Render (FastAPI backend) ──▶ SingleStore (durable DB)
             NEXT_PUBLIC_API_URL              CORS_ORIGINS                DATABASE_URL
```

The database holds **policy version control** (`policies`, `policy_versions`),
the immutable governance `audit_events`, conflicts, staleness findings, and all
other app state — so it survives every Render redeploy (unlike the previous
ephemeral SQLite file).

---

## 1. Backend deploy on Render — verified LIVE

- Service: `policy-guardian-backend` (`srv-d99kmrecjfls738d5kbg`)
- URL: https://policy-guardian-backend-wbge.onrender.com
- Deployed from `render.yaml` (Blueprint). Latest deploy status: **live**.

## 2. Database: SingleStore

The backend talks to SingleStore over the MySQL wire protocol via the
`singlestoredb` SQLAlchemy dialect (added to `requirements.txt`). Two SingleStore
DDL quirks are handled automatically in `app/core/db.py`:

- unlengthed `String` columns compile to `VARCHAR(1024)` (SingleStore rejects
  `VARCHAR` without a length);
- `FOREIGN KEY` constraints are stripped before `create_all` (SingleStore has no
  FK support) — ORM relationship joins are unaffected.

`DATABASE_URL` scheme is normalized in `app/core/config.py`, so any of these work:

```
singlestoredb://<user>:<password>@<host>:3306/policyguardian?ssl_disabled=False
singlestore://<user>:<password>@<host>:3306/policyguardian      # auto → singlestoredb://
postgresql://... / postgres://...                                # auto → postgresql+psycopg://
```

### 2a. Create the database (via the SingleStore MCP)

The MCP is registered in `.mcp.json` (`uvx singlestore-mcp-server`). It loads on
the next Claude Code session. From there:

1. List workspaces / connect to the target workspace.
2. `CREATE DATABASE IF NOT EXISTS policyguardian;`
3. Copy the workspace connection string (host, port 3306, admin user, password).

Tables are created automatically by the backend on first boot (`init_db`), so no
manual schema step is required.

### 2b. Point the backend at SingleStore

In the Render dashboard → `policy-guardian-backend` → **Environment**, set the
`DATABASE_URL` secret (declared `sync: false` in `render.yaml`, so it never lands
in git):

```
DATABASE_URL=singlestoredb://<user>:<password>@<host>:3306/policyguardian?ssl_disabled=False
```

Save → Render redeploys. Confirm health:

```
curl https://policy-guardian-backend-wbge.onrender.com/ready
# {"status":"ready","db":true,"analysis_engine":"deterministic"}
```

`SEED_ON_STARTUP=1` seeds the sample corpus once, only when the DB is empty
(`seed_if_empty` guards on the policy count), so it won't duplicate on redeploys.

## 3. Frontend on Vercel → backend

Set on the Vercel project (Settings → Environment Variables):

```
NEXT_PUBLIC_API_URL=https://policy-guardian-backend-wbge.onrender.com
```

The client (`frontend/lib/api.ts`) then calls `${NEXT_PUBLIC_API_URL}/api/v1`.

## 4. Backend CORS → frontend

In Render, set `CORS_ORIGINS` to the exact Vercel origin(s), comma-separated:

```
CORS_ORIGINS=https://<your-project>.vercel.app
```

---

## Remaining live steps (need SingleStore connection — next MCP session or manual)

- [ ] Create `policyguardian` database in the SingleStore workspace.
- [ ] Set `DATABASE_URL` secret on Render → redeploy → verify `/ready` shows `db:true`.
- [ ] Set `NEXT_PUBLIC_API_URL` on Vercel; set real `CORS_ORIGINS` on Render.
- [ ] Reminder: free-tier caveat does not apply to SingleStore here; the earlier
      Render free-Postgres path was dropped in favor of SingleStore.
