"""Approval and Egress Submission Schemas"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.telemetry import TelemetryPayload


class ApprovalDecisionEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovedSubmission(BaseModel):
    model_config = ConfigDict(extra="ignore")

    request_id: str = Field(...)
    decision: ApprovalDecisionEnum = Field(...)
    decision_by: str = Field(..., min_length=1)
    decision_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None
    approved_payload_hash: str = Field(..., min_length=16)
    sanitized_payload: TelemetryPayload = Field(...)
