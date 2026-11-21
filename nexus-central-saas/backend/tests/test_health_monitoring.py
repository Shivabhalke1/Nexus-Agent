"""Unit Tests for System Health Monitoring (Feature 2)"""

from datetime import datetime, timezone, timedelta
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.monitoring.health_engine import HealthEngine
from app.schemas.health import HealthStateEnum
from app.models.entities import TelemetryRecord
from app.core.database import SessionLocal

client = TestClient(app)


def test_health_evaluation_four_states():
    # 1. EXCELLENT
    state = HealthEngine.evaluate_service_health(
        app_metrics={"status": "healthy", "avg_response_time_ms": 20.0, "error_rate": 0.001},
        sys_metrics={"cpu_utilization_percent": 25.0, "memory_utilization_percent": 40.0},
    )
    assert state == HealthStateEnum.EXCELLENT

    # 2. GOOD
    state = HealthEngine.evaluate_service_health(
        app_metrics={"status": "healthy", "avg_response_time_ms": 150.0, "error_rate": 0.015},
        sys_metrics={"cpu_utilization_percent": 60.0, "memory_utilization_percent": 70.0},
    )
    assert state == HealthStateEnum.GOOD

    # 3. FAIR
    state = HealthEngine.evaluate_service_health(
        app_metrics={"status": "healthy", "avg_response_time_ms": 450.0, "error_rate": 0.05},
        sys_metrics={"cpu_utilization_percent": 75.0, "memory_utilization_percent": 82.0},
    )
    assert state == HealthStateEnum.FAIR

    # 4. POOR (High CPU)
    state = HealthEngine.evaluate_service_health(
        app_metrics={"status": "healthy", "avg_response_time_ms": 50.0, "error_rate": 0.001},
        sys_metrics={"cpu_utilization_percent": 92.0, "memory_utilization_percent": 50.0},
    )
    assert state == HealthStateEnum.POOR

    # 4. POOR (Service Down)
    state = HealthEngine.evaluate_service_health(
        app_metrics={"status": "down"},
        sys_metrics={"cpu_utilization_percent": 10.0, "memory_utilization_percent": 20.0},
    )
    assert state == HealthStateEnum.POOR


def test_health_summary_api():
    db = SessionLocal()
    try:
        # Insert a healthy record
        payload = {
            "source": {"source_id": "test-service"},
            "application_metrics": {"service_name": "test-service", "status": "healthy", "avg_response_time_ms": 25.0, "error_rate": 0.0},
            "system_metrics": {"cpu_utilization_percent": 15.0, "memory_utilization_percent": 35.0, "disk_utilization_percent": 20.0},
        }
        rec = TelemetryRecord(
            payload_id="test-health-p1",
            request_id="req-1",
            source_id="test-service",
            is_sanitized=True,
            payload_hash="hash1234567890abcdef",
            received_at=datetime.now(timezone.utc),
            payload_json=json.dumps(payload),
        )
        db.add(rec)
        db.commit()

        resp = client.get("/api/v1/health/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_health"] == "Excellent"
        assert data["is_telemetry_stale"] is False
        assert len(data["services"]) == 1
        assert data["services"][0]["service_name"] == "test-service"
    finally:
        db.query(TelemetryRecord).filter(TelemetryRecord.payload_id == "test-health-p1").delete()
        db.commit()
        db.close()
