"""System and Application Health Calculation Engine (Feature 2)"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import TelemetryRecord, Collector, ActiveIncidentRecord
from app.schemas.health import HealthStateEnum, ServiceHealthDetail, SystemHealthSummary
from app.core.config import settings
import json


class HealthEngine:
    """Computes overall and service-level health states across the 4 required tiers:

    1. Excellent
    2. Good
    3. Fair
    4. Poor
    """

    @classmethod
    def evaluate_service_health(cls, app_metrics: Optional[Dict], sys_metrics: Optional[Dict]) -> HealthStateEnum:
        """Evaluate metrics against thresholds."""
        if not app_metrics and not sys_metrics:
            return HealthStateEnum.POOR

        status = (app_metrics or {}).get("status", "healthy").lower()
        if status in ("down", "unresponsive", "error"):
            return HealthStateEnum.POOR

        cpu = (sys_metrics or {}).get("cpu_utilization_percent", 0.0)
        mem = (sys_metrics or {}).get("memory_utilization_percent", 0.0)
        disk = (sys_metrics or {}).get("disk_utilization_percent", 0.0)
        latency = (app_metrics or {}).get("avg_response_time_ms", 0.0)
        error_rate = (app_metrics or {}).get("error_rate", 0.0)
        db_errors = (app_metrics or {}).get("db_query_errors", 0)

        # Check POOR thresholds
        if (
            cpu >= settings.CPU_FAIR_MAX  # >= 85%
            or mem >= settings.MEMORY_FAIR_MAX  # >= 90%
            or disk >= 95.0
            or latency >= 800.0
            or error_rate >= 0.10
            or db_errors > 0
        ):
            return HealthStateEnum.POOR

        # Check FAIR thresholds
        if (
            cpu >= settings.CPU_GOOD_MAX  # >= 70%
            or mem >= settings.MEMORY_GOOD_MAX  # >= 75%
            or latency >= 300.0
            or error_rate >= 0.03
        ):
            return HealthStateEnum.FAIR

        # Check GOOD thresholds
        if (
            cpu >= settings.CPU_EXCELLENT_MAX  # >= 50%
            or mem >= settings.MEMORY_EXCELLENT_MAX  # >= 60%
            or latency >= 100.0
            or error_rate >= 0.01
        ):
            return HealthStateEnum.GOOD

        # EXCELLENT
        return HealthStateEnum.EXCELLENT

    @classmethod
    def get_system_health(cls, db: Session) -> SystemHealthSummary:
        """Compute system health summary using the latest persisted telemetry."""
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(seconds=settings.STALE_TELEMETRY_THRESHOLD_SECONDS)

        # 1. Fetch latest telemetry record
        latest_record = db.query(TelemetryRecord).order_by(TelemetryRecord.received_at.desc()).first()

        # 2. Check active incidents count
        active_incidents_count = (
            db.query(ActiveIncidentRecord)
            .filter(ActiveIncidentRecord.status == "ACTIVE")
            .count()
        )

        if not latest_record:
            return SystemHealthSummary(
                overall_health=HealthStateEnum.POOR,
                active_services_count=0,
                total_incidents_active=active_incidents_count,
                last_received_at=None,
                collector_connected=False,
                is_telemetry_stale=True,
                services=[],
                system_metrics={},
            )

        # Parse stored payload
        payload = json.loads(latest_record.payload_json)
        sys_data = payload.get("system_metrics")
        app_data = payload.get("application_metrics")
        source = payload.get("source", {})
        service_name = (app_data or {}).get("service_name", source.get("source_id", "monitored-service"))

        # Check staleness
        received_at = latest_record.received_at
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)
        is_stale = received_at < stale_threshold

        health_state = cls.evaluate_service_health(app_data, sys_data)

        # If telemetry is stale, health degrades to Fair or Poor
        if is_stale and health_state in (HealthStateEnum.EXCELLENT, HealthStateEnum.GOOD):
            health_state = HealthStateEnum.FAIR

        service_detail = ServiceHealthDetail(
            service_name=service_name,
            health_state=health_state,
            status_indicator="stale" if is_stale else (app_data or {}).get("status", "healthy"),
            cpu_percent=(sys_data or {}).get("cpu_utilization_percent"),
            memory_percent=(sys_data or {}).get("memory_utilization_percent"),
            disk_percent=(sys_data or {}).get("disk_utilization_percent"),
            error_rate=(app_data or {}).get("error_rate"),
            avg_latency_ms=(app_data or {}).get("avg_response_time_ms"),
            active_db_connections=(app_data or {}).get("active_db_connections"),
            db_pool_active=(app_data or {}).get("db_pool_active"),
            db_pool_max=(app_data or {}).get("db_pool_max"),
            cache_hit_rate_percent=(app_data or {}).get("cache_hit_rate_percent"),
            active_threads=(app_data or {}).get("active_threads"),
            event_loop_latency_ms=(app_data or {}).get("event_loop_latency_ms"),
            orders_per_minute=(app_data or {}).get("orders_per_minute"),
            cart_abandonment_rate=(app_data or {}).get("cart_abandonment_rate"),
            revenue_at_risk_usd=(app_data or {}).get("revenue_at_risk_usd"),
            active_trace_id=(app_data or {}).get("active_trace_id"),
            last_telemetry_at=received_at,
            is_stale=is_stale,
        )

        return SystemHealthSummary(
            overall_health=health_state,
            active_services_count=1,
            total_incidents_active=active_incidents_count,
            last_received_at=received_at,
            collector_connected=not is_stale,
            is_telemetry_stale=is_stale,
            services=[service_detail],
            system_metrics=sys_data or {},
        )
