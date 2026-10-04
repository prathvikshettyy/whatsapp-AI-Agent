"""FastAPI Application entrypoint with logging, lifespan, and routers."""

from contextlib import asynccontextmanager
import time
import uuid
from typing import Any, Dict
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import structlog

from backend.app.api.analytics import analytics_router
from backend.app.api.auth import auth_router
from backend.app.api.conversations import conversations_router
from backend.app.api.kb import kb_router
from backend.app.api.settings import settings_router
from backend.app.api.stream import stream_router
from backend.app.api.webhook import webhook_router
from backend.app.config import settings
from backend.app.db import engine, init_db
from backend.app.services.ratelimit import get_redis
from backend.app.services.whatsapp import whatsapp_service

# Configure structlog JSON logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("backend_startup")
    await init_db()
    yield
    logger.info("backend_shutdown")
    await engine.dispose()
    await whatsapp_service.close()


app = FastAPI(
    title="WhatsApp AI Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS setup for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    latency = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = req_id
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=latency,
        request_id=req_id,
    )
    return response


# Include API Routers
app.include_router(webhook_router)
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(kb_router)
app.include_router(settings_router)
app.include_router(stream_router)
app.include_router(analytics_router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Health check validating Postgres and Redis connectivity."""
    db_ok = True
    redis_ok = True

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        logger.error("db_health_check_failed", error=str(e))

    try:
        redis_client = await get_redis()
        await redis_client.ping()
    except Exception as e:
        redis_ok = False
        logger.warning("redis_health_check_failed", error=str(e))

    all_healthy = db_ok and redis_ok
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if all_healthy else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "redis": "connected" if redis_ok else "unreachable",
    }
