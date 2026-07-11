x# Architecture — Policy Guardian AI

## 1. System context

```
┌────────────┐   sync / webhook   ┌──────────────────────────────────────────┐
│  Sources   │ ─────────────────► │            Backend (FastAPI)             │
│ GitHub     │                    │                                          │
│ Local dir  │                    │  Connectors → Ingestion → Policy Store   │
│ Upload     │                    │                    │                     │
└────────────┘                    │            AI Policy Intelligence        │
                                  │   obligations · similarity · conflicts   │
                                  │   redundancy · staleness · graph · risk  │
                                  │                    │                     │
                                  │      REST /api/v1 · Reports · Notify      │
                                  └───────────────┬──────────────────────────┘
                                                  │ JSON
                                  ┌───────────────▼──────────────────────────┐
                                  │        Frontend (Next.js console)         │
                                  │  overview · findings · graph · reports    │
                                  └──────────────────────────────────────────┘
   Infra: PostgreSQL (SQLite dev) · Redis + Celery (sync/notify) · Docker Compose · GH Actions
```

## 2. Repository layout (monorepo)

```
PolicyConflictDetection/
├── docs/                     # Agent A — SRS, contracts, architecture, roadmap
├── sample_data/policies/     # seed corpus (shared test fixtures)
├── backend/
│   └── app/
│       ├── main.py           # FastAPI app factory + router mount
│       ├── core/             # config, logging, db, ids, security
│       ├── models/           # SQLAlchemy ORM (mirrors data-dictionary)
│       ├── schemas/          # Pydantic contracts (mirrors data-dictionary)
│       ├── api/              # routers (one per resource group)
│       ├── services/         # ingestion, analysis orchestration, reports, notify
│       ├── connectors/       # BaseConnector, github, local_folder, manager
│       ├── workers/          # celery app + tasks (sync, analyze, notify)
│       ├── ai_engine/        # Agent C — parsing → obligations → detectors → graph
│       ├── risk_scoring/     # Agent C — health & governance scoring
│       ├── graph_builder/    # Agent C — NetworkX/pure graph → React Flow JSON
│       ├── explainability/   # Agent C — ExplanationPayload builder
│       └── tests/            # backend + tests/ai (Agent C eval)
├── frontend/                 # Agent D — Next.js 14 App Router console
├── docker-compose.yml        # full stack
├── .github/workflows/ci.yml  # lint + test both tiers
└── README.md
```

> The AI engine lives under `backend/app/` (`ai_engine`, `risk_scoring`,
> `graph_builder`, `explainability`) so backend imports it directly without an
> extra service hop. The deliverable paths in the brief (`app/ai_engine`, …) map
> to `backend/app/ai_engine`, … .

## 3. AI Policy Intelligence pipeline (Agent C)

```
raw_text
  └─► parser.split_sections()            # sections by "Section X.Y" / md headings
        └─► obligations.extract()        # modal→strength, verb→action, negation→polarity,
              │                          #   topic map, scope map, param extraction
              ├─► similarity.index()     # lexical (TF-IDF/Jaccard/difflib); optional embeddings
              ├─► conflicts.detect()     # DIRECT/TEMPORAL/SCOPE/STRENGTH/PARAMETER
              ├─► redundancy.detect()    # REDUNDANCY / PARTIAL_REDUNDANCY
              └─► staleness.detect()     # review-age / deprecated-tech / superseded / orphan
                    └─► graph_builder.build()   # policy & obligation graphs → React Flow
                          └─► risk_scoring.score()   # per-policy health + governance
                                └─► explainability.build()  # ExplanationPayload per finding
```

**Determinism contract.** Every function above is pure and deterministic given the
corpus. The optional embedding layer (`similarity.py`) is the *only* place ML is
used, and it only *reorders/adds* candidate pairs — it never changes a HIGH direct
conflict into a non-finding. This keeps NFR-2 (determinism) and precision intact.

## 4. Connector Framework (Agent B)

```
BaseConnector (ABC)
  ├─ verify() -> ConnectorStatus
  ├─ list_policies() -> [PolicyRef]
  ├─ fetch(ref) -> RawPolicy{ path, text, meta }
  └─ supports_webhooks() -> bool

ConnectorManager
  ├─ register(type, cls)         # registry of all 10 connector types
  ├─ get(connector_id)           # instantiate from stored config
  └─ sync(connector_id)          # list → fetch → ingest → analyze

Implemented: GitHubConnector, LocalFolderConnector, UploadConnector.
Registered stubs (NOT_CONFIGURED, same interface): GitLab, Bitbucket, GoogleDrive,
OneDrive, SharePoint, Slack, Teams.
```

Adding a connector = subclass `BaseConnector`, register it, done. No changes to
ingestion, analysis, or the API.

## 5. Ingestion & versioning (Agent B)
`services/ingestion.py` normalizes a `RawPolicy` into a `Policy` + first
`PolicyVersion`. Re-ingest with changed `raw_text` → new `PolicyVersion`, bump
`version`, update `updated_at`, emit a TimelineEvent. Content hash dedupes no-op
syncs. Version history feeds the roadmap version-diff feature.

## 6. Webhooks (Agent B)
`api/webhooks.py` accepts provider payloads at `/api/v1/webhooks/{connector}`,
verifies HMAC signature when present, stores a `WebhookEvent` (RECEIVED), enqueues
a Celery task to re-sync affected paths, then marks PROCESSED. Falls back to
synchronous processing when Redis/Celery is absent (NFR-5).

## 7. Notifications (Agent B/services)
`services/notify.py` fires a webhook-out / integration hook to compliance managers
when analysis produces a *new* HIGH conflict. Employees are never notified
(FR-12). Delivery is pluggable (Slack/Teams/email in roadmap); the hackathon build
logs + persists the notification and posts to a configurable outbound URL.

## 8. Reliability & degradation (NFR-5)
| Dependency | Present | Absent → fallback |
|---|---|---|
| PostgreSQL | primary store | SQLite file `./policyguardian.db` |
| Redis/Celery | async sync + notify | in-process synchronous execution |
| sentence-transformers/spaCy/FAISS | semantic upgrade | lexical similarity core |

The system is fully functional with **none** of the optional dependencies —
critical given the target runtime is Python 3.14.

## 9. Observability (NFR-4)
Structured JSON logs (`core/logging.py`) with `request_id`; `/health` and `/ready`
probes; every finding traces to source spans for audit reproducibility.
