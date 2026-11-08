"""Tests for freight quote endpoints and validation."""

from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_shipment_quotes_seeded():
    """Verify that seeded quotes for demo shipment can be retrieved."""
    response = client.get("/api/shipments/demo-shipment-001/quotes")
    assert response.status_code == 200
    quotes = response.json()
    assert len(quotes) == 3

    # Check ascending sort by total amount
    totals = [float(q["total_amount"]) for q in quotes]
    assert totals == sorted(totals)


def test_quotes_clearly_marked_synthetic():
    """Verify that demo quotes are explicitly marked with SYNTHETIC_DEMO and carrier demo tags."""
    response = client.get("/api/shipments/demo-shipment-001/quotes")
    assert response.status_code == 200
    quotes = response.json()
    for q in quotes:
        assert q["source_kind"] == "SYNTHETIC_DEMO"
        assert "(Demo)" in q["provider_label"]


def test_get_quote_by_id_success():
    """Verify retrieving a single quote by its ID."""
    response = client.get("/api/quotes/quote-demo-001")
    assert response.status_code == 200
    quote = response.json()
    assert quote["id"] == "quote-demo-001"
    assert quote["shipment_id"] == "demo-shipment-001"
    assert quote["provider_label"] == "Atlantic Bulk Carriers (Demo)"
    assert float(quote["base_amount"]) == 28500.0
    assert float(quote["surcharge_amount"]) == 4500.0
    assert float(quote["total_amount"]) == 33000.0
    # Integrity check: base + surcharge == total
    assert Decimal(str(quote["base_amount"])) + Decimal(str(quote["surcharge_amount"])) == Decimal(str(quote["total_amount"]))


def test_get_quote_by_id_not_found():
    """Verify requesting a non-existent quote returns 404 and structured error code."""
    response = client.get("/api/quotes/nonexistent-quote-000")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "QUOTE_NOT_FOUND"


def test_create_quote_valid():
    """Verify creating a new valid quote with automatic total computation."""
    # Create dedicated shipment for isolation
    shipment_res = client.post(
        "/api/shipments",
        json={
            "cargo_type": "Wheat Grain",
            "quantity_tonnes": 15000,
            "origin": "Port Alpha",
            "destination": "Port Omega",
            "ready_date": "2026-11-20",
            "currency": "USD",
        },
    )
    assert shipment_res.status_code == 201
    shipment_id = shipment_res.json()["id"]

    payload = {
        "provider_label": "Northern Seas Shipping (Demo)",
        "reference": "NSS-2026-990",
        "base_amount": 31000.00,
        "surcharge_amount": 4000.00,
        "currency": "USD",
        "transit_days": 16,
        "vessel_class": "Ultramax",
        "cargo_capacity_tonnes": 60000.00,
        "terms": {"fuel_surcharge": 4000.00, "itemized": True},
        "source_kind": "SYNTHETIC_DEMO",
    }
    response = client.post(f"/api/shipments/{shipment_id}/quotes", json=payload)
    assert response.status_code == 201
    quote = response.json()
    assert quote["id"] is not None
    assert quote["shipment_id"] == shipment_id
    assert float(quote["total_amount"]) == 35000.00  # 31000 + 4000 computed


def test_create_quote_sum_mismatch():
    """Reject quote if provided total does not equal base + surcharges."""
    payload = {
        "provider_label": "Faulty Billing Logistics",
        "reference": "FBL-001",
        "base_amount": 10000.00,
        "surcharge_amount": 2000.00,
        "total_amount": 15000.00,  # Deliberately mismatched (should be 12000)
        "currency": "USD",
    }
    response = client.post("/api/shipments/demo-shipment-001/quotes", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "must equal base" in data["error"]["message"]


def test_create_quote_currency_mismatch():
    """Reject quote if its currency does not match the parent shipment currency."""
    payload = {
        "provider_label": "Euro Carrier",
        "reference": "EC-001",
        "base_amount": 20000.00,
        "surcharge_amount": 1000.00,
        "currency": "EUR",  # Shipment is USD
    }
    response = client.post("/api/shipments/demo-shipment-001/quotes", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "CURRENCY_MISMATCH"


def test_create_quote_nonexistent_shipment():
    """Reject creating a quote for an unknown shipment."""
    payload = {
        "provider_label": "Ghost Carrier",
        "reference": "GC-001",
        "base_amount": 10000.00,
        "currency": "USD",
    }
    response = client.post("/api/shipments/unknown-shipment-id/quotes", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SHIPMENT_NOT_FOUND"
