"""Unit Tests for NEXUS Local Collector Telemetry Schemas and Data Contract
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.telemetry import (
    SourceType,
    SourceIdentifier,
    MetricData,
    SystemMetricsData,
    ApplicationMetricsData,
    LogEntry,
    TelemetryPayload,
)
from app.schemas.detection import (
    SensitiveCategoryEnum,
    SensitiveDataFinding,
    DetectionResult,
)
from app.schemas.policy import (
    ViolationSeverityEnum,
    PolicyViolation,
    PolicyValidationResult,
    PolicyRule,
)
from app.schemas.approval import (
    ApprovalDecisionEnum,
    ApprovalRequest,
    ApprovedSubmission,
    ApprovalAuditRecord,
)
from app.schemas.analysis import (
    AnomalySeverityEnum,
    LocalAlert,
)
from app.core.security import compute_payload_integrity_hash


def test_source_identifier_valid():
    source = SourceIdentifier(
        source_id="nexus-demo-portal",
        source_type=SourceType.APPLICATION,
        environment="staging",
        hostname="node-01.local",
        ip_address="192.168.1.10",
    )
    assert source.source_id == "nexus-demo-portal"
    assert source.source_type == SourceType.APPLICATION
    assert source.environment == "staging"


def test_source_identifier_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        SourceIdentifier(
            source_id="nexus-demo-portal",
            source_type=SourceType.APPLICATION,
            unknown_field="injected",
        )


def test_system_metrics_validation():
    # Valid metrics
    sys_metrics = SystemMetricsData(
        cpu_utilization_percent=45.5,
        memory_utilization_percent=62.0,
        memory_used_bytes=4000000000,
        memory_total_bytes=8000000000,
        disk_utilization_percent=70.1,
        disk_used_bytes=70000000000,
        disk_total_bytes=100000000000,
    )
    assert sys_metrics.cpu_utilization_percent == 45.5

    # Out of range CPU percentage
    with pytest.raises(ValidationError):
        SystemMetricsData(
            cpu_utilization_percent=105.0,  # Invalid: > 100
            memory_utilization_percent=50.0,
            memory_used_bytes=1000,
            memory_total_bytes=2000,
            disk_utilization_percent=50.0,
            disk_used_bytes=1000,
            disk_total_bytes=2000,
        )


def test_application_metrics_validation():
    app_metrics = ApplicationMetricsData(
        service_name="demo-portal-api",
        status="healthy",
        http_requests_total=1000,
        http_errors_total=5,
        error_rate=0.005,
        avg_response_time_ms=25.4,
        p95_response_time_ms=65.2,
    )
    assert app_metrics.service_name == "demo-portal-api"
    assert app_metrics.error_rate == 0.005

    # Invalid error rate > 1.0
    with pytest.raises(ValidationError):
        ApplicationMetricsData(
            service_name="demo-portal-api",
            error_rate=1.5,
        )


def test_log_entry_level_validation():
    log = LogEntry(
        level="info",  # Should be normalized to INFO
        message="User authentication success",
        service="auth-service",
        attributes={"user_id": "usr_123"},
    )
    assert log.level == "INFO"

    with pytest.raises(ValidationError):
        LogEntry(
            level="INVALID_LEVEL",
            message="Test message",
            service="test",
        )


def test_telemetry_payload_serialization_and_integrity():
    source = SourceIdentifier(
        source_id="nexus-demo-portal",
        source_type=SourceType.APPLICATION,
        environment="production",
    )
    payload = TelemetryPayload(
        source=source,
        system_metrics=SystemMetricsData(
            cpu_utilization_percent=12.5,
            memory_utilization_percent=40.0,
            memory_used_bytes=2048,
            memory_total_bytes=4096,
            disk_utilization_percent=50.0,
            disk_used_bytes=5000,
            disk_total_bytes=10000,
        ),
        logs=[
            LogEntry(
                level="INFO",
                message="Sanitized operational event",
                service="demo-portal",
            )
        ],
        is_sanitized=True,
    )

    payload_dict = payload.model_dump(mode="json")
    assert payload_dict["is_sanitized"] is True
    assert len(payload_dict["logs"]) == 1

    # Compute integrity hash
    hash1 = compute_payload_integrity_hash(payload_dict)
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 length

    # Integrity hash should be deterministic
    hash2 = compute_payload_integrity_hash(payload_dict)
    assert hash1 == hash2

    # Mutating a field must produce a different hash
    tampered_dict = payload_dict.copy()
    tampered_dict["is_sanitized"] = False
    tampered_hash = compute_payload_integrity_hash(tampered_dict)
    assert hash1 != tampered_hash


def test_sensitive_detection_schemas():
    finding = SensitiveDataFinding(
        category=SensitiveCategoryEnum.API_KEY,
        field_path="logs[0].attributes.api_key",
        rule_name="api_key_regex",
        confidence=0.98,
        description="Potential API key pattern found",
        masked_sample="sk-ant-***REDACTED***",
    )
    assert finding.category == SensitiveCategoryEnum.API_KEY

    result = DetectionResult(
        payload_id="test-payload-id",
        has_sensitive_data=True,
        findings_count=1,
        findings=[finding],
        scan_duration_ms=4.2,
    )
    assert result.has_sensitive_data is True
    assert result.findings[0].rule_name == "api_key_regex"


def test_policy_schemas():
    violation = PolicyViolation(
        rule_id="POL-001",
        rule_name="no_unredacted_secrets",
        severity=ViolationSeverityEnum.BLOCK,
        message="Payload contains detected unredacted API key",
        field_path="logs[0].attributes.api_key",
    )
    assert violation.severity == ViolationSeverityEnum.BLOCK

    policy_result = PolicyValidationResult(
        payload_id="test-payload-id",
        is_compliant=False,
        can_be_approved=False,
        violations=[violation],
    )
    assert policy_result.can_be_approved is False
    assert len(policy_result.violations) == 1


def test_approval_schemas():
    source = SourceIdentifier(
        source_id="nexus-demo-portal",
        source_type=SourceType.APPLICATION,
    )
    payload = TelemetryPayload(source=source, is_sanitized=True)
    payload_hash = compute_payload_integrity_hash(payload.model_dump(mode="json"))

    policy_res = PolicyValidationResult(
        payload_id=payload.payload_id,
        is_compliant=True,
        can_be_approved=True,
    )

    req = ApprovalRequest(
        payload_id=payload.payload_id,
        source=source,
        sanitized_payload=payload,
        payload_integrity_hash=payload_hash,
        policy_validation=policy_res,
    )
    assert req.status == ApprovalDecisionEnum.PENDING

    submission = ApprovedSubmission(
        request_id=req.request_id,
        decision=ApprovalDecisionEnum.APPROVED,
        decision_by="security_admin",
        approved_payload_hash=payload_hash,
        sanitized_payload=payload,
    )
    assert submission.decision == ApprovalDecisionEnum.APPROVED
    assert submission.decision_by == "security_admin"


def test_local_alert_schema():
    alert = LocalAlert(
        title="High CPU Load Detected",
        description="CPU utilization exceeded 85% sustained over 30s",
        severity=AnomalySeverityEnum.HIGH,
        scenario_type="high_cpu",
        source_id="nexus-demo-portal",
        metric_name="system_cpu_percent",
        observed_value=88.4,
        threshold_value=85.0,
        recommendation="Inspect runaway worker threads or scale host container",
    )
    assert alert.severity == AnomalySeverityEnum.HIGH
    assert alert.scenario_type == "high_cpu"
