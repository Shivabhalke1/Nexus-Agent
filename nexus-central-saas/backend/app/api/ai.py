"""AI Engine API Endpoints"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import ActiveIncidentRecord, TelemetryRecord
from app.schemas.ai import AIIncidentAnalysis, AIHealthInsight
from app.monitoring.health_engine import HealthEngine
from app.ai.engine import AIRootCauseEngine

ai_router = APIRouter(prefix="/ai", tags=["AI Engine"])


@ai_router.get("/status")
def get_ai_status():
    """Return status and metadata of the integrated AI Engine."""
    return {
        "status": "active",
        "engine_name": "NEXUS Cortex AI Engine",
        "version": "1.0.0",
        "model_architecture": "Multi-Variate Heuristic & Probabilistic Diagnostic Classifier",
        "capabilities": [
            "Root Cause Analysis (RCA)",
            "Anomaly Probability Estimation",
            "Multi-Variate Feature Attribution",
            "Natural Language Technical Explanation Synthesis",
            "Remediation Operation Recommendation",
        ],
        "supported_scenarios": list(AIRootCauseEngine.SCENARIO_PROFILES.keys()),
    }


@ai_router.post("/analyze-incident/{incident_id}", response_model=AIIncidentAnalysis)
def analyze_incident(incident_id: str, db: Session = Depends(get_db)):
    """Run AI Root Cause Analysis on a specific incident."""
    inc = db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )

    # Fetch recent telemetry if available
    recent_telemetry = (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.received_at.desc())
        .limit(5)
        .all()
    )

    analysis = AIRootCauseEngine.analyze_incident(inc, recent_telemetry=recent_telemetry)
    return analysis


@ai_router.get("/insights", response_model=AIHealthInsight)
def get_system_ai_insights(db: Session = Depends(get_db)):
    """Generate high-level AI diagnostic insights for current system health."""
    health_summary = HealthEngine.get_system_health(db)
    active_incidents = (
        db.query(ActiveIncidentRecord)
        .filter(ActiveIncidentRecord.status == "ACTIVE")
        .all()
    )

    insights = AIRootCauseEngine.generate_health_insights(
        overall_health=health_summary.overall_health.value,
        active_incidents=active_incidents,
        metrics=health_summary.system_metrics,
    )
    return insights
