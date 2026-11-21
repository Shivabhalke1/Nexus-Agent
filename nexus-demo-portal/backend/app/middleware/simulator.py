"""Middleware intercepting requests to inject active failure scenario anomalies."""
import asyncio
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.failure_simulator.state import simulator_state


class FailureSimulatorMiddleware(BaseHTTPMiddleware):
    """Inspects active simulation scenarios and applies configured anomalies."""

    async def dispatch(self, request: Request, call_next):
        status = simulator_state.get_status()
        path = request.url.path

        # Never block the simulator control endpoints or emergency reset
        if path.startswith("/api/v1/simulator"):
            return await call_next(request)

        # Scenario 3: Backend Unavailable (HTTP 503)
        if status["backend_unavailable"]["active"]:
            target = status["backend_unavailable"].get("target_endpoint")
            if not target or path.startswith(target):
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": {
                            "code": "SERVICE_UNAVAILABLE",
                            "message": "Simulated backend service outage active.",
                            "simulation": "backend_unavailable",
                        },
                        "request_id": getattr(request.state, "request_id", "sim-503"),
                    },
                )

        # Scenario 4: Database Connection Failure (intercept database operations or health check)
        if status["database_failure"]["active"]:
            if path in {"/api/v1/health", "/api/v1/health/ready"} or path.startswith("/api/v1/products"):
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": {
                            "code": "DATABASE_UNAVAILABLE",
                            "message": "Simulated database connection failure active (non-destructive).",
                            "simulation": "database_failure",
                        },
                        "request_id": getattr(request.state, "request_id", "sim-db-down"),
                    },
                )

        # Scenario 5: Increased Application Errors (HTTP 500)
        if status["increased_errors"]["active"]:
            target = status["increased_errors"].get("target_endpoint")
            if not target or path.startswith(target):
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": "Simulated high application error rate active.",
                            "simulation": "increased_errors",
                        },
                        "request_id": getattr(request.state, "request_id", "sim-500"),
                    },
                )

        # Scenario 2: Slow API Response (Artificial Delay)
        if status["slow_api"]["active"]:
            target = status["slow_api"].get("target_endpoint")
            if not target or path.startswith(target):
                delay_sec = status["slow_api"].get("delay_ms", 1500) / 1000.0
                await asyncio.sleep(delay_sec)

        return await call_next(request)
