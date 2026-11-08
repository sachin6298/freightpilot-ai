"""Regression tests for access-control and token-validation safeguards."""

from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import settings
from app.db.session import SessionLocal
from app.core.security import get_optional_current_user
from app.main import app

client = TestClient(app)


def _register_buyer():
    response = client.post("/api/auth/register", json={
        "email": f"security-{uuid4().hex[:12]}@example.test",
        "password": "Strong-Security-Password-123!",
    })
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_missing_bearer_token_is_rejected_when_auth_is_required(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as error:
            get_optional_current_user(credentials=None, db=db)
    assert error.value.status_code == 401
    assert error.value.detail["code"] == "AUTHENTICATION_REQUIRED"


def test_refresh_type_token_cannot_be_used_as_access_token():
    access_token = _register_buyer()
    claims = jwt.decode(
        access_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
        issuer="freightpilot-ai",
    )
    claims["typ"] = "refresh"
    wrong_type_token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {wrong_type_token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN_TYPE"


def test_unverified_seller_cannot_browse_or_quote_in_marketplace():
    response = client.post("/api/auth/register/seller", json={
        "email": f"seller-{uuid4().hex[:12]}@example.test",
        "password": "Strong-Security-Password-123!",
        "business_name": "Unverified Freight LLC",
        "business_address": "100 Test Road, Patna",
        "country": "IN",
        "contact_person": "Test User",
        "contact_phone": "+9198" + str(uuid4().int % 10**8).zfill(8),
    })
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    response = client.get("/api/marketplace/shipments", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SELLER_NOT_VERIFIED"


def test_buyer_cannot_access_admin_analytics():
    token = _register_buyer()
    response = client.get("/api/analytics/admin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NOT_AN_ADMIN"
