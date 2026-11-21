"""Foundation tests for NEXUS Central SaaS backend"""

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    verify_collector_api_key,
)
from app.core.config import settings

client = TestClient(app)


def test_health_check_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "NEXUS-Central-SaaS"


def test_service_status_endpoint():
    resp = client.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "receive_data" in data["features"]
    assert "system_health_monitoring" in data["features"]
    assert "incident_detection" in data["features"]
    assert "engineer_approval" in data["features"]
    assert "resolve_problem" in data["features"]


def test_password_hashing():
    pw = "engineer123!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_session():
    token = create_access_token(subject="lead_engineer")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "lead_engineer"
    assert payload["role"] == "engineer"


def test_collector_api_key_validation():
    assert verify_collector_api_key("nexus-collector-auth-key-cicada-2026") is True
    assert verify_collector_api_key("invalid-key") is False
    assert verify_collector_api_key(None) is False
