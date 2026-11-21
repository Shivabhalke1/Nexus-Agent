"""Engineer Approval and Problem Resolution Schemas"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class ResolutionOperationEnum(str, Enum):
    RESTART_SERVICE = "RESTART_SERVICE"
    SCALE_REPLICAS = "SCALE_REPLICAS"
    RESET_DB_POOL = "RESET_DB_POOL"
    CLEAR_APP_CACHE = "CLEAR_APP_CACHE"
    RATE_LIMIT_LOGIN = "RATE_LIMIT_LOGIN"
    RESET_FAILURE_SIMULATOR = "RESET_FAILURE_SIMULATOR"


class ExecutionOutcomeEnum(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    SUCCESSFUL = "SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"
    UNEXECUTED = "UNEXECUTED"


class EngineerApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="ignore")

    decision: str  # APPROVED or REJECTED
    engineer_username: str
    reason: Optional[str] = None
    decision_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResolutionOperation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operation_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str = Field(...)
    operation_type: ResolutionOperationEnum = Field(...)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str = Field(...)
    status: ExecutionOutcomeEnum = Field(default=ExecutionOutcomeEnum.PENDING_APPROVAL)
    approval_decision: Optional[EngineerApprovalDecision] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
