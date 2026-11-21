"""Unit Tests for Data Filtering Engine
"""

from app.filtering.engine import DataFilterEngine
from app.filtering.rules import FilterConfig
from app.schemas.telemetry import (
    SourceIdentifier,
    SourceType,
    TelemetryPayload,
    LogEntry,
    ApplicationMetricsData,
    SystemMetricsData,
)


def test_denylist_field_removal():
    engine = DataFilterEngine()
    data = {
        "user_id": 123,
        "raw_headers": "Cookie: session=abc; Host: internal",
        "debug_stacktrace": "Traceback (most recent call last)...",
        "profile": {
            "name": "Alice",
            "cookie": "session_id_val",
        },
    }
    cleaned, pruned = engine._filter_dict(data)
    assert "raw_headers" not in cleaned
    assert "debug_stacktrace" not in cleaned
    assert "cookie" not in cleaned["profile"]
    assert cleaned["user_id"] == 123
    assert cleaned["profile"]["name"] == "Alice"
    assert pruned == 3


def test_allowlist_field_selection():
    config = FilterConfig(
        allowlist_enabled=True,
        allowed_fields={"service", "status_code", "duration_ms"},
    )
    engine = DataFilterEngine(config=config)
    data = {
        "service": "demo-portal",
        "status_code": 200,
        "duration_ms": 14.5,
        "internal_id": "xyz",
        "random_noise": 999,
    }
    cleaned, pruned = engine._filter_dict(data)
    assert set(cleaned.keys()) == {"service", "status_code", "duration_ms"}
    assert pruned == 2


def test_log_level_filtering():
    engine = DataFilterEngine(config=FilterConfig(min_log_level="INFO"))
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(
        source=source,
        logs=[
            LogEntry(level="DEBUG", message="Verbose debug packet dump", service="net"),
            LogEntry(level="INFO", message="Operational request processed", service="api"),
            LogEntry(level="ERROR", message="Database connection refused", service="db"),
        ],
    )
    filtered = engine.filter_payload(payload)
    assert len(filtered.logs) == 2
    levels = [l.level for l in filtered.logs]
    assert "DEBUG" not in levels
    assert "INFO" in levels
    assert "ERROR" in levels


def test_preservation_of_operational_metrics():
    engine = DataFilterEngine()
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    sys_metrics = SystemMetricsData(
        cpu_utilization_percent=55.0,
        memory_utilization_percent=60.0,
        memory_used_bytes=1000,
        memory_total_bytes=2000,
        disk_utilization_percent=40.0,
        disk_used_bytes=1000,
        disk_total_bytes=2000,
    )
    app_metrics = ApplicationMetricsData(
        service_name="demo-portal",
        status="healthy",
        http_requests_total=500,
        http_errors_total=2,
        error_rate=0.004,
        avg_response_time_ms=12.5,
        raw_metrics={"allowed_counter": 500, "raw_headers": "SecretToken"},
    )
    payload = TelemetryPayload(
        source=source,
        system_metrics=sys_metrics,
        application_metrics=app_metrics,
    )

    filtered = engine.filter_payload(payload)

    # Confirm critical metrics are 100% intact
    assert filtered.system_metrics.cpu_utilization_percent == 55.0
    assert filtered.application_metrics.http_requests_total == 500
    assert filtered.application_metrics.error_rate == 0.004
    # Raw headers in raw_metrics must be stripped
    assert "raw_headers" not in filtered.application_metrics.raw_metrics
    assert filtered.application_metrics.raw_metrics["allowed_counter"] == 500
