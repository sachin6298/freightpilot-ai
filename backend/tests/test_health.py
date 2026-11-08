"""Tests for the /health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
<<<<<<< HEAD
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
=======
    assert data["status"] == "ok"
    assert data["app"] == "freightpilot-ai"
    assert set(data) == {"status", "app"}
>>>>>>> e6ba7bf4c8fc4ecc1613050b3b9d81a0cf7678b9
