"""Approval Service
Manages administrator approvals, enforces hard policy guardrails,
verifies cryptographic integrity, and records immutable audit trails.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.approval.store import ApprovalStore
from app.schemas.approval import (
    ApprovalDecisionEnum,
    ApprovalRequest,
    ApprovedSubmission,
    ApprovalAuditRecord,
)
from app.schemas.telemetry import TelemetryPayload
from app.schemas.policy import PolicyValidationResult
from app.core.security import compute_payload_integrity_hash
from app.core.logging_config import get_logger

logger = get_logger("approval_service")


class PolicyViolationBlockedError(Exception):
    """Raised when an administrator attempts to approve a policy-blocked payload."""
    pass


class IntegrityMismatchError(Exception):
    """Raised when the payload integrity hash fails verification."""
    pass


class ApprovalService:
    """Orchestrates human telemetry approval workflows."""

    def __init__(self, store: Optional[ApprovalStore] = None):
        self.store = store or ApprovalStore()

    def create_approval_request(
        self,
        sanitized_payload: TelemetryPayload,
        policy_validation: PolicyValidationResult,
        detection_summary: Optional[Dict[str, Any]] = None,
    ) -> ApprovalRequest:
        """Create and persist a pending approval request."""
        payload_dict = sanitized_payload.model_dump(mode="json")
        integrity_hash = compute_payload_integrity_hash(payload_dict)

        req = ApprovalRequest(
            payload_id=sanitized_payload.payload_id,
            status=ApprovalDecisionEnum.PENDING,
            source=sanitized_payload.source,
            sanitized_payload=sanitized_payload,
            payload_integrity_hash=integrity_hash,
            policy_validation=policy_validation,
            detection_summary=detection_summary or {},
        )
        self.store.save_request(req)
        logger.info(f"Created approval request {req.request_id} for payload {req.payload_id}")
        return req

    def list_pending_requests(self) -> List[ApprovalRequest]:
        """Fetch all requests pending administrator review."""
        return self.store.list_pending()

    def purge_old_pending(self, keep_latest: int = 10) -> int:
        """Purge stale pending requests, keeping only the most recent N items."""
        return self.store.purge_old_pending(keep_latest=keep_latest)

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Fetch a specific approval request by ID."""
        return self.store.get_request(request_id)

    def approve(
        self,
        request_id: str,
        admin_username: str,
        notes: Optional[str] = None,
    ) -> ApprovedSubmission:
        """Approve a pending request with hard policy enforcement and integrity check."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Approval request '{request_id}' not found")

        # 1. HARD POLICY GUARDRAIL: Cannot override a hard policy block
        if not req.policy_validation.can_be_approved:
            logger.error(
                f"Attempted to approve policy-blocked payload {req.payload_id}. "
                f"Action blocked by privacy guardrail."
            )
            raise PolicyViolationBlockedError(
                f"Payload '{req.payload_id}' failed policy validation and cannot be approved"
            )

        # 2. Cryptographic Integrity Verification
        current_dict = req.sanitized_payload.model_dump(mode="json")
        computed_hash = compute_payload_integrity_hash(current_dict)
        if computed_hash != req.payload_integrity_hash:
            logger.error(
                f"Integrity check failed for {req.payload_id}: "
                f"stored={req.payload_integrity_hash}, computed={computed_hash}"
            )
            raise IntegrityMismatchError("Payload tampered after request creation")

        # 3. Update Request Status
        self.store.update_status(request_id, ApprovalDecisionEnum.APPROVED)

        # 4. Record Immutable Audit Trail
        audit_record = ApprovalAuditRecord(
            request_id=request_id,
            payload_id=req.payload_id,
            decision=ApprovalDecisionEnum.APPROVED,
            decided_by=admin_username,
            timestamp=datetime.now(timezone.utc),
            payload_integrity_hash=computed_hash,
            transmission_status="PENDING_TRANSMISSION",
            notes=notes,
        )
        self.store.record_audit(audit_record)

        logger.info(
            f"Payload {req.payload_id} explicitly APPROVED by admin '{admin_username}' "
            f"with integrity hash {computed_hash[:16]}..."
        )

        return ApprovedSubmission(
            request_id=request_id,
            decision=ApprovalDecisionEnum.APPROVED,
            decision_by=admin_username,
            decision_at=datetime.now(timezone.utc),
            reason=notes,
            approved_payload_hash=computed_hash,
            sanitized_payload=req.sanitized_payload,
        )

    def reject(
        self,
        request_id: str,
        admin_username: str,
        reason: Optional[str] = None,
    ) -> None:
        """Reject a pending telemetry submission."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Approval request '{request_id}' not found")

        self.store.update_status(request_id, ApprovalDecisionEnum.REJECTED)

        audit_record = ApprovalAuditRecord(
            request_id=request_id,
            payload_id=req.payload_id,
            decision=ApprovalDecisionEnum.REJECTED,
            decided_by=admin_username,
            timestamp=datetime.now(timezone.utc),
            payload_integrity_hash=req.payload_integrity_hash,
            transmission_status="REJECTED_NOT_TRANSMITTED",
            notes=reason or "Rejected by administrator",
        )
        self.store.record_audit(audit_record)

        logger.info(f"Payload {req.payload_id} REJECTED by admin '{admin_username}'. Reason: {reason}")
