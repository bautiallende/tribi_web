import logging
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .api import catalog_router
from .api.admin import router as admin_router
from .api.auth import router as auth_router
from .api.device import router as device_router
from .api.orders import esims_router, payments_router
from .api.orders import router as orders_router
from .core.config import settings
from .core.logging_utils import (
    bind_request_context,
    clear_request_context,
    setup_logging,
)
from .db.session import SessionLocal
from .jobs.scheduler import get_job_scheduler

load_dotenv()
setup_logging(level=settings.log_level_value, log_format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    try:  # pragma: no cover - optional dependency guard
        import importlib

        sentry_sdk = importlib.import_module("sentry_sdk")
        fastapi_integration = importlib.import_module("sentry_sdk.integrations.fastapi")
        FastApiIntegration = getattr(fastapi_integration, "FastApiIntegration")

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[FastApiIntegration()],
        )
        logger.info("Sentry initialized")
    except ModuleNotFoundError:
        logger.warning("Sentry SDK not installed; skipping error monitoring")

app = FastAPI(title="Tribi Backend", version="0.1.0")
job_scheduler = get_job_scheduler()


@app.middleware("http")
async def request_id_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    bind_request_context(request_id)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={
                "method": request.method,
                "path": request.url.path,
            },
        )
        raise
    finally:
        clear_request_context()

    response.headers["X-Request-ID"] = request_id
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if not settings.ENABLE_REQUEST_LOGS:
        return await call_next(request)

    start_time = time.perf_counter()

    response = await call_next(request)

    duration = (time.perf_counter() - start_time) * 1000
    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration, 2),
            "query": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
        },
    )

    return response


# CORS middleware with credentials support for cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(catalog_router)
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(esims_router)
app.include_router(device_router)
app.include_router(admin_router)


@app.on_event("startup")
async def start_jobs() -> None:
    await job_scheduler.start()


@app.on_event("shutdown")
async def stop_jobs() -> None:
    await job_scheduler.stop()


@app.get("/health")
def read_health():
    return {"status": "ok"}


@app.get("/health/full")
def read_health_full():
    db_status = "ok"
    session = None
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("healthcheck_db_failed", extra={"error": str(exc)})
        db_status = "error"
    finally:
        try:
            if session is not None:
                session.close()
        except Exception:  # pragma: no cover - defensive
            pass

    jobs = job_scheduler.status()
    overall = "ok"
    if db_status != "ok" or (jobs["enabled"] and not jobs["running"]):
        overall = "degraded"

    return {
        "status": overall,
        "database": {"status": db_status},
        "jobs": jobs,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
