"""Comprehensive automated test suite for upgraded FreightPilot AI features."""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.models import Base, User, SellerProfile
from app.db.session import engine
from app.services.seller_verification_service import TrustScoreCalculator

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_health_check():
    """Verify health endpoint indicates configured database status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["app"] == "freightpilot-ai"


def test_freight_cost_calculator():
    """Verify explainable calculator produces itemized breakdown without combining currencies."""
    payload = {
        "cargo_type": "GENERAL_CARGO",
        "quantity_tonnes": 50,
        "distance_km": 1200,
        "transport_mode": "OCEAN",
        "currency": "USD",
        "include_insurance": True,
        "express_handling": False
    }
    res = client.post("/api/calculator/estimate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "estimated_freight_cost" in data
    assert data["currency"] == "USD"
    assert "breakdown" in data
    assert "base_freight" in data["breakdown"]
    assert "fuel_surcharge" in data["breakdown"]
    assert len(data["assumptions"]) > 0


def test_trust_score_calculation():
    """Verify explainable seller trust score factor calculation."""
    profile = SellerProfile(
        business_name="Test Line Corp",
        business_address="123 Pier St",
        country="US",
        contact_person="Ops Manager",
        contact_email="ops@testline.com",
        contact_phone="+1234567890",
        verification_status="VERIFIED"
    )
    score_data = TrustScoreCalculator.calculate_score(
        profile, completed_shipments=10, average_rating=4.8, cancellation_rate=0.02, dispute_rate=0.01
    )
    assert score_data["total_score"] > 60
    assert score_data["components"]["business_verification"]["score"] == 40
    assert score_data["components"]["operational_history"]["completed_shipments"] == 10


def test_role_registration_validation():
    """Verify separate Buyer and Seller registration payload constraints."""
    res = client.post("/api/auth/register/buyer", json={"email": "invalid-buyer@test.com", "password": "short"})
    assert res.status_code == 422


def test_copilot_chat_advisory_disclaimer():
    """Verify AI support assistant includes explicit advisory disclaimer."""
    res = client.post("/api/copilot/chat", json={"message": "How do PayPal payments work?", "role_context": "BUYER"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "cannot directly commit payments" in data["disclaimer"]
