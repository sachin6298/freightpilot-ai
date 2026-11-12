"""Tests for the /health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FreightPilot AI Backend"
    assert set(data) == {"status", "service"}


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "FreightPilot AI Backend"
    assert data["status"] == "running"
    assert "version" in data


def test_readiness_check_reports_database_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["database"] == "available"


def test_localhost_frontend_cors_preflight_is_allowed():
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_loopback_frontend_cors_preflight_is_allowed():
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


def test_firebase_phone_auth_routes_are_registered_at_frontend_contract_paths():
    registered_paths = {route.path for route in app.routes}
    assert "/api/auth/firebase/verify-phone" in registered_paths
    assert "/api/auth/firebase/link-phone" in registered_paths
    assert "/api/auth/firebase/phone/verify" not in registered_paths
    assert "/api/auth/firebase/phone/link" not in registered_paths
