"""Observability middleware recording latency, request counts, and structured logs."""
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.config import settings
from app.observability.metrics import metrics_collector

logger = logging.getLogger(settings.SERVICE_NAME)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Intercepts all HTTP traffic to record request telemetry and correlation IDs."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()
        request.state.request_id = request_id

        # Proceed with request
        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        endpoint = request.url.path

        # Record in metrics collector
        metrics_collector.record_request(
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Attach telemetry headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        # Log structured request telemetry (skip high-frequency health probes from bloating log files)
        if not endpoint.startswith("/health") and not endpoint == "/metrics":
            logger.info(
                f"HTTP {request.method} {endpoint} -> {response.status_code} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

        return response
