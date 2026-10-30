"""Main FastAPI application entry point for FreightPilot AI."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Base
from app.db.seed import reset_demo_data, seed_demo_data
from app.db.session import SessionLocal, engine, get_db
from app.routes import copilot, payments, quotes, shipments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    # Seed demo data if in DEMO_MODE
    if settings.DEMO_MODE:
        with SessionLocal() as db:
            seed_demo_data(db)

    yield


app = FastAPI(
    title="FreightPilot AI API",
    description="Backend API for Freight Procurement & Payment Risk Review",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS restricted to allowed origins
allowed_origins = [settings.FRONTEND_ORIGIN]
if settings.FRONTEND_ORIGIN.rstrip("/") == "http://localhost:5173":
    allowed_origins.append("http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "; ".join(messages) if messages else "Invalid request payload.",
            }
        },
    )


# Include API routers
app.include_router(shipments.router)
app.include_router(quotes.router)
app.include_router(copilot.router)
app.include_router(payments.router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Health check endpoint specified in API_SPEC.md."""
    mode = "sandbox" if settings.DEMO_MODE else "production"
    return {
        "status": "ok",
        "app": "freightpilot-ai",
        "mode": mode,
    }


@app.post("/api/demo/reset", tags=["Demo"])
def reset_demo(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Reset demo data to initial synthetic quotes (restricted to DEMO_MODE=true)."""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "DEMO_MODE_DISABLED", "message": "Demo reset is disabled outside demo mode."},
        )
    shipment = reset_demo_data(db)
    return {
        "status": "ok",
        "message": "Demo data reset successfully.",
        "shipment_id": shipment.id,
    }
