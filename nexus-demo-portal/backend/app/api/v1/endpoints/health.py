"""Health and readiness diagnostic endpoints."""
import time
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db, check_db_health
from app.schemas.health import HealthResponse, ComponentHealth

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", response_model=HealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    """Comprehensive health check checking backend core and database connection."""
    start_time = time.perf_counter()
    db_healthy = False
    db_latency_ms = None
    db_message = None

    try:
        t0 = time.perf_counter()
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        db_healthy = True
        db_message = "Connected"
    except Exception as exc:
        db_message = f"Connection failed: {str(exc)}"

    overall_status = "healthy" if db_healthy else "degraded"
    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    response_data = HealthResponse(
        status=overall_status,
        service=settings.SERVICE_NAME,
        environment=settings.ENVIRONMENT,
        timestamp=time.time(),
        components={
            "api": ComponentHealth(
                status="healthy",
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                message="API runtime operational",
            ),
            "database": ComponentHealth(
                status="healthy" if db_healthy else "unhealthy",
                latency_ms=db_latency_ms,
                message=db_message,
            ),
        },
    )

    return JSONResponse(status_code=status_code, content=response_data.model_dump())


@router.get("/health/live")
def get_liveness():
    """Kubernetes/container liveness probe."""
    return {"status": "alive", "timestamp": time.time()}


@router.get("/health/ready")
def get_readiness():
    """Readiness probe checking database availability."""
    is_ready = check_db_health()
    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "Database is not reachable"},
        )
    return {"status": "ready", "database": "connected"}
