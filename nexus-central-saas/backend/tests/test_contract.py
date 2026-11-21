"""Integration Contract Compatibility Tests
Verifies that Central SaaS schema models accept exact payloads dispatched by Local Collector.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.telemetry import (
    SourceIdentifier,
    SourceType,
    SystemMetricsData,
    ApplicationMetricsData,
    LogEntry,
    TelemetryPayload,
)
from app.schemas.approval import ApprovedSubmission, ApprovalDecisionEnum


def test_approved_submission_contract():
    # Exact structure produced by Local Collector SaaSClient
    raw_dict = {
        "request_id": "c1f76e33-728b-4b2a-bf31-0dfae16f21a4",
        "decision": "APPROVED",
        "decision_by": "admin",
        "decision_at": "2026-11-21T00:15:30.000000Z",
        "reason": "Routine hourly telemetry export inspected and approved",
        "approved_payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "sanitized_payload": {
            "payload_id": "a8b34c2e-4890-4a81-b219-509930f4cfd1",
            "source": {
                "source_id": "nexus-demo-portal",
                "source_type": "APPLICATION",
                "environment": "production",
                "hostname": "collector-node-01",
                "ip_address": "127.0.0.1",
            },
            "collected_at": "2026-11-21T00:15:00.000000Z",
            "system_metrics": {
                "cpu_utilization_percent": 18.5,
                "memory_utilization_percent": 42.1,
                "memory_used_bytes": 3532652544,
                "memory_total_bytes": 8388608000,
                "disk_utilization_percent": 34.0,
                "disk_used_bytes": 17179869184,
                "disk_total_bytes": 50529027072,
                "network_bytes_sent": 1048576,
                "network_bytes_recv": 2097152,
                "network_interfaces": {},
                "timestamp": "2026-11-21T00:15:00.000000Z",
            },
            "application_metrics": {
                "service_name": "nexus-demo-portal",
                "status": "healthy",
                "http_requests_total": 1420,
                "http_errors_total": 3,
                "error_rate": 0.0021,
                "avg_response_time_ms": 14.2,
                "p95_response_time_ms": 38.6,
                "active_db_connections": 5,
                "db_query_errors": 0,
                "raw_metrics": {},
                "timestamp": "2026-11-21T00:15:00.000000Z",
            },
            "logs": [
                {
                    "timestamp": "2026-11-21T00:14:58.000000Z",
                    "level": "INFO",
                    "message": "User login succeeded for [REDACTED_EMAIL]",
                    "service": "demo-portal",
                    "attributes": {"status_code": 200},
                }
            ],
            "custom_events": [],
            "metadata": {"collector_version": "1.0.0"},
            "is_sanitized": True,
            "sanitization_summary": {"total_fields_modified": 1},
        },
    }

    submission = ApprovedSubmission.model_validate(raw_dict)
    assert submission.request_id == "c1f76e33-728b-4b2a-bf31-0dfae16f21a4"
    assert submission.decision == ApprovalDecisionEnum.APPROVED
    assert submission.sanitized_payload.is_sanitized is True
    assert submission.sanitized_payload.system_metrics.cpu_utilization_percent == 18.5
    assert len(submission.sanitized_payload.logs) == 1


def test_malformed_submission_rejected():
    with pytest.raises(ValidationError):
        ApprovedSubmission.model_validate(
            {
                "request_id": "invalid",
                "decision": "UNKNOWN_DECISION",  # Invalid enum
                "decision_by": "admin",
                "approved_payload_hash": "123",
                "sanitized_payload": {},
            }
        )
