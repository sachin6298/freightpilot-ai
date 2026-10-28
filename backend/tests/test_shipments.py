"""Tests for shipment management endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_shipments_includes_seeded_demo():
    """Verify that listing shipments includes the seeded demo shipment with quotes count."""
    response = client.get("/api/shipments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    demo = next((s for s in data if s["id"] == "demo-shipment-001"), None)
    assert demo is not None
    assert demo["origin"] == "Port of Santos, Brazil"
    assert demo["destination"] == "Port of Rotterdam, Netherlands"
    assert demo["currency"] == "USD"
    assert demo["mode"] == "DEMO"
    assert demo["quotes_count"] == 3


def test_get_shipment_by_id():
    """Verify retrieving a single shipment by its ID."""
    response = client.get("/api/shipments/demo-shipment-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "demo-shipment-001"
    assert data["cargo_type"] == "Agricultural Grain Bulk"
    assert float(data["quantity_tonnes"]) == 25000.0


def test_get_shipment_not_found():
    """Verify requesting a non-existent shipment returns 404 with standard error format."""
    response = client.get("/api/shipments/nonexistent-uuid-999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SHIPMENT_NOT_FOUND"


def test_create_valid_shipment():
    """Verify creating a valid new shipment persists and returns 201 Created."""
    payload = {
        "cargo_type": "Steel Coils",
        "quantity_tonnes": 5000.50,
        "origin": "Port of Shanghai, China",
        "destination": "Port of Hamburg, Germany",
        "ready_date": "2026-11-15",
        "required_arrival_date": "2026-12-20",
        "currency": "USD",
    }
    response = client.post("/api/shipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["cargo_type"] == "Steel Coils"
    assert float(data["quantity_tonnes"]) == 5000.50
    assert data["origin"] == "Port of Shanghai, China"
    assert data["destination"] == "Port of Hamburg, Germany"
    assert data["mode"] == "DEMO"
    assert data["quotes_count"] == 0

    # Verify retrieval
    get_res = client.get(f"/api/shipments/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["cargo_type"] == "Steel Coils"


def test_create_shipment_invalid_quantity():
    """Reject zero or negative cargo quantity."""
    payload = {
        "cargo_type": "Grain",
        "quantity_tonnes": -100,
        "origin": "Port A",
        "destination": "Port B",
        "ready_date": "2026-11-15",
    }
    response = client.post("/api/shipments", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_shipment_same_origin_and_destination():
    """Reject shipment where origin and destination are identical."""
    payload = {
        "cargo_type": "Grain",
        "quantity_tonnes": 1000,
        "origin": "Port of Rotterdam",
        "destination": "port of rotterdam",
        "ready_date": "2026-11-15",
    }
    response = client.post("/api/shipments", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "Origin and destination must be different" in data["error"]["message"]


def test_create_shipment_invalid_arrival_date():
    """Reject shipment where required arrival date is before ready date."""
    payload = {
        "cargo_type": "Grain",
        "quantity_tonnes": 1000,
        "origin": "Port Alpha",
        "destination": "Port Beta",
        "ready_date": "2026-11-20",
        "required_arrival_date": "2026-11-10",
    }
    response = client.post("/api/shipments", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "Required arrival date cannot be earlier than ready date" in data["error"]["message"]


def test_create_shipment_unsupported_currency():
    """Reject shipment with unsupported currency."""
    payload = {
        "cargo_type": "Grain",
        "quantity_tonnes": 1000,
        "origin": "Port Alpha",
        "destination": "Port Beta",
        "ready_date": "2026-11-20",
        "currency": "XYZ",
    }
    response = client.post("/api/shipments", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "Currency 'XYZ' is not supported" in data["error"]["message"]
