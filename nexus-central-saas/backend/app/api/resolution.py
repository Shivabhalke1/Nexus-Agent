"""Problem Resolution API Endpoints (Feature 5: Resolve Problem)"""

import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_engineer
from app.models.entities import ResolutionOperationRecord
from app.resolution.registry import get_permitted_operations
from app.resolution.service import (
    ProblemResolutionService,
    OperationNotApprovedError,
    InvalidOperationError,
)

resolution_router = APIRouter(prefix="/resolution", tags=["Problem Resolution"])


@resolution_router.get("/registry")
def list_permitted_operations():
    """List explicitly permitted resolution operations."""
    return get_permitted_operations()


@resolution_router.post("/{operation_id}/execute")
async def execute_resolution_operation(
    operation_id: str,
    engineer: str = Depends(get_current_engineer),
    db: Session = Depends(get_db),
):
    """Execute an authorized problem-resolution operation."""
    try:
        result = await ProblemResolutionService.execute_operation(
            operation_id=operation_id,
            engineer_username=engineer,
            db=db,
        )
        return result
    except OperationNotApprovedError as ona:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ona))
    except InvalidOperationError as ioe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ioe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@resolution_router.get("/history")
def list_resolution_history(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve history of resolution operations and execution results."""
    records = (
        db.query(ResolutionOperationRecord)
        .order_by(ResolutionOperationRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for r in records:
        result.append({
            "operation_id": r.operation_id,
            "incident_id": r.incident_id,
            "operation_type": r.operation_type,
            "description": r.description,
            "status": r.status,
            "approved_by": r.approved_by,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            "executed_at": r.executed_at.isoformat() if r.executed_at else None,
            "result": json.loads(r.result_json) if r.result_json else None,
        })
    return result
