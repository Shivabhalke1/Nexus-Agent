"""Health Monitoring API Endpoints (Feature 2)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.health import SystemHealthSummary
from app.monitoring.health_engine import HealthEngine

health_router = APIRouter(prefix="/health", tags=["System Health"])


@health_router.get("", response_model=SystemHealthSummary)
@health_router.get("/summary", response_model=SystemHealthSummary)
def get_health_summary(db: Session = Depends(get_db)):
    """Retrieve current overall and service health summary."""
    return HealthEngine.get_system_health(db)
