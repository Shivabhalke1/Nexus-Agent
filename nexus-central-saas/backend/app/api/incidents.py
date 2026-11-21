"""Incident Management API Endpoints (Feature 3)"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import ActiveIncidentRecord
from app.schemas.incident import IncidentRecord, IncidentStatusEnum
from datetime import datetime, timezone

incidents_router = APIRouter(prefix="/incidents", tags=["Incident Detection"])


@incidents_router.get("", response_model=List[IncidentRecord])
@incidents_router.get("/active", response_model=List[IncidentRecord])
def list_active_incidents(db: Session = Depends(get_db)):
    """Retrieve all currently active detected incidents."""
    incidents = (
        db.query(ActiveIncidentRecord)
        .filter(ActiveIncidentRecord.status == IncidentStatusEnum.ACTIVE.value)
        .order_by(ActiveIncidentRecord.detected_at.desc())
        .all()
    )
    return incidents


@incidents_router.get("/{incident_id}", response_model=IncidentRecord)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific incident."""
    inc = db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@incidents_router.post("/{incident_id}/resolve")
def resolve_incident(incident_id: str, db: Session = Depends(get_db)):
    """Mark an incident as resolved."""
    inc = db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    inc.status = IncidentStatusEnum.RESOLVED.value
    inc.resolved_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "RESOLVED", "incident_id": incident_id, "resolved_at": inc.resolved_at.isoformat()}
