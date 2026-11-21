"""Human Approval Schema Definitions
NEXUS Local Collector - Pydantic v2 Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.telemetry import SourceIdentifier, TelemetryPayload
from app.schemas.policy import PolicyValidationResult


class ApprovalDecisionEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID for approval request")
    payload_id: str = Field(..., description="ID of sanitized payload awaiting approval")
    status: ApprovalDecisionEnum = Field(default=ApprovalDecisionEnum.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: SourceIdentifier = Field(..., description="Origin source identifier")
    sanitized_payload: TelemetryPayload = Field(..., description="The EXACT sanitized payload to be inspected")
    payload_integrity_hash: str = Field(..., description="SHA-256 canonical hash of the sanitized payload")
    policy_validation: PolicyValidationResult = Field(..., description="Policy validation results")
    detection_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of sensitive data protections applied")


class ApprovedSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(..., description="Associated approval request ID")
    decision: ApprovalDecisionEnum = Field(..., description="APPROVED or REJECTED")
    decision_by: str = Field(..., min_length=1, description="Authenticated administrator username")
    decision_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = Field(default=None, description="Optional administrative decision reason or notes")
    approved_payload_hash: str = Field(..., description="Integrity hash that was approved by admin")
    sanitized_payload: TelemetryPayload = Field(..., description="The payload to be transmitted")


class ApprovalAuditRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique audit record ID")
    request_id: str = Field(..., description="Approval request ID")
    payload_id: str = Field(..., description="Payload ID")
    decision: ApprovalDecisionEnum = Field(..., description="APPROVED or REJECTED")
    decided_by: str = Field(..., description="Administrator username")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload_integrity_hash: str = Field(..., description="SHA-256 hash of the exact payload")
    transmission_status: Optional[str] = Field(default="NOT_TRANSMITTED", description="TRANSMITTED, FAILED, or NOT_TRANSMITTED")
    notes: Optional[str] = Field(default=None)
