"""Tests for demo data reset functionality."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_demo_reset():
    """Verify that calling the demo reset endpoint restores original demo dataset."""
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["shipment_id"] == "demo-shipment-001"

    # Verify quotes exist after reset
    quotes_res = client.get("/api/shipments/demo-shipment-001/quotes")
    assert quotes_res.status_code == 200
    quotes = quotes_res.json()
    assert len(quotes) == 3
