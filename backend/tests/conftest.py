"""Pytest configuration for FreightPilot backend tests."""

import os

# Set test environment variables BEFORE importing app modules
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "true")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("EMAIL_PROVIDER", "console")
os.environ.setdefault("SMS_PROVIDER", "console")

# Import after setting env vars
import pytest
from fastapi.testclient import TestClient
from app.db.models import Base
from app.db.session import engine, SessionLocal
from app.db.seed import seed_demo_data
from app.main import app


@pytest.fixture(scope="session")
def client():
    """Create a test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def db():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Set up database for each test."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_demo_data(session)
    yield
    Base.metadata.drop_all(bind=engine)