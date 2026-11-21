"""Unit Tests for Policy Validation Engine
Verifies hard blocking of:
1. Unsanitized payloads (is_sanitized=False)
2. Remaining unredacted secrets
3. Prohibited fields
4. Oversized payloads
And allows fully compliant sanitized payloads with can_be_approved=True.
"""

from app.policies.validator import PolicyValidator
from app.policies.rules import PolicyConfig
from app.schemas.policy import ViolationSeverityEnum
from app.schemas.telemetry import (
    SourceIdentifier,
    SourceType,
    TelemetryPayload,
    LogEntry,
)


def test_unsanitized_payload_blocked():
    validator = PolicyValidator()
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(source=source, is_sanitized=False)

    result = validator.validate_payload(payload)
    assert result.is_compliant is False
    assert result.can_be_approved is False
    block_rules = [v.rule_id for v in result.violations if v.severity == ViolationSeverityEnum.BLOCK]
    assert "POL-SANITIZATION-REQUIRED" in block_rules


def test_unredacted_sensitive_data_blocked():
    validator = PolicyValidator()
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(
        source=source,
        is_sanitized=True,  # Falsely claimed sanitized while containing cleartext password
        logs=[
            LogEntry(
                level="INFO",
                message="User login succeeded",
                service="auth",
                attributes={"user_password": "PlaintextPassword123!"},
            )
        ],
    )

    result = validator.validate_payload(payload)
    assert result.is_compliant is False
    assert result.can_be_approved is False
    block_rules = [v.rule_id for v in result.violations if v.severity == ViolationSeverityEnum.BLOCK]
    assert "POL-SENSITIVE-DATA-BLOCKED" in block_rules


def test_prohibited_field_blocked():
    validator = PolicyValidator()
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(
        source=source,
        is_sanitized=True,
        logs=[
            LogEntry(
                level="INFO",
                message="Operational event",
                service="web",
                attributes={"cookie": "session_id_value"},
            )
        ],
    )

    result = validator.validate_payload(payload)
    assert result.is_compliant is False
    assert result.can_be_approved is False
    block_rules = [v.rule_id for v in result.violations if v.severity == ViolationSeverityEnum.BLOCK]
    assert "POL-PROHIBITED-FIELD" in block_rules


def test_payload_size_limit_blocked():
    # Set a tiny limit of 500 bytes to test rejection
    validator = PolicyValidator(config=PolicyConfig(max_payload_size_bytes=500))
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(
        source=source,
        is_sanitized=True,
        logs=[
            LogEntry(level="INFO", message="A" * 1000, service="web")
        ],
    )

    result = validator.validate_payload(payload)
    assert result.is_compliant is False
    assert result.can_be_approved is False
    block_rules = [v.rule_id for v in result.violations if v.severity == ViolationSeverityEnum.BLOCK]
    assert "POL-PAYLOAD-SIZE-LIMIT" in block_rules


def test_compliant_payload_succeeds_can_be_approved():
    validator = PolicyValidator()
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(
        source=source,
        is_sanitized=True,
        logs=[
            LogEntry(
                level="INFO",
                message="User login succeeded for [REDACTED_EMAIL] with token [REDACTED_TOKEN]",
                service="auth",
                attributes={"status_code": 200},
            )
        ],
        metadata={"collector_version": "1.0.0"},
    )

    result = validator.validate_payload(payload)
    assert result.is_compliant is True
    assert result.can_be_approved is True
    assert len(result.violations) == 0
