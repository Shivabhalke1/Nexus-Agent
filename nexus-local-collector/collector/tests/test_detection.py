"""Unit Tests for Sensitive Data Detection Engine
Verifies detection across passwords, tokens, API keys, emails, DB URIs, and deep nested JSON.
"""

from app.detection.engine import SensitiveDataDetector, mask_sample_safely
from app.schemas.detection import SensitiveCategoryEnum
from app.schemas.telemetry import (
    SourceIdentifier,
    SourceType,
    TelemetryPayload,
    LogEntry,
)


def test_mask_sample_safely():
    assert mask_sample_safely("") == "[EMPTY]"
    assert mask_sample_safely("1234") == "****"
    masked_long = mask_sample_safely("super_secret_api_key_12345678")
    assert "super_secret_api_key_12345678" not in masked_long
    assert "[REDACTED_LEN_" in masked_long


def test_detect_sensitive_key_names():
    detector = SensitiveDataDetector()
    data = {
        "user": {
            "name": "Alice",
            "password": "SuperSecretPassword123!",
            "client_secret": "abcdef-123456-secret",
        }
    }
    result = detector.scan_dict(data)
    assert result.has_sensitive_data is True
    paths = [f.field_path for f in result.findings]
    assert "user.password" in paths
    assert "user.client_secret" in paths
    # Verify no raw password in descriptions or masked samples
    for finding in result.findings:
        assert "SuperSecretPassword123!" not in (finding.description + (finding.masked_sample or ""))


def test_detect_email_addresses():
    detector = SensitiveDataDetector()
    data = {
        "event": "Login attempt",
        "message": "User admin@nexus-observe.io attempted login from 10.0.0.1",
    }
    result = detector.scan_dict(data)
    assert result.has_sensitive_data is True
    email_findings = [f for f in result.findings if f.category == SensitiveCategoryEnum.EMAIL]
    assert len(email_findings) >= 1
    assert email_findings[0].field_path == "message"


def test_detect_bearer_token():
    detector = SensitiveDataDetector()
    data = {
        "request": {
            "headers": {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemACt8x4iTMCda8Yhe3iZaWbvV5XKSTbuAn0M"
            }
        }
    }
    result = detector.scan_dict(data)
    assert result.has_sensitive_data is True
    categories = {f.category for f in result.findings}
    assert SensitiveCategoryEnum.ACCESS_TOKEN in categories


def test_detect_database_connection_uri():
    detector = SensitiveDataDetector()
    data = {
        "config": {
            "database_url": "postgresql://dbuser:mypassword123@db.internal:5432/nexus_db"
        }
    }
    result = detector.scan_dict(data)
    assert result.has_sensitive_data is True
    db_findings = [f for f in result.findings if f.category == SensitiveCategoryEnum.DATABASE_CREDENTIAL]
    assert len(db_findings) >= 1
    assert "mypassword123" not in (db_findings[0].description + (db_findings[0].masked_sample or ""))


def test_detect_in_telemetry_payload_nested_logs():
    detector = SensitiveDataDetector()
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(
        source=source,
        logs=[
            LogEntry(
                level="INFO",
                message="Clean log entry with no secrets",
                service="auth",
            ),
            LogEntry(
                level="ERROR",
                message="Failed login for user developer@example.com with api_key=ak_live_9988776655443322",
                service="auth",
                attributes={
                    "nested_credentials": {
                        "user_password": "PlaintextPassword99!"
                    }
                },
            ),
        ],
    )

    result = detector.scan_payload(payload)
    assert result.has_sensitive_data is True
    assert result.findings_count >= 2

    # Verify findings correctly identified locations
    paths = [f.field_path for f in result.findings]
    assert any("logs[1]" in p for p in paths)
    assert any("nested_credentials.user_password" in p for p in paths)
