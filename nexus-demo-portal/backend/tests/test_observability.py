"""Integration tests for Observability, Metrics, and Privacy Logging."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.observability.metrics import metrics_collector
from app.observability.logger import sanitize_dict

# Shared in-memory test database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_prometheus_metrics_endpoint(client):
    # Make a few requests
    client.get("/api/v1/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text = response.text
    assert "nexus_requests_total" in text
    assert "nexus_system_cpu_percent" in text
    assert "nexus_system_uptime_seconds" in text


def test_json_metrics_endpoint(client):
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "application" in data
    assert "system" in data
    assert data["application"]["total_requests"] >= 1
    assert "cpu_percent" in data["system"]
    assert "memory_used_mb" in data["system"]


def test_system_telemetry_endpoint(client):
    response = client.get("/api/v1/metrics/system")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "cpu_percent" in data
    assert "disk_percent" in data
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] > 0


def test_privacy_sanitizer():
    dirty_payload = {
        "user_id": 42,
        "password": "SuperSecretPassword123!",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "auth_header": "Bearer secret_jwt_token_here",
        "nested": {
            "secret_key": "my-private-api-key",
            "normal_field": "visible_value",
        },
    }
    cleaned = sanitize_dict(dirty_payload)
    assert cleaned["user_id"] == 42
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["access_token"] == "[REDACTED]"
    assert "secret_jwt_token_here" not in cleaned["auth_header"]
    assert cleaned["nested"]["secret_key"] == "[REDACTED]"
    assert cleaned["nested"]["normal_field"] == "visible_value"
