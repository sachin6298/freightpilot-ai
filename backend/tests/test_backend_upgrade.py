"""Regression tests for newly added backend workflows."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import Base
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal, engine
from app.main import app

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


def _register():
    email = f"qa-{uuid4().hex[:10]}@example.test"
    response = client.post("/api/auth/register", json={"email": email, "password": "Strong-Pass-1234"})
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _create_shipment(token: str):
    response = client.post("/api/shipments", headers={"Authorization": f"Bearer {token}"}, json={
        "cargo_type": "Steel coils", "quantity_tonnes": "1200.50",
        "origin": "Port Alpha", "destination": "Port Beta",
        "ready_date": "2026-11-15", "currency": "USD",
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_registration_login_and_me():
    token = _register()
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "USER"


def test_owned_shipment_is_not_visible_to_another_user():
    owner_token = _register()
    other_token = _register()
    shipment = _create_shipment(owner_token)
    response = client.get(
        f"/api/shipments/{shipment['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404


def test_tracking_state_transitions_and_notifications():
    token = _register()
    shipment = _create_shipment(token)
    headers = {"Authorization": f"Bearer {token}"}
    shipment_id = shipment["id"]

    for target in ("QUOTED", "BOOKED", "IN_TRANSIT", "EXCEPTION"):
        event = client.post(f"/api/shipments/{shipment_id}/tracking", headers=headers, json={
            "status": target, "location": "Port Alpha", "description": f"Shipment status: {target}",
        })
        assert event.status_code == 201, event.text

    invalid = client.post(f"/api/shipments/{shipment_id}/tracking", headers=headers, json={
        "status": "DRAFT", "description": "Illegal backwards transition",
    })
    assert invalid.status_code == 409

    timeline = client.get(f"/api/shipments/{shipment_id}/tracking", headers=headers)
    assert timeline.status_code == 200
    assert [item["status"] for item in timeline.json()] == ["QUOTED", "BOOKED", "IN_TRANSIT", "EXCEPTION"]

    notifications = client.get("/api/notifications?unread_only=true", headers=headers)
    assert notifications.status_code == 200
    assert any(item["kind"] == "SHIPMENT" for item in notifications.json())


def test_analytics_returns_db_aggregates():
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["shipment_count"] >= 1
    assert "captured_spend_by_currency" in data
    carrier_response = client.get("/api/analytics/carriers")
    assert carrier_response.status_code == 200
    assert isinstance(carrier_response.json()["items"], list)


def test_expired_quote_cannot_create_payment_order():
    response = client.post("/api/payments/create-order", json={
        "quote_id": "quote-demo-003", "idempotency_key": f"expired-{uuid4().hex[:12]}",
    })
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "QUOTE_EXPIRED"


def test_verified_paypal_webhook_is_processed_once():
    from unittest.mock import patch
    from app.db.models import Payment

    with SessionLocal() as db:
        payment = Payment(
            shipment_id="demo-shipment-001", quote_id="quote-demo-001",
            amount_snapshot="33000.00", currency_snapshot="USD",
            provider="paypal_sandbox", provider_order_id=f"WH-{uuid4().hex[:12]}",
            status="CREATED",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
        order_id = payment.provider_order_id

    event_id = f"WH-EVENT-{uuid4().hex[:12]}"
    payload = {
        "id": event_id,
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": f"CAPTURE-{uuid4().hex[:10]}",
            "amount": {"value": "33000.00", "currency_code": "USD"},
            "supplementary_data": {"related_ids": {"order_id": order_id}},
        },
    }
    with patch("app.routes.payments.verify_paypal_webhook", return_value=True):
        first = client.post("/api/webhooks/paypal", json=payload)
        second = client.post("/api/webhooks/paypal", json=payload)
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "processed"
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "duplicate"

    with SessionLocal() as db:
        stored = db.query(Payment).filter(Payment.id == payment_id).one()
        assert stored.status == "CAPTURED"
        assert stored.provider_capture_id == payload["resource"]["id"]


def test_unconfigured_carrier_is_not_presented_as_live():
    response = client.get("/api/carriers")
    assert response.status_code == 200
    body = response.json()
    assert body["live_integrations_available"] is False
    assert "No live carrier API adapter is configured" in body["note"]

    refresh = client.post(
        "/api/shipments/demo-shipment-001/refresh-quotes?carrier_code=unknown",
    )
    assert refresh.status_code == 501
    assert refresh.json()["error"]["code"] == "CARRIER_NOT_CONFIGURED"
