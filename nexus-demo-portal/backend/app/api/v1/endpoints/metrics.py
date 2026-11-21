"""Metrics exposure endpoints for Prometheus scraping and JSON consumers."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.event import ApplicationEvent
from app.schemas.response import APIResponse
from app.observability.metrics import metrics_collector

router = APIRouter(prefix="/metrics", tags=["Observability & Telemetry"])


@router.get("", response_model=APIResponse[dict])
def get_metrics_json():
    """Retrieve structured JSON snapshot of application and system telemetry."""
    return APIResponse(
        success=True,
        message="Metrics snapshot retrieved successfully",
        data={
            "application": metrics_collector.get_application_metrics(),
            "system": metrics_collector.get_system_metrics(),
        },
    )


@router.get("/system", response_model=APIResponse[dict])
def get_system_metrics():
    """Retrieve host utilization telemetry (CPU, Memory, Disk, Threads, Uptime)."""
    return APIResponse(
        success=True,
        message="System telemetry retrieved",
        data=metrics_collector.get_system_metrics(),
    )


@router.get("/events", response_model=APIResponse[List[dict]])
def get_telemetry_events(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve recent application audit events."""
    query = db.query(ApplicationEvent).order_by(ApplicationEvent.timestamp.desc())
    if severity:
        query = query.filter(ApplicationEvent.severity == severity.upper())

    events = query.limit(limit).all()
    events_data = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "severity": e.severity,
            "request_id": e.request_id,
            "timestamp": e.timestamp.isoformat(),
            "payload": e.payload,
        }
        for e in events
    ]

    return APIResponse(
        success=True,
        message="Events retrieved",
        data=events_data,
    )
