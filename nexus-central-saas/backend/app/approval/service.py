"""Engineer Approval Service (Feature 4)"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.entities import ResolutionOperationRecord, ActiveIncidentRecord
from app.schemas.resolution import (
    ResolutionOperationEnum,
    ExecutionOutcomeEnum,
    ResolutionOperation,
    EngineerApprovalDecision,
)
from app.core.logging_config import get_logger

logger = get_logger("approval_service")


class ApprovalSecurityError(Exception):
    """Raised when an unauthorized user attempts approval or parameters are mutated."""
    pass


class EngineerApprovalService:
    """Manages explicit engineer authorizations for problem-resolution operations."""

    @classmethod
    def propose_operation(
        cls,
        incident_id: str,
        operation_type: ResolutionOperationEnum,
        parameters: Dict[str, Any],
        description: str,
        db: Session,
    ) -> ResolutionOperationRecord:
        """Create a proposed resolution operation pending engineer review."""
        incident = db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found")

        op = ResolutionOperationRecord(
            operation_id=f"op_{uuid4().hex[:12]}",
            incident_id=incident_id,
            operation_type=operation_type.value,
            parameters_json=json.dumps(parameters),
            description=description,
            status=ExecutionOutcomeEnum.PENDING_APPROVAL.value,
        )
        db.add(op)
        db.commit()
        logger.info(f"Proposing operation {op.operation_id} [{op.operation_type}] for incident {incident_id}")
        return op

    @classmethod
    def list_pending(cls, db: Session) -> List[ResolutionOperationRecord]:
        """Fetch all operations awaiting engineer approval."""
        return (
            db.query(ResolutionOperationRecord)
            .filter(ResolutionOperationRecord.status == ExecutionOutcomeEnum.PENDING_APPROVAL.value)
            .order_by(ResolutionOperationRecord.created_at.desc())
            .all()
        )

    @classmethod
    def get_operation(cls, operation_id: str, db: Session) -> Optional[ResolutionOperationRecord]:
        """Fetch operation by ID."""
        return (
            db.query(ResolutionOperationRecord)
            .filter(ResolutionOperationRecord.operation_id == operation_id)
            .first()
        )

    @classmethod
    def approve(
        cls,
        operation_id: str,
        engineer_username: str,
        reason: Optional[str],
        db: Session,
    ) -> ResolutionOperationRecord:
        """Explicitly approve an operation."""
        op = cls.get_operation(operation_id, db)
        if not op:
            raise ValueError(f"Operation '{operation_id}' not found")

        if op.status != ExecutionOutcomeEnum.PENDING_APPROVAL.value:
            raise ValueError(f"Operation is already {op.status}; cannot approve")

        op.status = ExecutionOutcomeEnum.APPROVED.value
        op.approved_by = engineer_username
        op.approval_reason = reason or "Approved by engineer"
        op.approved_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Operation {operation_id} APPROVED by engineer '{engineer_username}'")
        return op

    @classmethod
    def reject(
        cls,
        operation_id: str,
        engineer_username: str,
        reason: Optional[str],
        db: Session,
    ) -> ResolutionOperationRecord:
        """Explicitly reject an operation."""
        op = cls.get_operation(operation_id, db)
        if not op:
            raise ValueError(f"Operation '{operation_id}' not found")

        op.status = ExecutionOutcomeEnum.REJECTED.value
        op.approved_by = engineer_username
        op.approval_reason = reason or "Rejected by engineer"
        op.approved_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Operation {operation_id} REJECTED by engineer '{engineer_username}'")
        return op
