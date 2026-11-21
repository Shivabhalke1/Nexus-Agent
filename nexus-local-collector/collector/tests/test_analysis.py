"""Unit Tests for Local Analysis Engine
Verifies detection of all 6 Demo Portal failure simulation scenarios:
1. high_cpu
2. slow_api
3. increased_errors
4. backend_unavailable
5. database_failure
6. failed_logins
"""

from app.analysis.engine import LocalAnalysisEngine
from app.schemas.analysis import AnomalySeverityEnum
from app.schemas.telemetry import (
    SourceIdentifier,
    SourceType,
    TelemetryPayload,
    SystemMetricsData,
    ApplicationMetricsData,
    LogEntry,
)


def make_test_payload(system_metrics=None, application_metrics=None, logs=None):
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    return TelemetryPayload(
        source=source,
        system_metrics=system_metrics,
        application_metrics=application_metrics,
        logs=logs or [],
    )


def test_scenario_1_high_cpu():
    engine = LocalAnalysisEngine()
    sys_metrics = SystemMetricsData(
        cpu_utilization_percent=92.5,  # Exceeds 85% critical
        memory_utilization_percent=50.0,
        memory_used_bytes=1000,
        memory_total_bytes=2000,
        disk_utilization_percent=50.0,
        disk_used_bytes=1000,
        disk_total_bytes=2000,
    )
    payload = make_test_payload(system_metrics=sys_metrics)
    alerts = engine.analyze_payload(payload)

    cpu_alerts = [a for a in alerts if a.scenario_type == "high_cpu"]
    assert len(cpu_alerts) == 1
    assert cpu_alerts[0].severity == AnomalySeverityEnum.CRITICAL
    assert cpu_alerts[0].observed_value == 92.5


def test_scenario_2_slow_api():
    engine = LocalAnalysisEngine()
    app_metrics = ApplicationMetricsData(
        service_name="demo-portal",
        avg_response_time_ms=1250.0,  # Exceeds 800ms critical
    )
    payload = make_test_payload(application_metrics=app_metrics)
    alerts = engine.analyze_payload(payload)

    slow_alerts = [a for a in alerts if a.scenario_type == "slow_api"]
    assert len(slow_alerts) == 1
    assert slow_alerts[0].severity == AnomalySeverityEnum.CRITICAL


def test_scenario_3_increased_errors():
    engine = LocalAnalysisEngine()
    app_metrics = ApplicationMetricsData(
        service_name="demo-portal",
        http_requests_total=100,
        http_errors_total=25,
        error_rate=0.25,  # 25% errors (exceeds 15% critical)
    )
    payload = make_test_payload(application_metrics=app_metrics)
    alerts = engine.analyze_payload(payload)

    err_alerts = [a for a in alerts if a.scenario_type == "increased_errors"]
    assert len(err_alerts) == 1
    assert err_alerts[0].severity == AnomalySeverityEnum.CRITICAL


def test_scenario_4_backend_unavailable():
    engine = LocalAnalysisEngine()
    app_metrics = ApplicationMetricsData(
        service_name="demo-portal",
        status="down",
    )
    payload = make_test_payload(application_metrics=app_metrics)
    alerts = engine.analyze_payload(payload)

    down_alerts = [a for a in alerts if a.scenario_type == "backend_unavailable"]
    assert len(down_alerts) == 1
    assert down_alerts[0].severity == AnomalySeverityEnum.CRITICAL


def test_scenario_5_database_failure():
    engine = LocalAnalysisEngine()
    app_metrics = ApplicationMetricsData(
        service_name="demo-portal",
        db_query_errors=5,
        active_db_connections=0,
    )
    payload = make_test_payload(application_metrics=app_metrics)
    alerts = engine.analyze_payload(payload)

    db_alerts = [a for a in alerts if a.scenario_type == "database_failure"]
    assert len(db_alerts) == 1
    assert db_alerts[0].severity == AnomalySeverityEnum.CRITICAL


def test_scenario_6_failed_logins():
    engine = LocalAnalysisEngine()
    logs = [
        LogEntry(level="WARN", message="Failed login for user admin", service="auth", event_type="FAILED_LOGIN"),
        LogEntry(level="WARN", message="Failed login for user admin", service="auth", event_type="FAILED_LOGIN"),
        LogEntry(level="WARN", message="Failed login for user root", service="auth", event_type="FAILED_LOGIN"),
        LogEntry(level="INFO", message="Operational request", service="api"),
    ]
    payload = make_test_payload(logs=logs)
    alerts = engine.analyze_payload(payload)

    login_alerts = [a for a in alerts if a.scenario_type == "failed_logins"]
    assert len(login_alerts) == 1
    assert login_alerts[0].severity == AnomalySeverityEnum.HIGH
    assert login_alerts[0].observed_value == 3.0


def test_nominal_healthy_payload_produces_no_alerts():
    engine = LocalAnalysisEngine()
    sys_metrics = SystemMetricsData(
        cpu_utilization_percent=20.0,
        memory_utilization_percent=45.0,
        memory_used_bytes=1000,
        memory_total_bytes=2000,
        disk_utilization_percent=30.0,
        disk_used_bytes=1000,
        disk_total_bytes=2000,
    )
    app_metrics = ApplicationMetricsData(
        service_name="demo-portal",
        status="healthy",
        avg_response_time_ms=15.0,
        error_rate=0.001,
        active_db_connections=4,
        db_query_errors=0,
    )
    logs = [
        LogEntry(level="INFO", message="Healthy request processed", service="api")
    ]
    payload = make_test_payload(system_metrics=sys_metrics, application_metrics=app_metrics, logs=logs)
    alerts = engine.analyze_payload(payload)
    assert len(alerts) == 0
