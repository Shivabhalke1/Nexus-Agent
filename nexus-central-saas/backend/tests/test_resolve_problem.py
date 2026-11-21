"""Unit and Integration Tests for Problem Resolution (Feature 5: Resolve Problem)"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.entities import ActiveIncidentRecord, ResolutionOperationRecord
from app.schemas.resolution import ResolutionOperationEnum, ExecutionOutcomeEnum

client = TestClient(app)


@pytest.fixture
def auth_headers():
    resp = client.post("/api/v1/auth/login", json={"username": "engineer", "password": "engineer123!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def active_incident_with_operation():
    db = SessionLocal()
    inc = ActiveIncidentRecord(
        incident_id="inc_resolve_test_001",
        title="High Error Rate",
        description="Application error rate reached 20%",
        severity="CRITICAL",
        status="ACTIVE",
        scenario_type="increased_errors",
        source_id="nexus-demo-portal",
        service_name="demo-portal",
    )
    db.add(inc)
    db.commit()

    op = ResolutionOperationRecord(
        operation_id="op_resolve_test_001",
        incident_id=inc.incident_id,
        operation_type=ResolutionOperationEnum.CLEAR_APP_CACHE.value,
        parameters_json="{}",
        description="Flush app memory cache",
        status=ExecutionOutcomeEnum.PENDING_APPROVAL.value,
    )
    db.add(op)
    db.commit()

    yield inc, op

    db.query(ResolutionOperationRecord).filter(ResolutionOperationRecord.operation_id == "op_resolve_test_001").delete()
    db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == "inc_resolve_test_001").delete()
    db.commit()
    db.close()


def test_registry_lists_permitted_operations():
    resp = client.get("/api/v1/resolution/registry")
    assert resp.status_code == 200
    ops = resp.json()
    op_types = [o["operation_type"] for o in ops]
    assert "RESTART_SERVICE" in op_types
    assert "CLEAR_APP_CACHE" in op_types
    assert "SCALE_REPLICAS" in op_types
    assert "RESET_DB_POOL" in op_types
    assert "RESET_FAILURE_SIMULATOR" in op_types


def test_unapproved_operation_cannot_execute(auth_headers, active_incident_with_operation):
    inc, op = active_incident_with_operation
    # Operation is still PENDING_APPROVAL
    resp = client.post(f"/api/v1/resolution/{op.operation_id}/execute", headers=auth_headers)
    assert resp.status_code == 400
    assert "cannot be executed because status is 'PENDING_APPROVAL'" in resp.json()["detail"]


def test_approved_operation_executes_successfully(auth_headers, active_incident_with_operation):
    inc, op = active_incident_with_operation

    # 1. Approve operation first
    approve_resp = client.post(
        f"/api/v1/approvals/{op.operation_id}/approve",
        json={"reason": "Approved for execution"},
        headers=auth_headers,
    )
    assert approve_resp.status_code == 200

    # 2. Execute operation
    exec_resp = client.post(f"/api/v1/resolution/{op.operation_id}/execute", headers=auth_headers)
    assert exec_resp.status_code == 200
    data = exec_resp.json()
    assert data["status"] == "SUCCESSFUL"
    assert data["executed_by"] == "engineer"

    # 3. Verify incident was marked RESOLVED
    db = SessionLocal()
    updated_inc = db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == inc.incident_id).first()
    assert updated_inc.status == "RESOLVED"
    assert updated_inc.resolution_operation_id == op.operation_id
    db.close()

    # 4. Check resolution history endpoint
    hist_resp = client.get("/api/v1/resolution/history")
    assert hist_resp.status_code == 200
    op_ids = [h["operation_id"] for h in hist_resp.json()]
    assert op.operation_id in op_ids
