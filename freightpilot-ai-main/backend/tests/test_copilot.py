"""Tests for AI Copilot quote comparison and analysis fallback."""

from fastapi.testclient import TestClient

from app.db.models import Base
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal, engine
from app.main import app

client = TestClient(app)


def setup_module():
    """Ensure database tables exist and demo data is seeded for copilot tests."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


def test_copilot_compare_success():
    """Verify POST /api/copilot/compare returns structured comparison for valid shipment and quote IDs."""
    response = client.post(
        "/api/copilot/compare",
        json={
            "shipment_id": "demo-shipment-001",
            "quote_ids": ["quote-demo-001", "quote-demo-002"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "comparison" in data
    assert len(data["comparison"]) == 2
    assert "missing_information" in data
    assert "next_questions" in data
    assert "disclaimer" in data
    assert "estimates" in data["disclaimer"].lower()


def test_copilot_compare_shipment_not_found():
    """Verify 404 error when shipment ID does not exist."""
    response = client.post(
        "/api/copilot/compare",
        json={
            "shipment_id": "non-existent-shipment",
            "quote_ids": ["quote-demo-001"],
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SHIPMENT_NOT_FOUND"


def test_copilot_compare_empty_quote_ids():
    """Verify 400 error when quote_ids list is empty."""
    response = client.post(
        "/api/copilot/compare",
        json={
            "shipment_id": "demo-shipment-001",
            "quote_ids": [],
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] in ("VALIDATION_ERROR", "EMPTY_QUOTE_IDS")


def test_copilot_compare_quote_not_found():
    """Verify 404 error when one or more quote IDs do not belong to the shipment."""
    response = client.post(
        "/api/copilot/compare",
        json={
            "shipment_id": "demo-shipment-001",
            "quote_ids": ["quote-demo-001", "invalid-quote-id"],
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "QUOTE_NOT_FOUND"
