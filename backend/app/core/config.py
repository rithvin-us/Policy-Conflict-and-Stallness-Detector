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


class Settings:
    APP_NAME = "Policy Guardian AI"
    VERSION = "1.0.0"
    API_PREFIX = "/api/v1"

    # SQLite by default; set DATABASE_URL to a Postgres DSN in production.
    DATABASE_URL = os.getenv(
        "DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'policyguardian.db'}"
    )

    # Redis/Celery are optional — absent => synchronous in-process execution.
    REDIS_URL = os.getenv("REDIS_URL", "")
    USE_CELERY = os.getenv("USE_CELERY", "0") == "1"

    # Seed corpus loaded on first boot so the dashboard is never empty.
    SEED_ON_STARTUP = os.getenv("SEED_ON_STARTUP", "1") == "1"
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

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")


settings = Settings()
settings.REPORT_DIR.mkdir(parents=True, exist_ok=True)
