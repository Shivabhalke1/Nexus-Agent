"""Unit and Integration Tests for Human Approval Service and Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.approval.store import ApprovalStore
from app.approval.service import (
    ApprovalService,
    PolicyViolationBlockedError,
    IntegrityMismatchError,
)
from app.schemas.approval import ApprovalDecisionEnum
from app.schemas.policy import PolicyValidationResult, PolicyViolation, ViolationSeverityEnum
from app.schemas.telemetry import SourceIdentifier, SourceType, TelemetryPayload, LogEntry
from app.core.security import compute_payload_integrity_hash

client = TestClient(app)


@pytest.fixture
def fresh_service(tmp_path):
    db_file = tmp_path / "test_approval.db"
    store = ApprovalStore(db_path=str(db_file))
    return ApprovalService(store=store)


def test_admin_login():
    # Valid login
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123!"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert len(token) > 20

    # Invalid password
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong_password"})
    assert resp.status_code == 401


def test_approval_lifecycle_compliant(fresh_service):
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(source=source, is_sanitized=True)
    policy_res = PolicyValidationResult(
        payload_id=payload.payload_id,
        is_compliant=True,
        can_be_approved=True,
    )

    req = fresh_service.create_approval_request(payload, policy_res)
    assert req.status == ApprovalDecisionEnum.PENDING

    # Approve
    submission = fresh_service.approve(req.request_id, admin_username="admin", notes="LGTM")
    assert submission.decision == ApprovalDecisionEnum.APPROVED
    assert submission.approved_payload_hash == req.payload_integrity_hash

    # Re-fetch from store to check status updated
    updated_req = fresh_service.get_request(req.request_id)
    assert updated_req.status == ApprovalDecisionEnum.APPROVED


def test_approval_blocked_on_policy_violation(fresh_service):
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(source=source, is_sanitized=False)
    policy_res = PolicyValidationResult(
        payload_id=payload.payload_id,
        is_compliant=False,
        can_be_approved=False,
        violations=[
            PolicyViolation(
                rule_id="POL-BLOCK-TEST",
                rule_name="Blocked Test",
                severity=ViolationSeverityEnum.BLOCK,
                message="Hard block triggered",
            )
        ],
    )

    req = fresh_service.create_approval_request(payload, policy_res)

    # Attempting to approve must fail with PolicyViolationBlockedError
    with pytest.raises(PolicyViolationBlockedError):
        fresh_service.approve(req.request_id, admin_username="admin")


def test_approval_tamper_detection(fresh_service):
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(source=source, is_sanitized=True)
    policy_res = PolicyValidationResult(
        payload_id=payload.payload_id,
        is_compliant=True,
        can_be_approved=True,
    )

    req = fresh_service.create_approval_request(payload, policy_res)

    # Tamper with stored payload directly
    tampered_payload = payload.model_copy(update={"is_sanitized": False})
    with fresh_service.store._get_conn() as conn:
        import json
        conn.execute(
            "UPDATE approval_requests SET sanitized_payload_json = ? WHERE request_id = ?",
            (json.dumps(tampered_payload.model_dump(mode="json")), req.request_id),
        )
        conn.commit()

    # Attempting to approve must raise IntegrityMismatchError
    with pytest.raises(IntegrityMismatchError):
        fresh_service.approve(req.request_id, admin_username="admin")


def test_rejection_workflow(fresh_service):
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    payload = TelemetryPayload(source=source, is_sanitized=True)
    policy_res = PolicyValidationResult(payload_id=payload.payload_id, is_compliant=True, can_be_approved=True)

    req = fresh_service.create_approval_request(payload, policy_res)
    fresh_service.reject(req.request_id, admin_username="admin", reason="Suspicious activity in payload")

    rejected_req = fresh_service.get_request(req.request_id)
    assert rejected_req.status == ApprovalDecisionEnum.REJECTED

    # Audit log check
    history = fresh_service.store.list_audit_history()
    assert len(history) >= 1
    assert history[0]["decision"] == "REJECTED"
    assert history[0]["notes"] == "Suspicious activity in payload"


def test_api_pipeline_and_approval_endpoints():
    # 1. Trigger full pipeline
    resp = client.post("/api/v1/pipeline/run")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "success"
    req_id = res_data["request_id"]

    # 2. List pending
    resp_pending = client.get("/api/v1/approval/pending")
    assert resp_pending.status_code == 200
    pending_ids = [r["request_id"] for r in resp_pending.json()]
    assert req_id in pending_ids

    # 3. Inspect request
    resp_inspect = client.get(f"/api/v1/approval/{req_id}")
    assert resp_inspect.status_code == 200
    assert resp_inspect.json()["request_id"] == req_id

    # 4. Login to get token
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 5. Approve request
    resp_approve = client.post(f"/api/v1/approval/{req_id}/approve", json={"notes": "Approved in API test"}, headers=headers)
    assert resp_approve.status_code == 200
    assert resp_approve.json()["status"] == "APPROVED"

    # 6. Verify audit history
    resp_audit = client.get("/api/v1/approval/history")
    assert resp_audit.status_code == 200
    audit_req_ids = [a["request_id"] for a in resp_audit.json()]
    assert req_id in audit_req_ids
