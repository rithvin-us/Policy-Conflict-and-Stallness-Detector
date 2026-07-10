"""FastAPI application factory for Policy Guardian AI.

Wires logging, database bootstrap, first-boot seeding, CORS, request-ID
correlation, structured error handling, and the versioned API router.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.db import SessionLocal, engine, init_db
from app.core.logging import configure_logging, get_logger, new_request_id
from app.services.seed import seed_if_empty

log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed the corpus + first analysis on boot (tables are already created in
    # create_app, so this runs regardless of how the app is launched).
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    log.info("startup complete",
             extra={"extra_fields": {"db": settings.DATABASE_URL.split("://")[0]}})
    yield


def create_app() -> FastAPI:
    configure_logging()
    init_db()  # create tables eagerly so the app is usable the instant it exists
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Continuous policy governance & compliance intelligence.",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = new_request_id()
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001 - convert to structured 500
            log.exception("unhandled error")
            return JSONResponse(
                status_code=500,
                content={"error": {"code": "internal_error",
                                   "message": "Internal server error",
                                   "request_id": rid}},
                headers={"X-Request-ID": rid},
            )
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = rid
        log.info("request", extra={"extra_fields": {
            "method": request.method, "path": request.url.path,
            "status": response.status_code, "ms": round(elapsed, 1)}})
        return response

    @app.get("/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok", "version": settings.VERSION,
                "service": settings.APP_NAME}

    @app.get("/ready", tags=["system"])
    def ready() -> dict:
        db_ok = True
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
        except Exception:  # noqa: BLE001
            db_ok = False
        return {"status": "ready" if db_ok else "degraded",
                "db": db_ok, "analysis_engine": "deterministic"}

    app.include_router(api_router, prefix=settings.API_PREFIX)
    return app


app = create_app()
