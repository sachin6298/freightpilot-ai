"""Tests for PayPal payment integration with mocked provider responses."""

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.db.models import Base
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal, engine
from app.main import app

client = TestClient(app)


def setup_module():
    """Ensure database tables exist and demo data is seeded."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


def test_create_order_success():
    """Verify order creation with mocked PayPal success response."""
    with patch("app.routes.payments.create_paypal_order") as mock_create:
        mock_create.return_value = {"id": "PAYPAL_12345", "status": "CREATED"}
        response = client.post(
            "/api/payments/create-order",
            json={"quote_id": "quote-demo-001", "idempotency_key": "test-key-1"},
        )
        if response.status_code != 201:
            print(f"DEBUG: Create order failed with {response.status_code}: {response.json()}")
        assert response.status_code == 201
        data = response.json()
        assert data["provider_order_id"] == "PAYPAL_12345"
        assert data["status"] == "CREATED"
        mock_create.assert_called_once()


def test_capture_order_success():
    """Verify capture success with mocked PayPal response."""
    # 1. Create Order
    with patch("app.routes.payments.create_paypal_order") as mock_create:
        mock_create.return_value = {"id": "PAYPAL_67890", "status": "CREATED"}
        create_res = client.post(
            "/api/payments/create-order",
            json={"quote_id": "quote-demo-002", "idempotency_key": "test-key-2"},
        )
        payment_id = create_res.json()["payment_id"]

    # 2. Capture
    with patch("app.routes.payments.get_paypal_order_details") as mock_get_details, \
         patch("app.routes.payments.capture_paypal_order") as mock_capture:
        mock_get_details.return_value = {
            "status": "APPROVED",
            "purchase_units": [{"amount": {"value": "42000.00", "currency_code": "USD"}}],
        }
        mock_capture.return_value = {
            "purchase_units": [{"payments": {"captures": [{"id": "CAPT_123", "status": "COMPLETED"}]}}]
        }

        capture_res = client.post(f"/api/payments/{payment_id}/capture", json={})
        if capture_res.status_code != 200:
            print(f"DEBUG: Capture order failed with {capture_res.status_code}: {capture_res.json()}")
        assert capture_res.status_code == 200
        data = capture_res.json()
        assert data["status"] == "CAPTURED"
        assert data["provider_capture_id"] == "CAPT_123"
        mock_capture.assert_called_once()
