"""Unified Telemetry Collection Orchestrator
Coordinates host and application collection into a single TelemetryPayload.
"""

from datetime import datetime, timezone
import socket
from typing import Optional
from app.collection.system_collector import SystemMetricsCollector
from app.collection.app_collector import ApplicationMetricsCollector
from app.schemas.telemetry import (
    SourceIdentifier,
    SourceType,
    TelemetryPayload,
)
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("orchestrator")


class CollectionOrchestrator:
    """Orchestrates collection across host system and monitored applications."""

    def __init__(
        self,
        system_collector: Optional[SystemMetricsCollector] = None,
        app_collector: Optional[ApplicationMetricsCollector] = None,
    ):
        self.system_collector = system_collector or SystemMetricsCollector()
        self.app_collector = app_collector or ApplicationMetricsCollector(
            base_url=settings.DEMO_PORTAL_BASE_URL,
            timeout_seconds=settings.COLLECTION_TIMEOUT_SECONDS,
        )

    def _get_local_source_info(self) -> SourceIdentifier:
        """Resolve local hostname and IP address."""
        hostname = "localhost"
        ip_addr = "127.0.0.1"
        try:
            hostname = socket.gethostname()
            ip_addr = socket.gethostbyname(hostname)
        except Exception:
            pass

        return SourceIdentifier(
            source_id="nexus-demo-portal",
            source_type=SourceType.APPLICATION,
            environment="production",
            hostname=hostname,
            ip_address=ip_addr,
        )

    async def collect_batch(self, include_events: bool = True) -> TelemetryPayload:
        """Execute a full collection cycle."""
        logger.info("Starting collection cycle")
        source = self._get_local_source_info()
        collected_at = datetime.now(timezone.utc)

        # 1. Collect Host Metrics
        sys_metrics = self.system_collector.collect()

        # 2. Collect App Metrics
        app_metrics = await self.app_collector.collect_metrics()

        # 3. Collect Logs/Audit Events
        logs = []
        if include_events:
            logs = await self.app_collector.collect_events(limit=50)

        payload = TelemetryPayload(
            source=source,
            collected_at=collected_at,
            system_metrics=sys_metrics,
            application_metrics=app_metrics,
            logs=logs,
            metadata={
                "collector_version": settings.COLLECTOR_VERSION,
                "environment": settings.ENVIRONMENT,
                "collection_source": "orchestrator",
            },
            is_sanitized=False,
        )

        logger.info(
            f"Collection cycle complete: payload_id={payload.payload_id}, "
            f"cpu={sys_metrics.cpu_utilization_percent}%, "
            f"app_status={app_metrics.status}, logs_count={len(logs)}"
        )
        return payload
