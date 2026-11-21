"""Local Analysis Engine
Evaluates collected telemetry against operational thresholds and detects
the 6 Demo Portal failure scenarios plus system resource saturation.
Operates 100% locally with zero external dependencies.
"""

from datetime import datetime, timezone
from typing import List, Optional
from app.analysis.thresholds import AnomalyThresholds, DEFAULT_THRESHOLDS
from app.schemas.analysis import AnomalySeverityEnum, LocalAlert
from app.schemas.telemetry import TelemetryPayload
from app.core.logging_config import get_logger

logger = get_logger("analysis_engine")


class LocalAnalysisEngine:
    """Detects abnormal metrics and event patterns locally."""

    def __init__(self, thresholds: Optional[AnomalyThresholds] = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def analyze_payload(self, payload: TelemetryPayload) -> List[LocalAlert]:
        """Analyze a telemetry payload and return detected local alerts."""
        alerts: List[LocalAlert] = []
        source_id = payload.source.source_id
        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # 1. System Metrics Analysis (CPU, Memory, Disk)
        # -------------------------------------------------------------
        if payload.system_metrics:
            sys = payload.system_metrics

            # Scenario 1: High CPU
            if sys.cpu_utilization_percent >= self.thresholds.cpu_percent_critical:
                alerts.append(
                    LocalAlert(
                        title="Critical Host CPU Utilization",
                        description=f"Host CPU load reached {sys.cpu_utilization_percent:.1f}%, exceeding critical threshold of {self.thresholds.cpu_percent_critical}%.",
                        severity=AnomalySeverityEnum.CRITICAL,
                        scenario_type="high_cpu",
                        source_id=source_id,
                        metric_name="cpu_utilization_percent",
                        observed_value=sys.cpu_utilization_percent,
                        threshold_value=self.thresholds.cpu_percent_critical,
                        recommendation="Inspect background tasks or runaway compute workloads on the host.",
                    )
                )
            elif sys.cpu_utilization_percent >= self.thresholds.cpu_percent_warn:
                alerts.append(
                    LocalAlert(
                        title="High Host CPU Utilization Warning",
                        description=f"Host CPU load reached {sys.cpu_utilization_percent:.1f}%, exceeding warning threshold of {self.thresholds.cpu_percent_warn}%.",
                        severity=AnomalySeverityEnum.HIGH,
                        scenario_type="high_cpu",
                        source_id=source_id,
                        metric_name="cpu_utilization_percent",
                        observed_value=sys.cpu_utilization_percent,
                        threshold_value=self.thresholds.cpu_percent_warn,
                        recommendation="Monitor CPU trends; check if load sustains over next collection cycles.",
                    )
                )

            # Memory Saturation
            if sys.memory_utilization_percent >= self.thresholds.memory_percent_critical:
                alerts.append(
                    LocalAlert(
                        title="Critical Memory Exhaustion",
                        description=f"Host memory usage reached {sys.memory_utilization_percent:.1f}%.",
                        severity=AnomalySeverityEnum.CRITICAL,
                        scenario_type="memory_saturation",
                        source_id=source_id,
                        metric_name="memory_utilization_percent",
                        observed_value=sys.memory_utilization_percent,
                        threshold_value=self.thresholds.memory_percent_critical,
                        recommendation="Check for memory leaks or allocate additional RAM.",
                    )
                )

            # Disk Saturation
            if sys.disk_utilization_percent >= self.thresholds.disk_percent_critical:
                alerts.append(
                    LocalAlert(
                        title="Critical Disk Space Exhaustion",
                        description=f"Host disk usage reached {sys.disk_utilization_percent:.1f}%.",
                        severity=AnomalySeverityEnum.CRITICAL,
                        scenario_type="disk_saturation",
                        source_id=source_id,
                        metric_name="disk_utilization_percent",
                        observed_value=sys.disk_utilization_percent,
                        threshold_value=self.thresholds.disk_percent_critical,
                        recommendation="Purge temporary files or rotate application logs.",
                    )
                )

        # -------------------------------------------------------------
        # 2. Application Metrics Analysis (Demo Portal Failure Scenarios)
        # -------------------------------------------------------------
        if payload.application_metrics:
            app = payload.application_metrics

            # Scenario 4: Backend Unavailability
            if app.status.lower() in ("down", "unresponsive", "error"):
                alerts.append(
                    LocalAlert(
                        title="Backend Application Unavailable",
                        description=f"Monitored service '{app.service_name}' reported status '{app.status}'. Endpoints are unresponsive.",
                        severity=AnomalySeverityEnum.CRITICAL,
                        scenario_type="backend_unavailable",
                        source_id=source_id,
                        metric_name="service_status",
                        recommendation="Verify whether backend process/container is running; check application logs.",
                    )
                )

            # Scenario 2: Slow API Responses
            if app.avg_response_time_ms >= self.thresholds.api_latency_ms_critical:
                alerts.append(
                    LocalAlert(
                        title="Critical API Latency Degradation",
                        description=f"Average API response time is {app.avg_response_time_ms:.1f}ms (threshold: {self.thresholds.api_latency_ms_critical}ms).",
                        severity=AnomalySeverityEnum.CRITICAL,
                        scenario_type="slow_api",
                        source_id=source_id,
                        metric_name="avg_response_time_ms",
                        observed_value=app.avg_response_time_ms,
                        threshold_value=self.thresholds.api_latency_ms_critical,
                        recommendation="Profile slow endpoints; inspect downstream bottlenecks or lock contention.",
                    )
                )
            elif app.avg_response_time_ms >= self.thresholds.api_latency_ms_warn:
                alerts.append(
                    LocalAlert(
                        title="Elevated API Latency Warning",
                        description=f"Average API response time is {app.avg_response_time_ms:.1f}ms (threshold: {self.thresholds.api_latency_ms_warn}ms).",
                        severity=AnomalySeverityEnum.MEDIUM,
                        scenario_type="slow_api",
                        source_id=source_id,
                        metric_name="avg_response_time_ms",
                        observed_value=app.avg_response_time_ms,
                        threshold_value=self.thresholds.api_latency_ms_warn,
                        recommendation="Monitor response latency across route paths.",
                    )
                )

            # Scenario 3: Increased Application Errors
            if app.error_rate >= self.thresholds.error_rate_critical:
                alerts.append(
                    LocalAlert(
                        title="High Application Error Rate (Critical)",
                        description=f"HTTP error rate is {app.error_rate * 100:.1f}% ({app.http_errors_total} errors recorded).",
                        severity=AnomalySeverityEnum.CRITICAL,
                        scenario_type="increased_errors",
                        source_id=source_id,
                        metric_name="error_rate",
                        observed_value=app.error_rate,
                        threshold_value=self.thresholds.error_rate_critical,
                        recommendation="Inspect server error logs for recurring 5xx HTTP status codes.",
                    )
                )
            elif app.error_rate >= self.thresholds.error_rate_warn:
                alerts.append(
                    LocalAlert(
                        title="Elevated Application Error Rate",
                        description=f"HTTP error rate is {app.error_rate * 100:.1f}%.",
                        severity=AnomalySeverityEnum.HIGH,
                        scenario_type="increased_errors",
                        source_id=source_id,
                        metric_name="error_rate",
                        observed_value=app.error_rate,
                        threshold_value=self.thresholds.error_rate_warn,
                        recommendation="Check for failing API calls or dependency errors.",
                    )
                )

            # Scenario 5: Database Failure / Connectivity Loss
            if app.db_query_errors >= self.thresholds.db_errors_threshold or (
                app.status.lower() == "healthy" and app.active_db_connections == 0 and app.http_requests_total > 10
            ):
                alerts.append(
                    LocalAlert(
                        title="Database Connectivity Failure",
                        description=f"Database errors detected: {app.db_query_errors} query errors, {app.active_db_connections} active connections.",
                        severity=AnomalySeverityEnum.CRITICAL,
                        scenario_type="database_failure",
                        source_id=source_id,
                        metric_name="db_query_errors",
                        observed_value=float(app.db_query_errors),
                        threshold_value=float(self.thresholds.db_errors_threshold),
                        recommendation="Verify database server status, connection pool limits, and credentials.",
                    )
                )

        # -------------------------------------------------------------
        # 3. Log Pattern Analysis (Scenario 6: Repeated Failed Logins)
        # -------------------------------------------------------------
        failed_login_count = 0
        for log in payload.logs:
            lower_msg = log.message.lower()
            ev_type = (log.event_type or "").upper()
            if (
                ev_type in ("FAILED_LOGIN", "AUTH_FAILURE", "LOGIN_FAILURE")
                or "failed login" in lower_msg
                or "invalid credentials" in lower_msg
                or "login failed" in lower_msg
            ):
                failed_login_count += 1

        if failed_login_count >= self.thresholds.failed_logins_threshold:
            alerts.append(
                LocalAlert(
                    title="Repeated Failed Login Attempts Detected",
                    description=f"Detected {failed_login_count} failed login attempts in collection batch (threshold: {self.thresholds.failed_logins_threshold}).",
                    severity=AnomalySeverityEnum.HIGH,
                    scenario_type="failed_logins",
                    source_id=source_id,
                    metric_name="failed_logins_count",
                    observed_value=float(failed_login_count),
                    threshold_value=float(self.thresholds.failed_logins_threshold),
                    recommendation="Review authentication logs for potential credential stuffing or brute-force activity.",
                )
            )

        logger.info(
            f"Local analysis completed for payload {payload.payload_id}: "
            f"alerts_generated={len(alerts)}"
        )
        return alerts
