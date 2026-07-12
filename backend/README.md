# Sentinal — Backend

FastAPI service: connectors → ingestion → deterministic AI analysis → REST API.

## Run locally (no Docker, no ML deps)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # optional
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- On first boot the app seeds `../sample_data/policies`, runs analysis, and
  populates the dashboard automatically — no manual steps.

## Test

```bash
cd backend
pytest -q            # 37 tests: AI evaluation + API + connectors
```

## Layout

| Path | Responsibility |
|---|---|
| `app/ai_engine/` | obligation extraction, conflict/redundancy/staleness detection, parser |
| `app/risk_scoring/` | per-policy health + governance score |
| `app/graph_builder/` | policy / obligation graph → React-Flow JSON |
| `app/explainability/` | ExplanationPayload builder |
| `app/models/` | SQLAlchemy ORM (mirrors `docs/data-dictionary.md`) |
| `app/schemas/` | Pydantic requests + ORM→contract serializers |
| `app/connectors/` | `BaseConnector` SPI, GitHub / Local / Upload + stubs, manager |
| `app/services/` | ingestion, analysis orchestration, reports, notify, seed |
| `app/api/routes/` | REST routers (see `docs/api-contracts.md`) |
| `app/workers/` | optional Celery app + synchronous dispatch fallback |

## Configuration

All via environment (see `.env.example`). Notable:
- `DATABASE_URL` — SQLite default; Postgres DSN in production.
- `ANALYSIS_AS_OF` — fixed reference date for deterministic staleness.
- `POLICYGUARDIAN_USE_EMBEDDINGS=1` — enable the optional embeddings layer
  (`requirements-ml.txt`).
- `NOTIFY_WEBHOOK_URL` — outbound compliance-manager notifications.

## Graceful degradation
Runs with **none** of Postgres / Redis / Celery / ML libraries installed:
SQLite + synchronous execution + deterministic lexical similarity.
