"""Telemetry Ingestion Endpoints (Feature 1: Receive Data)"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_collector_api_key
from app.schemas.approval import ApprovedSubmission, ApprovalDecisionEnum
from app.ingestion.processor import TelemetryProcessor

ingestion_router = APIRouter(tags=["Telemetry Ingestion"])


def verify_collector_auth(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> str:
    """Validate incoming Local Collector API Key."""
    if not x_api_key or not verify_collector_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
    return x_api_key


@ingestion_router.post("/api/v1/ingest")
@ingestion_router.post("/api/v1/saas/ingest")
def ingest_telemetry(
    submission: ApprovedSubmission,
    api_key: str = Depends(verify_collector_auth),
    db: Session = Depends(get_db),
):
    """Receive, validate, and store approved telemetry from Local Collector."""
    # 1. Require explicit APPROVED decision
    if submission.decision != ApprovalDecisionEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Central SaaS only accepts APPROVED telemetry (received: {submission.decision})",
        )

    # 2. Strict Sanitization Invariant
    if not submission.sanitized_payload.is_sanitized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Central SaaS strictly rejects unsanitized telemetry (is_sanitized=False)",
        )

    # 3. Process and persist
    ack = TelemetryProcessor.process_submission(submission, db)
    return ack


@ingestion_router.get("/api/v1/telemetry/recent")
def list_recent_telemetry(limit: int = 20, db: Session = Depends(get_db)):
    """Retrieve recently accepted telemetry records."""
    return TelemetryProcessor.get_recent_telemetry(db, limit=limit)
