"""Main FastAPI application entry point for FreightPilot AI."""

from contextlib import asynccontextmanager
from typing import Any
import logging

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.seed import reset_demo_data, seed_demo_data
from app.db.session import SessionLocal, get_db
from app.db.migrate import initialize_database
from app.routes import admin, analytics, auth, carriers, copilot, notifications, payments, quotes, shipments, tracking, seller_verification, marketplace, documents, calculator
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.core.security import get_optional_current_user
from app.db.models import User


logger = logging.getLogger("freightpilot.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    # Schema changes in production are deployed explicitly with `alembic upgrade head`.
    # Automatic create_all is limited to local development/test environments.
    # Initialize database if not in production and using SQLite
    if not settings.is_production and settings.DATABASE_URL.startswith("sqlite"):
        initialize_database()

    # Seed demo data if in DEMO_MODE
    if settings.DEMO_MODE:
        with SessionLocal() as db:
            seed_demo_data(db)

    yield


app = FastAPI(
    title="FreightPilot AI API",
    description="Backend API for freight procurement, shipment operations and payment risk review.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# Restrict CORS to explicit frontend origins. Never use wildcard origins with credentials.
allowed_origins = [settings.FRONTEND_ORIGIN.strip().rstrip("/")]
allowed_origins.extend(origin.strip().rstrip("/") for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip())
if settings.FRONTEND_ORIGIN.rstrip("/") == "http://localhost:5173":
    allowed_origins.append("http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(allowed_origins)),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)
app.add_middleware(SecurityHeadersMiddleware)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)


# Standardized error responses according to API_SPEC.md
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    messages = []
    for error in exc.errors():
        loc = " -> ".join(str(item) for item in error.get("loc", []) if item != "body")
        msg = error.get("msg", "Invalid value")
        messages.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "; ".join(messages) if messages else "Invalid request payload.",
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled API exception path=%s exception_type=%s", request.url.path, type(exc).__name__)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}})


# Include API routers
app.include_router(auth.router)
app.include_router(shipments.router)
app.include_router(tracking.router)
app.include_router(quotes.router)
app.include_router(copilot.router)
app.include_router(payments.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(carriers.router)
app.include_router(seller_verification.router)
app.include_router(marketplace.router)
app.include_router(documents.router)
app.include_router(calculator.router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Liveness probe for UptimeRobot and load balancers.
    Returns minimal info - no infrastructure details disclosed.
    """
    return {"status": "healthy", "service": "FreightPilot AI Backend"}


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    """Root endpoint for basic connectivity check."""
    return {"service": "FreightPilot AI Backend", "status": "running", "version": "1.0.0"}


@app.get("/health/ready", tags=["System"])
async def readiness_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness probe verifies required database and rate-limit infrastructure."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail={"code": "DATABASE_UNAVAILABLE", "message": "Database is not ready."})
    if settings.is_production and settings.RATE_LIMIT_ENABLED:
        redis_client = None
        try:
            from redis.asyncio import Redis
            redis_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
            await redis_client.ping()
        except Exception:
            raise HTTPException(status_code=503, detail={"code": "RATE_LIMIT_BACKEND_UNAVAILABLE", "message": "Rate-limit infrastructure is not ready."})
        finally:
            if redis_client is not None:
                await redis_client.aclose()
    return {"status": "ready", "database": "available", "rate_limit_store": "available" if settings.is_production and settings.RATE_LIMIT_ENABLED else "not_required"}


@app.post("/api/demo/reset", tags=["Demo"])
def reset_demo(
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    """Reset synthetic demo fixtures only; disabled whenever demo mode is off."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail={"code": "DEMO_MODE_DISABLED", "message": "Demo reset is disabled outside demo mode."})
    if settings.AUTH_REQUIRED and (user is None or user.role != "ADMIN"):
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    shipment = reset_demo_data(db)
    return {"status": "ok", "message": "Demo data reset successfully.", "shipment_id": shipment.id}
