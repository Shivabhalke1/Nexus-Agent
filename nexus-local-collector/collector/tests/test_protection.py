"""Unit Tests for Data Protection Engine
"""

from app.protection.engine import DataProtectionEngine, ProtectionVerificationError
from app.protection.masking import (
    REDACTION_EMAIL,
    REDACTION_SECRET,
    REDACTION_TOKEN,
)
from app.schemas.telemetry import (
    SourceIdentifier,
    SourceType,
    TelemetryPayload,
    LogEntry,
)


def test_redact_sensitive_keys_and_values():
    engine = DataProtectionEngine()
    data = {
        "user": {
            "name": "Bob",
            "password": "CleartextPassword999!",
            "api_key": "live_sk_secret_value_12345",
        }
    }
    cleaned, counts = engine._sanitize_data(data)
    assert cleaned["user"]["password"] == REDACTION_SECRET
    assert cleaned["user"]["api_key"] == REDACTION_SECRET
    assert cleaned["user"]["name"] == "Bob"
    assert counts["secrets_redacted"] >= 2


def test_redact_text_with_emails_and_tokens():
    engine = DataProtectionEngine()
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(
        source=source,
        logs=[
            LogEntry(
                level="INFO",
                message="User login succeeded for user alice@nexus.test with token Bearer 1234567890abcdef1234567890",
                service="auth",
                attributes={
                    "credentials": {
                        "client_secret": "my-client-secret-999"
                    }
                },
            )
        ],
    )

    sanitized = engine.protect_payload(payload)

    assert sanitized.is_sanitized is True
    assert sanitized.sanitization_summary is not None
    assert sanitized.sanitization_summary["total_fields_modified"] > 0

    log = sanitized.logs[0]
    # Verify no raw secrets or emails in log
    assert "alice@nexus.test" not in log.message
    assert REDACTION_EMAIL in log.message
    assert "1234567890abcdef1234567890" not in log.message
    assert REDACTION_TOKEN in log.message
    assert "my-client-secret-999" not in str(log.attributes)
    assert log.attributes["credentials"]["client_secret"] == REDACTION_SECRET
