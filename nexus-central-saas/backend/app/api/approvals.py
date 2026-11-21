"""Engineer Approval API Endpoints (Feature 4)"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_engineer
from app.approval.service import EngineerApprovalService
from app.schemas.resolution import ResolutionOperationEnum

approvals_router = APIRouter(prefix="/approvals", tags=["Engineer Approval"])


class ProposeOperationRequest(BaseModel):
    incident_id: str
    operation_type: ResolutionOperationEnum
    parameters: Dict[str, Any] = {}
    description: str


class DecisionRequest(BaseModel):
    reason: Optional[str] = None


@approvals_router.post("/propose")
def propose_operation(
    req: ProposeOperationRequest,
    engineer: str = Depends(get_current_engineer),
    db: Session = Depends(get_db),
):
    """Propose a permitted problem-resolution operation."""
    try:
        op = EngineerApprovalService.propose_operation(
            incident_id=req.incident_id,
            operation_type=req.operation_type,
            parameters=req.parameters,
            description=req.description,
            db=db,
        )
        return {
            "operation_id": op.operation_id,
            "incident_id": op.incident_id,
            "operation_type": op.operation_type,
            "status": op.status,
            "description": op.description,
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@approvals_router.get("/pending")
def list_pending_approvals(db: Session = Depends(get_db)):
    """List operations awaiting engineer approval."""
    ops = EngineerApprovalService.list_pending(db)
    result = []
    for op in ops:
        result.append({
            "operation_id": op.operation_id,
            "incident_id": op.incident_id,
            "operation_type": op.operation_type,
            "description": op.description,
            "status": op.status,
            "parameters": json.loads(op.parameters_json),
            "created_at": op.created_at.isoformat() if op.created_at else None,
        })
    return result


@approvals_router.get("/{operation_id}")
def get_operation_details(operation_id: str, db: Session = Depends(get_db)):
    """Fetch details of an approval operation."""
    op = EngineerApprovalService.get_operation(operation_id, db)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return {
        "operation_id": op.operation_id,
        "incident_id": op.incident_id,
        "operation_type": op.operation_type,
        "description": op.description,
        "status": op.status,
        "parameters": json.loads(op.parameters_json),
        "approved_by": op.approved_by,
        "approval_reason": op.approval_reason,
        "approved_at": op.approved_at.isoformat() if op.approved_at else None,
        "executed_at": op.executed_at.isoformat() if op.executed_at else None,
        "result": json.loads(op.result_json) if op.result_json else None,
    }


@approvals_router.post("/{operation_id}/approve")
def approve_operation(
    operation_id: str,
    body: DecisionRequest = None,
    engineer: str = Depends(get_current_engineer),
    db: Session = Depends(get_db),
):
    """Explicitly authorize an operation."""
    reason = body.reason if body else None
    try:
        op = EngineerApprovalService.approve(
            operation_id=operation_id,
            engineer_username=engineer,
            reason=reason,
            db=db,
        )
        return {
            "status": "APPROVED",
            "operation_id": op.operation_id,
            "approved_by": op.approved_by,
            "approved_at": op.approved_at.isoformat(),
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@approvals_router.post("/{operation_id}/reject")
def reject_operation(
    operation_id: str,
    body: DecisionRequest = None,
    engineer: str = Depends(get_current_engineer),
    db: Session = Depends(get_db),
):
    """Explicitly reject an operation."""
    reason = body.reason if body else None
    try:
        op = EngineerApprovalService.reject(
            operation_id=operation_id,
            engineer_username=engineer,
            reason=reason,
            db=db,
        )
        return {
            "status": "REJECTED",
            "operation_id": op.operation_id,
            "rejected_by": op.approved_by,
            "rejected_at": op.approved_at.isoformat(),
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
