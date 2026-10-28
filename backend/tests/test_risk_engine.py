"""Tests for deterministic explainable risk analysis and freight rate estimation."""

from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_shipment_rate_estimate_endpoint():
    """Verify statistical rate estimate endpoint returns median, spread, and disclaimer."""
    response = client.get("/api/shipments/demo-shipment-001/estimate")
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "USD"
    assert data["coverage_status"] == "REPRESENTATIVE_DEMO"
    assert data["sample_size"] == 3
    assert data["median_rate"] == 33000.0  # Median of 16000, 33000, 42000
    assert data["min_rate"] == 16000.0
    assert data["max_rate"] == 42000.0
    assert "prototype" in data["disclaimer"].lower()
    assert "live market feed" in data["disclaimer"].lower() or "trained ml" in data["disclaimer"].lower()


def test_insufficient_data_rate_estimate():
    """Verify that a shipment with < 2 quotes returns INSUFFICIENT_DATA status."""
    # Create isolated shipment with 0 quotes
    shipment_res = client.post(
        "/api/shipments",
        json={
            "cargo_type": "Lithium Batteries",
            "quantity_tonnes": 500,
            "origin": "Port of Tokyo, Japan",
            "destination": "Port of Seattle, USA",
            "ready_date": "2026-11-20",
            "currency": "USD",
        },
    )
    assert shipment_res.status_code == 201
    shipment_id = shipment_res.json()["id"]

    est_res = client.get(f"/api/shipments/{shipment_id}/estimate")
    assert est_res.status_code == 200
    est = est_res.json()
    assert est["coverage_status"] == "INSUFFICIENT_DATA"
    assert est["median_rate"] is None
    assert est["sample_size"] == 0


def test_quote_1_normal_low_concern():
    """Verify Quote 1 (Atlantic Bulk Carriers) is assessed as LOWER_CONCERN."""
    response = client.get("/api/quotes/quote-demo-001")
    assert response.status_code == 200
    quote = response.json()
    assert "assessment" in quote
    assessment = quote["assessment"]
    assert assessment["label"] == "LOWER_CONCERN"
    assert assessment["score"] < 25
    # Variance vs median ($33,000 vs $33,000) should be 0.0%
    assert quote["benchmark_variance_pct"] == 0.0


def test_quote_2_missing_breakdown_and_advance_term():
    """Verify Quote 2 (Global Express) triggers MISSING_FEE_BREAKDOWN and ADVANCE_TERM_REVIEW."""
    response = client.get("/api/quotes/quote-demo-002")
    assert response.status_code == 200
    quote = response.json()
    assessment = quote["assessment"]
    assert assessment is not None

    flag_codes = [f["code"] for f in assessment["flags"]]
    assert "MISSING_FEE_BREAKDOWN" in flag_codes
    assert "ADVANCE_TERM_REVIEW" in flag_codes

    # Check evidence exists
    missing_fee_flag = next(f for f in assessment["flags"] if f["code"] == "MISSING_FEE_BREAKDOWN")
    assert "surcharges" in missing_fee_flag["evidence"].lower()
    assert len(missing_fee_flag["recommended_check"]) > 0

    assert assessment["score"] >= 25
    assert assessment["label"] in ("REVIEW", "HIGH_ATTENTION")


def test_quote_3_high_attention_outlier_capacity_expired():
    """Verify Quote 3 (Pacific Star) triggers multiple critical flags and is marked HIGH_ATTENTION."""
    response = client.get("/api/quotes/quote-demo-003")
    assert response.status_code == 200
    quote = response.json()
    assessment = quote["assessment"]
    assert assessment is not None

    flag_codes = [f["code"] for f in assessment["flags"]]
    assert "QUOTE_PRICE_OUTLIER" in flag_codes
    assert "CAPACITY_MISMATCH" in flag_codes
    assert "QUOTE_EXPIRED" in flag_codes

    # Check price variance is negative (low price outlier)
    assert quote["benchmark_variance_pct"] is not None
    assert quote["benchmark_variance_pct"] < -40.0

    assert assessment["score"] >= 50
    assert assessment["label"] == "HIGH_ATTENTION"


def test_schedule_conflict_trigger():
    """Verify that a quote exceeding the shipment arrival window triggers SCHEDULE_CONFLICT."""
    # Create shipment with tight arrival window (10 days)
    shipment_res = client.post(
        "/api/shipments",
        json={
            "cargo_type": "Perishable Fruit",
            "quantity_tonnes": 1000,
            "origin": "Port of Valparaiso, Chile",
            "destination": "Port of Philadelphia, USA",
            "ready_date": "2026-11-01",
            "required_arrival_date": "2026-11-10",
            "currency": "USD",
        },
    )
    assert shipment_res.status_code == 201
    shipment_id = shipment_res.json()["id"]

    # Create quote with 20 transit days (will arrive Nov 21, 11 days late)
    quote_res = client.post(
        f"/api/shipments/{shipment_id}/quotes",
        json={
            "provider_label": "Slow Voyage Lines",
            "reference": "SVL-001",
            "base_amount": 18000.00,
            "surcharge_amount": 2000.00,
            "currency": "USD",
            "transit_days": 20,
            "terms": {"itemized": True},
        },
    )
    assert quote_res.status_code == 201
    quote = quote_res.json()
    assessment = quote["assessment"]

    flag_codes = [f["code"] for f in assessment["flags"]]
    assert "SCHEDULE_CONFLICT" in flag_codes
    conflict_flag = next(f for f in assessment["flags"] if f["code"] == "SCHEDULE_CONFLICT")
    assert "exceeds" in conflict_flag["evidence"].lower()


def test_quote_recalculate_assessment_endpoint():
    """Verify POST /api/quotes/{quote_id}/assess recalculates and updates the database record."""
    response = client.post("/api/quotes/quote-demo-001/assess")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "quote-demo-001"
    assert data["assessment"]["label"] == "LOWER_CONCERN"
