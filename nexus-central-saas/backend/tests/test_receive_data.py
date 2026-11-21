"""Unit and Integration Tests for Telemetry Ingestion (Feature 1: Receive Data)"""

from datetime import datetime, timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def make_valid_submission(pid=None):
    payload_id = pid or f"payload-ingest-{uuid4().hex[:8]}"
    return {
        "request_id": f"req-ingest-{uuid4().hex[:8]}",
        "decision": "APPROVED",
        "decision_by": "admin",
        "decision_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Routine verified telemetry batch",
        "approved_payload_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "sanitized_payload": {
            "payload_id": payload_id,
            "source": {
                "source_id": "nexus-demo-portal",
                "source_type": "APPLICATION",
                "environment": "production",
                "hostname": "node-01.local",
                "ip_address": "127.0.0.1",
            },
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "system_metrics": {
                "cpu_utilization_percent": 30.5,
                "memory_utilization_percent": 55.0,
                "memory_used_bytes": 4000000000,
                "memory_total_bytes": 8000000000,
                "disk_utilization_percent": 45.0,
                "disk_used_bytes": 40000000000,
                "disk_total_bytes": 100000000000,
            },
            "application_metrics": {
                "service_name": "nexus-demo-portal",
                "status": "healthy",
                "http_requests_total": 850,
                "http_errors_total": 2,
                "error_rate": 0.002,
                "avg_response_time_ms": 18.5,
                "p95_response_time_ms": 42.0,
                "active_db_connections": 6,
                "db_query_errors": 0,
            },
            "logs": [],
            "custom_events": [],
            "metadata": {"collector_version": "1.0.0"},
            "is_sanitized": True,
            "sanitization_summary": {"total_fields_modified": 2},
        },
    }


def test_ingest_telemetry_success():
    submission = make_valid_submission()
    pid = submission["sanitized_payload"]["payload_id"]
    headers = {"X-API-Key": settings.COLLECTOR_API_KEY}

    # Test /api/v1/ingest
    resp = client.post("/api/v1/ingest", json=submission, headers=headers)
    assert resp.status_code == 200
    ack = resp.json()
    assert ack["status"] == "ACCEPTED"
    assert ack["payload_id"] == pid
    assert ack["source_id"] == "nexus-demo-portal"

    # Test query recent
    rec_resp = client.get("/api/v1/telemetry/recent")
    assert rec_resp.status_code == 200
    ids = [r["payload_id"] for r in rec_resp.json()]
    assert pid in ids


def test_ingest_telemetry_unauthenticated():
    submission = make_valid_submission()
    # Missing API Key
    resp = client.post("/api/v1/ingest", json=submission)
    assert resp.status_code == 401

    # Invalid API Key
    resp = client.post("/api/v1/ingest", json=submission, headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_ingest_telemetry_rejects_unsanitized():
    submission = make_valid_submission()
    submission["sanitized_payload"]["is_sanitized"] = False  # Violates sanitization rule
    headers = {"X-API-Key": settings.COLLECTOR_API_KEY}

    resp = client.post("/api/v1/ingest", json=submission, headers=headers)
    assert resp.status_code == 400
    assert "unsanitized telemetry" in resp.json()["detail"]


def test_ingest_telemetry_rejects_non_approved():
    submission = make_valid_submission()
    submission["decision"] = "REJECTED"  # Violates approval rule
    headers = {"X-API-Key": settings.COLLECTOR_API_KEY}

    resp = client.post("/api/v1/ingest", json=submission, headers=headers)
    assert resp.status_code == 400
    assert "APPROVED telemetry" in resp.json()["detail"]
