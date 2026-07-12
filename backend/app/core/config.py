"""Runtime configuration.

Plain ``os.getenv`` (no pydantic-settings dependency) so the app boots with zero
extra packages. Every setting has a safe local default; production overrides via
environment variables (see ``.env.example``).
"""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


def _normalize_db_url(url: str) -> str:
    """Coerce a Postgres DSN onto the installed driver (psycopg 3).

    Render (and Heroku-style providers) inject ``DATABASE_URL`` as
    ``postgres://`` or ``postgresql://`` with no driver suffix. SQLAlchemy maps
    both to the psycopg2 dialect, which is *not* installed — only ``psycopg``
    (v3) is in requirements — so the app would crash on boot. Rewrite the scheme
    to the explicit ``postgresql+psycopg://`` dialect. SQLite and already-qualified
    URLs pass through untouched.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    # SingleStore: accept the short scheme and target the installed dialect.
    if url.startswith("singlestore://"):
        return "singlestoredb://" + url[len("singlestore://"):]
    return url


class Settings:
    APP_NAME = "Sentinal"
    VERSION = "1.0.0"
    API_PREFIX = "/api/v1"

    # SQLite by default; set DATABASE_URL to a Postgres DSN in production.
    # Normalized so a bare Render/Heroku ``postgres(ql)://`` DSN targets psycopg 3.
    DATABASE_URL = _normalize_db_url(
        os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'policyguardian.db'}")
    )

    # Redis/Celery are optional — absent => synchronous in-process execution.
    REDIS_URL = os.getenv("REDIS_URL", "")
    USE_CELERY = os.getenv("USE_CELERY", "0") == "1"

    # Seed corpus disabled by default — dashboard starts empty. Set to "1" for local dev demos.
    SEED_ON_STARTUP = os.getenv("SEED_ON_STARTUP", "0") == "1"
    SEED_POLICY_DIR = os.getenv(
        "SEED_POLICY_DIR", str(REPO_ROOT / "sample_data" / "policies")
    )

    # Fixed reference date for deterministic staleness (falls back to today()).
    ANALYSIS_AS_OF = os.getenv("ANALYSIS_AS_OF", "")

    REPORT_DIR = Path(os.getenv("REPORT_DIR", str(BACKEND_DIR / "generated_reports")))

    # Outbound notification target for compliance managers (webhook-out).
    NOTIFY_WEBHOOK_URL = os.getenv("NOTIFY_WEBHOOK_URL", "")

    # Optional GitHub token for the GitHub connector (never persisted).
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

    # Shared secret configured on the GitHub webhook. When set, every inbound
    # webhook must carry a valid ``X-Hub-Signature-256`` HMAC or it is rejected
    # (401). Empty => signature check skipped (local development convenience).
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")


settings = Settings()
settings.REPORT_DIR.mkdir(parents=True, exist_ok=True)
