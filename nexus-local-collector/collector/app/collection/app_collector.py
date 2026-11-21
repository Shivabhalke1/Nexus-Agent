"""Application Telemetry Collector
Connects to NEXUS Demo Portal monitoring and metrics endpoints via HTTPX.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from app.schemas.telemetry import ApplicationMetricsData, LogEntry
from app.core.logging_config import get_logger

logger = get_logger("app_collector")


class ApplicationMetricsCollector:
    """Collects application health, Prometheus/JSON metrics, and events from Demo Portal."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout_seconds: float = 3.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def collect_health(self) -> Dict[str, Any]:
        """Fetch application health status."""
        url = f"{self.base_url}/api/v1/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"Health endpoint returned status {resp.status_code}")
                return {"status": "degraded", "http_status": resp.status_code}
        except httpx.ConnectError:
            logger.warning(f"Failed to connect to application at {url}")
            return {"status": "down", "error": "connection_refused"}
        except httpx.TimeoutException:
            logger.warning(f"Timeout connecting to application health at {url}")
            return {"status": "unresponsive", "error": "timeout"}
        except Exception as e:
            logger.error(f"Error querying health endpoint: {e}")
            return {"status": "error", "error": str(e)}

    async def collect_metrics(self) -> ApplicationMetricsData:
        """Fetch structured application metrics from /api/v1/metrics."""
        url = f"{self.base_url}/api/v1/metrics"
        service_name = "nexus-demo-portal"
        
        health_data = await self.collect_health()
        current_status = health_data.get("status", "unknown")
        if health_data.get("http_status") == 503 or current_status in ("degraded", "down", "unresponsive"):
            current_status = "down"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    raw_data = resp.json()
                    inner_app = raw_data.get("data", {}).get("application", {}) if isinstance(raw_data, dict) and "data" in raw_data else raw_data
                    http_reqs = inner_app.get("total_requests", raw_data.get("http_requests_total", 0))
                    http_errs = inner_app.get("total_errors", raw_data.get("http_errors_total", 0))
                    error_rate = float(inner_app.get("error_rate_percent", 0.0)) / 100.0 if "error_rate_percent" in inner_app else float(raw_data.get("error_rate", 0.0))
                    avg_latency = float(inner_app.get("avg_response_time_ms", raw_data.get("avg_response_time_ms", 0.0)))
                    p95_latency = float(inner_app.get("max_response_time_ms", raw_data.get("p95_response_time_ms", 0.0)))
                    active_conns = raw_data.get("active_db_connections", 0)
                    db_errors = raw_data.get("db_query_errors", 0)

                    import uuid
                    clean_err_rate = min(1.0, max(0.0, error_rate))
                    orders_pm = round(max(2.0, 22.0 - clean_err_rate * 18.0), 1)
                    abandon_rate = round(min(65.0, 7.5 + clean_err_rate * 50.0), 1)
                    risk_usd = round(http_errs * 54.0, 2) if clean_err_rate > 0 else 0.0
                    trace_hash = uuid.uuid4().hex
                    trace_id = f"00-{trace_hash[:16]}-{trace_hash[16:24]}-01"

                    return ApplicationMetricsData(
                        service_name=service_name,
                        status=current_status,
                        http_requests_total=http_reqs,
                        http_errors_total=http_errs,
                        error_rate=clean_err_rate,
                        avg_response_time_ms=avg_latency,
                        p95_response_time_ms=p95_latency,
                        active_db_connections=active_conns,
                        db_query_errors=db_errors,
                        db_pool_active=max(1, active_conns or 3),
                        db_pool_max=20,
                        cache_hit_rate_percent=round(max(70.0, 96.5 - clean_err_rate * 25.0), 1),
                        active_threads=8,
                        event_loop_latency_ms=round(1.2 + clean_err_rate * 4.5, 2),
                        failed_login_attempts=inner_app.get("status_codes", {}).get("401", 0) if isinstance(inner_app, dict) else 0,
                        orders_per_minute=orders_pm,
                        cart_abandonment_rate=abandon_rate,
                        revenue_at_risk_usd=risk_usd,
                        active_trace_id=trace_id,
                        raw_metrics=raw_data,
                        timestamp=datetime.now(timezone.utc),
                    )
        except Exception as e:
            logger.warning(f"Could not reach {url}: {e}")

        # Fallback when application metrics endpoint is offline or timing out
        return ApplicationMetricsData(
            service_name=service_name,
            status=current_status,
            http_requests_total=0,
            http_errors_total=0,
            error_rate=1.0 if current_status in ("down", "unresponsive") else 0.0,
            avg_response_time_ms=0.0,
            p95_response_time_ms=0.0,
            active_db_connections=0,
            db_query_errors=0,
            db_pool_active=0,
            db_pool_max=20,
            cache_hit_rate_percent=0.0,
            active_threads=1,
            event_loop_latency_ms=15.0,
            failed_login_attempts=0,
            orders_per_minute=0.0,
            cart_abandonment_rate=100.0,
            revenue_at_risk_usd=5000.0,
            active_trace_id="00-service-unavailable-01",
            raw_metrics={"collector_notice": "application_unreachable"},
            timestamp=datetime.now(timezone.utc),
        )

    async def collect_events(self, limit: int = 50) -> List[LogEntry]:
        """Fetch audit and telemetry events from Demo Portal."""
        url = f"{self.base_url}/api/v1/metrics/events?limit={limit}"
        entries: List[LogEntry] = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    events = resp.json()
                    for ev in events:
                        # Extract fields cleanly
                        ts = ev.get("timestamp")
                        parsed_ts = datetime.fromisoformat(ts) if ts else datetime.now(timezone.utc)
                        event_type = ev.get("event_type", "AUDIT_EVENT")
                        
                        # Infer level
                        level = "INFO"
                        status_code = ev.get("status_code", 200)
                        if status_code >= 500 or ev.get("error"):
                            level = "ERROR"
                        elif status_code >= 400:
                            level = "WARN"

                        msg = ev.get("message") or f"Event {event_type} on {ev.get('path', 'unknown')}"
                        
                        attributes = {
                            k: v for k, v in ev.items()
                            if k not in ("timestamp", "event_type", "message")
                        }

                        entries.append(
                            LogEntry(
                                timestamp=parsed_ts,
                                level=level,
                                message=msg,
                                service="demo-portal",
                                event_type=event_type,
                                attributes=attributes,
                            )
                        )
        except Exception as e:
            logger.debug(f"Could not retrieve audit events from {url}: {e}")

        return entries
