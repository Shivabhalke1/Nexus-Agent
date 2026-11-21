"""Central SaaS Mock Ingestion Endpoint
Used for local testing and self-contained end-to-end verification.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from app.schemas.approval import ApprovedSubmission
from app.core.logging_config import get_logger

logger = get_logger("mock_saas")
mock_saas_router = APIRouter()

# In-memory storage for mock ingested submissions
RECEIVED_SUBMISSIONS: List[Dict[str, Any]] = []


@mock_saas_router.post("/api/v1/saas/ingest")
def mock_ingest(
    submission: ApprovedSubmission,
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """Simulates NEXUS Central SaaS telemetry ingestion."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required X-API-Key header",
        )

    # Verify that payload is sanitized
    if not submission.sanitized_payload.is_sanitized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Central SaaS rejects unsanitized telemetry",
        )

    submission_dict = submission.model_dump(mode="json")
    RECEIVED_SUBMISSIONS.append(submission_dict)
    logger.info(
        f"Mock SaaS successfully received approved submission: request_id={submission.request_id}, "
        f"payload_hash={submission.approved_payload_hash[:16]}..."
    )

    return {
        "status": "ACCEPTED",
        "ingestion_id": f"saas_ingest_{len(RECEIVED_SUBMISSIONS)}",
        "received_at": submission.decision_at.isoformat(),
        "payload_id": submission.sanitized_payload.payload_id,
    }


@mock_saas_router.get("/api/v1/saas/received")
def get_received_submissions():
    """Retrieve all submissions received by mock SaaS."""
    return RECEIVED_SUBMISSIONS


@mock_saas_router.delete("/api/v1/saas/received")
def clear_received_submissions():
    """Clear mock SaaS storage."""
    RECEIVED_SUBMISSIONS.clear()
    return {"status": "cleared"}
