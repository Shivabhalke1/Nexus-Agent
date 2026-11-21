"""Unit and Integration Tests for Engineer Approval (Feature 4)"""

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
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def active_incident():
    db = SessionLocal()
    inc = ActiveIncidentRecord(
        incident_id="inc_test_approval_001",
        title="High CPU Incident",
        description="CPU reached 92%",
        severity="CRITICAL",
        status="ACTIVE",
        scenario_type="high_cpu",
        source_id="nexus-demo-portal",
        service_name="demo-portal",
    )
    db.add(inc)
    db.commit()
    yield inc
    db.query(ResolutionOperationRecord).filter(ResolutionOperationRecord.incident_id == "inc_test_approval_001").delete()
    db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == "inc_test_approval_001").delete()
    db.commit()
    db.close()


def test_propose_and_approve_lifecycle(auth_headers, active_incident):
    # 1. Propose operation
    propose_payload = {
        "incident_id": active_incident.incident_id,
        "operation_type": "RESTART_SERVICE",
        "parameters": {"service": "demo-portal", "grace_period_seconds": 15},
        "description": "Restart service container to clear runaway CPU threads",
    }
    resp = client.post("/api/v1/approvals/propose", json=propose_payload, headers=auth_headers)
    assert resp.status_code == 200
    op_id = resp.json()["operation_id"]

    # 2. List pending
    list_resp = client.get("/api/v1/approvals/pending")
    assert list_resp.status_code == 200
    pending_ids = [o["operation_id"] for o in list_resp.json()]
    assert op_id in pending_ids

    # 3. Unauthorized approve attempt (no headers) fails
    unauth_resp = client.post(f"/api/v1/approvals/{op_id}/approve")
    assert unauth_resp.status_code == 401

    # 4. Explicit engineer approval
    approve_resp = client.post(
        f"/api/v1/approvals/{op_id}/approve",
        json={"reason": "Approved after reviewing host telemetry metrics"},
        headers=auth_headers,
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"
    assert approve_resp.json()["approved_by"] == "engineer"


def test_reject_workflow(auth_headers, active_incident):
    propose_payload = {
        "incident_id": active_incident.incident_id,
        "operation_type": "SCALE_REPLICAS",
        "parameters": {"replicas": 5},
        "description": "Scale up workers",
    }
    resp = client.post("/api/v1/approvals/propose", json=propose_payload, headers=auth_headers)
    op_id = resp.json()["operation_id"]

    reject_resp = client.post(
        f"/api/v1/approvals/{op_id}/reject",
        json={"reason": "Rejected: cluster at capacity, scale not viable"},
        headers=auth_headers,
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "REJECTED"

    # Verify cannot approve a rejected operation
    retry_approve = client.post(f"/api/v1/approvals/{op_id}/approve", headers=auth_headers)
    assert retry_approve.status_code == 400
