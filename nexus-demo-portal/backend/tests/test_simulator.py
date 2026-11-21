"""Integration tests for the Controlled Failure Simulator and all 6 Scenarios."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.seed import seed_database
from app.failure_simulator.state import simulator_state

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
    with TestingSessionLocal() as db:
        seed_database(db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    # Ensure simulator is clean before each test
    simulator_state.reset_all()
    yield TestClient(app)
    simulator_state.reset_all()


def test_simulator_status_endpoint(client):
    res = client.get("/api/v1/simulator/status")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "high_cpu" in data
    assert "slow_api" in data
    assert "backend_unavailable" in data
    assert "database_failure" in data
    assert "increased_errors" in data
    assert "failed_logins" in data
    assert data["high_cpu"]["active"] is False


def test_scenario_2_slow_api(client):
    # Activate slow API with 200ms delay for fast test
    act_res = client.post(
        "/api/v1/simulator/scenarios/slow_api/activate",
        json={"duration_seconds": 10, "delay_ms": 200, "target_endpoint": "/api/v1/products"},
    )
    assert act_res.status_code == 200
    assert act_res.json()["data"]["active"] is True

    # Call /api/v1/products and verify delay was applied
    res = client.get("/api/v1/products")
    assert res.status_code == 200
    duration_ms = float(res.headers.get("x-response-time-ms", 0))
    assert duration_ms >= 180  # Should reflect at least 200ms delay

    # Deactivate
    deact_res = client.post("/api/v1/simulator/scenarios/slow_api/deactivate")
    assert deact_res.status_code == 200
    assert deact_res.json()["data"]["active"] is False


def test_scenario_3_backend_unavailable(client):
    # Activate backend unavailable
    client.post(
        "/api/v1/simulator/scenarios/backend_unavailable/activate",
        json={"duration_seconds": 10, "target_endpoint": "/api/v1/products"},
    )

    # Calling products should return 503
    res = client.get("/api/v1/products")
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "SERVICE_UNAVAILABLE"

    # Emergency Reset restores service
    client.post("/api/v1/simulator/reset")
    restored_res = client.get("/api/v1/products")
    assert restored_res.status_code == 200


def test_scenario_4_database_failure(client):
    # Activate DB fault injection
    client.post(
        "/api/v1/simulator/scenarios/database_failure/activate",
        json={"duration_seconds": 10},
    )

    # Health check should report 503
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 503
    assert health_res.json()["error"]["code"] == "DATABASE_UNAVAILABLE"

    # Reset restores health
    client.post("/api/v1/simulator/reset")
    restored_res = client.get("/api/v1/health")
    assert restored_res.status_code == 200


def test_scenario_5_increased_errors(client):
    client.post(
        "/api/v1/simulator/scenarios/increased_errors/activate",
        json={"duration_seconds": 10, "target_endpoint": "/api/v1/products"},
    )

    res = client.get("/api/v1/products")
    assert res.status_code == 500
    assert res.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"

    client.post("/api/v1/simulator/reset")
    assert client.get("/api/v1/products").status_code == 200


def test_scenario_6_failed_logins(client):
    res = client.post(
        "/api/v1/simulator/scenarios/failed_logins/activate",
        json={"duration_seconds": 10, "count": 3},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["attempts_generated"] == 3
    assert len(data["synthetic_targets"]) == 3
