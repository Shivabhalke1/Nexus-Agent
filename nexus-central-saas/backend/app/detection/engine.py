"""Central SaaS Incident Detection Engine (Feature 3)"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.entities import ActiveIncidentRecord
from app.schemas.incident import IncidentSeverityEnum, IncidentStatusEnum
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("incident_detection")


class IncidentDetectionEngine:
    """Evaluates incoming telemetry for anomalous system and application conditions."""

    @classmethod
    def evaluate_payload(cls, payload_dict: Dict[str, Any], db: Session) -> List[ActiveIncidentRecord]:
        """Detect abnormal conditions and record active incidents without duplicates."""
        detected_incidents: List[ActiveIncidentRecord] = []
        source = payload_dict.get("source", {})
        source_id = source.get("source_id", "nexus-demo-portal")
        sys_data = payload_dict.get("system_metrics") or {}
        app_data = payload_dict.get("application_metrics") or {}
        logs = payload_dict.get("logs") or []
        service_name = app_data.get("service_name", source_id)
        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # 1. High CPU Utilization
        # ---------------------------------------------------------
        cpu = sys_data.get("cpu_utilization_percent", 0.0)
        if cpu >= settings.CPU_FAIR_MAX:  # >= 85%
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="high_cpu",
                source_id=source_id,
                service_name=service_name,
                title="Critical Host CPU Utilization Exceeded",
                description=f"Host CPU utilization reached {cpu:.1f}%, exceeding 85% critical threshold.",
                severity=IncidentSeverityEnum.CRITICAL,
                metric_name="cpu_utilization_percent",
                observed_value=cpu,
                threshold_value=85.0,
            )

        # ---------------------------------------------------------
        # 2. High Memory Utilization
        # ---------------------------------------------------------
        mem = sys_data.get("memory_utilization_percent", 0.0)
        if mem >= settings.MEMORY_FAIR_MAX:  # >= 90%
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="high_memory",
                source_id=source_id,
                service_name=service_name,
                title="Critical Host Memory Exhaustion",
                description=f"Host memory utilization reached {mem:.1f}%, exceeding 90% threshold.",
                severity=IncidentSeverityEnum.CRITICAL,
                metric_name="memory_utilization_percent",
                observed_value=mem,
                threshold_value=90.0,
            )

        # ---------------------------------------------------------
        # 3. High Disk Utilization
        # ---------------------------------------------------------
        disk = sys_data.get("disk_utilization_percent", 0.0)
        if disk >= 95.0:
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="high_disk",
                source_id=source_id,
                service_name=service_name,
                title="Critical Disk Storage Saturation",
                description=f"Disk utilization reached {disk:.1f}%, exceeding 95% threshold.",
                severity=IncidentSeverityEnum.CRITICAL,
                metric_name="disk_utilization_percent",
                observed_value=disk,
                threshold_value=95.0,
            )

        # ---------------------------------------------------------
        # 4. Backend Unavailability
        # ---------------------------------------------------------
        status = app_data.get("status", "healthy").lower()
        if status in ("down", "unresponsive", "error", "degraded"):
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="backend_unavailable",
                source_id=source_id,
                service_name=service_name,
                title="Backend Application Unresponsive / Offline",
                description=f"Service '{service_name}' reported status '{status}'. Application endpoints unreachable.",
                severity=IncidentSeverityEnum.CRITICAL,
                metric_name="service_status",
            )

        # ---------------------------------------------------------
        # 5. Slow API Responses
        # ---------------------------------------------------------
        latency = app_data.get("avg_response_time_ms", 0.0)
        if latency >= 800.0:
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="slow_api",
                source_id=source_id,
                service_name=service_name,
                title="Severe API Latency Degradation",
                description=f"Average API response time reached {latency:.1f}ms, exceeding 800ms critical threshold.",
                severity=IncidentSeverityEnum.CRITICAL,
                metric_name="avg_response_time_ms",
                observed_value=latency,
                threshold_value=800.0,
            )

        # ---------------------------------------------------------
        # 6. Increased Application Errors
        # ---------------------------------------------------------
        err_rate = app_data.get("error_rate", 0.0)
        if err_rate >= 0.15:
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="increased_errors",
                source_id=source_id,
                service_name=service_name,
                title="High Application Error Rate (Critical)",
                description=f"Application HTTP error rate reached {err_rate * 100:.1f}%, exceeding 15% threshold.",
                severity=IncidentSeverityEnum.CRITICAL,
                metric_name="error_rate",
                observed_value=err_rate,
                threshold_value=0.15,
            )
        elif err_rate >= 0.05:
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="increased_errors",
                source_id=source_id,
                service_name=service_name,
                title="Elevated Application Error Rate Warning",
                description=f"Application HTTP error rate reached {err_rate * 100:.1f}%.",
                severity=IncidentSeverityEnum.HIGH,
                metric_name="error_rate",
                observed_value=err_rate,
                threshold_value=0.05,
            )

        # ---------------------------------------------------------
        # 7. Database Connectivity Failure
        # ---------------------------------------------------------
        db_errors = app_data.get("db_query_errors", 0)
        db_conns = app_data.get("active_db_connections", 1)
        if db_errors > 0 or (status == "healthy" and db_conns == 0 and app_data.get("http_requests_total", 0) > 10):
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="database_failure",
                source_id=source_id,
                service_name=service_name,
                title="Database Connectivity Failure",
                description=f"Database errors recorded: {db_errors} failures, {db_conns} active pool connections.",
                severity=IncidentSeverityEnum.CRITICAL,
                metric_name="db_query_errors",
                observed_value=float(db_errors),
                threshold_value=1.0,
            )

        # ---------------------------------------------------------
        # 8. Repeated Failed Login Attempts
        # ---------------------------------------------------------
        failed_logins = 0
        for log in logs:
            ev_type = (log.get("event_type") or "").upper()
            msg = (log.get("message") or "").lower()
            if (
                ev_type in ("FAILED_LOGIN", "AUTH_FAILURE", "LOGIN_FAILURE")
                or "failed login" in msg
                or "invalid credentials" in msg
            ):
                failed_logins += 1

        if failed_logins >= 3:
            cls._upsert_incident(
                db,
                detected_incidents,
                scenario_type="failed_logins",
                source_id=source_id,
                service_name=service_name,
                title="Repeated Authentication Failures Detected",
                description=f"Detected {failed_logins} failed login attempts in collection batch (threshold: 3).",
                severity=IncidentSeverityEnum.HIGH,
                metric_name="failed_logins_count",
                observed_value=float(failed_logins),
                threshold_value=3.0,
            )

        return detected_incidents

    @classmethod
    def _upsert_incident(
        cls,
        db: Session,
        incident_list: List[ActiveIncidentRecord],
        scenario_type: str,
        source_id: str,
        service_name: str,
        title: str,
        description: str,
        severity: IncidentSeverityEnum,
        metric_name: Optional[str] = None,
        observed_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
    ):
        """Prevent duplicate active incidents for a continuous condition."""
        existing = (
            db.query(ActiveIncidentRecord)
            .filter(
                ActiveIncidentRecord.scenario_type == scenario_type,
                ActiveIncidentRecord.source_id == source_id,
                ActiveIncidentRecord.status == "ACTIVE",
            )
            .first()
        )

        if existing:
            # Update metric observations
            existing.observed_value = observed_value
            existing.description = description
            db.commit()
            incident_list.append(existing)
            return

        new_incident = ActiveIncidentRecord(
            incident_id=f"inc_{scenario_type}_{uuid4().hex[:8]}",
            title=title,
            description=description,
            severity=severity.value,
            status=IncidentStatusEnum.ACTIVE.value,
            scenario_type=scenario_type,
            source_id=source_id,
            service_name=service_name,
            metric_name=metric_name,
            observed_value=observed_value,
            threshold_value=threshold_value,
            detected_at=datetime.now(timezone.utc),
        )
        db.add(new_incident)
        db.commit()
        incident_list.append(new_incident)
        logger.info(f"Created active incident: {new_incident.incident_id} [{new_incident.title}]")
