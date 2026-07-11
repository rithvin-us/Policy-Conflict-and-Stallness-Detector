# Policy Guardian AI — Frontend

Next.js 14 (App Router) + TypeScript + Tailwind + Framer Motion + React Flow +
Recharts. A dark "policy operations console" — deliberately not a generic SaaS
dashboard.

## Run locally

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The app proxies `/api/*` to the backend (default `http://localhost:8000`, override
with `BACKEND_INTERNAL_URL`). Start the backend first (see `../backend/README.md`).

## Scripts
- `npm run dev` — dev server
- `npm run build` / `npm start` — production build (standalone output)
- `npm run typecheck` — `tsc --noEmit`
- `npm run lint` — Next ESLint

## Structure

| Path | View |
|---|---|
| `app/page.tsx` | Governance overview — score gauge, KPIs, review queue, timeline |
| `app/conflicts/` | Findings table + side-by-side conflict compare (highlighted spans) |
| `app/staleness/` | Staleness surveillance |
| `app/graph/` | React Flow policy / obligation graph explorer |
| `app/policies/` | Policy library + detail + upload |
| `app/compliance/` | ISO/NIST/GDPR/COBIT coverage map |
| `app/connectors/` | Sources, sync, add-connector, webhook events |
| `app/reports/` | Generate + download audit reports |
| `lib/api.ts` | Typed API client (consumes only backend contracts) |
| `lib/types.ts` | TypeScript mirror of `docs/data-dictionary.md` |
| `components/` | Gauge, charts, graph, conflict-compare, UI primitives |

## UX assumptions
- Single operator persona: the compliance manager (no auth/RBAC in this build).
- All data comes from the backend; the frontend invents no fields.
- Colors encode severity consistently: HIGH = red, MEDIUM = amber, LOW = blue,
  healthy = teal.
