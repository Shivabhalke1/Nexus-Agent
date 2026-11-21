"""Unit Tests for Incident Detection Engine and APIs (Feature 3)"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.entities import ActiveIncidentRecord
from app.detection.engine import IncidentDetectionEngine

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_incidents():
    db = SessionLocal()
    db.query(ActiveIncidentRecord).delete()
    db.commit()
    db.close()
    yield
    db = SessionLocal()
    db.query(ActiveIncidentRecord).delete()
    db.commit()
    db.close()


def test_detect_high_cpu_incident():
    db = SessionLocal()
    try:
        payload = {
            "source": {"source_id": "nexus-demo-portal"},
            "system_metrics": {"cpu_utilization_percent": 91.0},
        }
        incidents = IncidentDetectionEngine.evaluate_payload(payload, db)
        assert len(incidents) == 1
        assert incidents[0].scenario_type == "high_cpu"
        assert incidents[0].severity == "CRITICAL"

        # Repeated abnormal telemetry should update rather than duplicate
        incidents2 = IncidentDetectionEngine.evaluate_payload(payload, db)
        assert len(incidents2) == 1
        total_active = db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.status == "ACTIVE").count()
        assert total_active == 1
    finally:
        db.close()


def test_detect_slow_api_and_error_incidents():
    db = SessionLocal()
    try:
        payload = {
            "source": {"source_id": "nexus-demo-portal"},
            "application_metrics": {
                "service_name": "nexus-demo-portal",
                "avg_response_time_ms": 1250.0,
                "error_rate": 0.22,
                "status": "healthy",
            },
        }
        incidents = IncidentDetectionEngine.evaluate_payload(payload, db)
        assert len(incidents) == 2
        scenarios = {i.scenario_type for i in incidents}
        assert "slow_api" in scenarios
        assert "increased_errors" in scenarios
    finally:
        db.close()


def test_detect_failed_logins_incident():
    db = SessionLocal()
    try:
        payload = {
            "source": {"source_id": "nexus-demo-portal"},
            "logs": [
                {"message": "Failed login for admin", "event_type": "FAILED_LOGIN"},
                {"message": "Failed login for root", "event_type": "FAILED_LOGIN"},
                {"message": "Failed login for test", "event_type": "FAILED_LOGIN"},
            ],
        }
        incidents = IncidentDetectionEngine.evaluate_payload(payload, db)
        assert len(incidents) == 1
        assert incidents[0].scenario_type == "failed_logins"
    finally:
        db.close()


def test_incident_api_endpoints():
    db = SessionLocal()
    try:
        payload = {
            "source": {"source_id": "nexus-demo-portal"},
            "system_metrics": {"cpu_utilization_percent": 89.0},
        }
        IncidentDetectionEngine.evaluate_payload(payload, db)

        # GET /api/v1/incidents/active
        resp = client.get("/api/v1/incidents/active")
        assert resp.status_code == 200
        active = resp.json()
        assert len(active) == 1
        inc_id = active[0]["incident_id"]

        # GET /api/v1/incidents/{incident_id}
        resp_single = client.get(f"/api/v1/incidents/{inc_id}")
        assert resp_single.status_code == 200
        assert resp_single.json()["incident_id"] == inc_id

        # POST /api/v1/incidents/{incident_id}/resolve
        resp_resolve = client.post(f"/api/v1/incidents/{inc_id}/resolve")
        assert resp_resolve.status_code == 200
        assert resp_resolve.json()["status"] == "RESOLVED"

        # Verify no longer active
        resp_after = client.get("/api/v1/incidents/active")
        assert len(resp_after.json()) == 0
    finally:
        db.close()
