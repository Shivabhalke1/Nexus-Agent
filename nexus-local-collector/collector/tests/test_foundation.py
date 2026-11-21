"""Unit tests for Phase 0: Project Foundation, Configuration, and Security."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    compute_payload_integrity_hash,
)
from app.core.logging_config import sanitize_dict


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["collector_id"] == settings.COLLECTOR_ID
    assert data["human_approval_enforced"] is True


def test_collector_status_endpoint(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "monitored_targets" in data
    assert "demo_portal_metrics" in data["monitored_targets"]
    assert len(data["pipeline_stages"]) == 7


def test_password_hashing():
    raw_pass = "AdminSecurePass2026!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_admin_jwt_session():
    token = create_access_token(subject="admin")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"

    # Bad token
    assert decode_access_token("fake.invalid.token") is None


def test_payload_integrity_hashing():
    payload_a = {"service": "demo", "metrics": {"cpu": 45.2, "ram": 1024}}
    payload_b = {"metrics": {"ram": 1024, "cpu": 45.2}, "service": "demo"}  # Different key order
    payload_c = {"service": "demo", "metrics": {"cpu": 45.3, "ram": 1024}}  # Slightly modified value

    hash_a = compute_payload_integrity_hash(payload_a)
    hash_b = compute_payload_integrity_hash(payload_b)
    hash_c = compute_payload_integrity_hash(payload_c)

    # Canonical hashing must yield identical hash despite key ordering
    assert hash_a == hash_b
    # Any tamper or modification must change hash
    assert hash_a != hash_c


def test_log_sanitizer():
    dirty = {
        "admin_user": "superadmin",
        "password": "ClearTextPassword123",
        "api_key": "secret-collector-key",
        "auth": "Bearer secret_jwt_token",
    }
    cleaned = sanitize_dict(dirty)
    assert cleaned["admin_user"] == "superadmin"
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["api_key"] == "[REDACTED]"
    assert "secret_jwt_token" not in cleaned["auth"]
