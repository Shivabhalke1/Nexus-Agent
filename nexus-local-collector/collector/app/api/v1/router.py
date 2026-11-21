"""FastAPI API v1 Router for NEXUS Local Collector
Exposes Authentication, Pipeline Orchestration, and Human Approval endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import verify_password, create_access_token, decode_access_token
from app.collection.orchestrator import CollectionOrchestrator
from app.detection.engine import SensitiveDataDetector
from app.filtering.engine import DataFilterEngine
from app.protection.engine import DataProtectionEngine
from app.analysis.engine import LocalAnalysisEngine
from app.policies.validator import PolicyValidator
from app.approval.service import (
    ApprovalService,
    PolicyViolationBlockedError,
    IntegrityMismatchError,
)
from app.transmission.client import SaaSClient
from app.schemas.approval import ApprovalRequest, ApprovedSubmission
from app.core.logging_config import get_logger

logger = get_logger("api_v1")

router = APIRouter()

# Singletons for services
approval_service = ApprovalService()
orchestrator = CollectionOrchestrator()
detector = SensitiveDataDetector()
filter_engine = DataFilterEngine()
protection_engine = DataProtectionEngine(detector=detector)
analysis_engine = LocalAnalysisEngine()
policy_validator = PolicyValidator(detector=detector)


# -------------------------------------------------------------------
# Auth Dependencies & Schemas
# -------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


def get_current_admin(authorization: Optional[str] = Header(None)) -> str:
    """Verify administrator JWT session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )
    return payload["sub"]


# -------------------------------------------------------------------
# Authentication Endpoints
# -------------------------------------------------------------------
@router.post("/auth/login", response_model=LoginResponse)
def login_admin(creds: LoginRequest):
    """Authenticate administrator and issue JWT access token."""
    if creds.username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(creds.password, settings.ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": creds.username, "role": "admin"})
    return LoginResponse(access_token=token, username=creds.username)


# -------------------------------------------------------------------
# Pipeline Execution Endpoint
# -------------------------------------------------------------------
async def execute_full_pipeline():
    """Execute the full collection -> detection -> filtering -> protection -> analysis -> policy cycle."""
    # 1. Collection
    raw_payload = await orchestrator.collect_batch(include_events=True)

    # 2. Detection (pre-filter findings)
    initial_detection = detector.scan_payload(raw_payload)

    # 3. Filtering
    filtered_payload = filter_engine.filter_payload(raw_payload)

    # 4. Protection
    sanitized_payload = protection_engine.protect_payload(filtered_payload)

    # 5. Local Analysis
    alerts = analysis_engine.analyze_payload(sanitized_payload)

    # 6. Policy Validation
    policy_res = policy_validator.validate_payload(sanitized_payload)

    # 7. Create Approval Request
    approval_req = approval_service.create_approval_request(
        sanitized_payload=sanitized_payload,
        policy_validation=policy_res,
        detection_summary={
            "initial_findings_count": initial_detection.findings_count,
            "alerts_count": len(alerts),
            "alerts": [a.model_dump(mode="json") for a in alerts],
            "sanitization_summary": sanitized_payload.sanitization_summary,
        },
    )

    # Auto-trim backlog: keep latest 12 items max
    approval_service.purge_old_pending(keep_latest=12)

    return {
        "status": "success",
        "request_id": approval_req.request_id,
        "payload_id": sanitized_payload.payload_id,
        "policy_compliant": policy_res.is_compliant,
        "can_be_approved": policy_res.can_be_approved,
        "alerts_detected": len(alerts),
    }


@router.post("/pipeline/run")
async def run_pipeline():
    """Execute the full collection and protection pipeline manually or via event webhook."""
    return await execute_full_pipeline()


# -------------------------------------------------------------------
# Human Approval Endpoints
# -------------------------------------------------------------------
@router.get("/approval/pending")
def list_pending():
    """List all pending approval requests."""
    reqs = approval_service.list_pending_requests()
    results = []
    for r in reqs:
        d = r.model_dump(mode="json")
        d["policy_compliant"] = r.policy_validation.is_compliant if r.policy_validation else True
        d["can_be_approved"] = r.policy_validation.can_be_approved if r.policy_validation else True
        results.append(d)
    return results


@router.post("/approval/purge-old")
def purge_old_requests(keep_latest: int = 10):
    """Purge stale pending requests, keeping only the most recent N items."""
    purged = approval_service.purge_old_pending(keep_latest=keep_latest)
    return {"status": "success", "purged": purged}


@router.get("/approval/history")
def get_approval_history():
    """Retrieve immutable approval audit history."""
    return approval_service.store.list_audit_history(limit=50)


@router.get("/approval/{request_id}")
def get_approval_details(request_id: str):
    """Retrieve full request details for administrator inspection."""
    req = approval_service.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    d = req.model_dump(mode="json")
    d["policy_compliant"] = req.policy_validation.is_compliant if req.policy_validation else True
    d["can_be_approved"] = req.policy_validation.can_be_approved if req.policy_validation else True
    return d


class DecisionPayload(BaseModel):
    notes: Optional[str] = None


@router.post("/approval/{request_id}/approve")
async def approve_telemetry(
    request_id: str,
    body: DecisionPayload = None,
    admin: str = Depends(get_current_admin),
):
    """Explicit administrator approval with hard policy and integrity check."""
    notes = body.notes if body else None
    try:
        submission = approval_service.approve(
            request_id=request_id,
            admin_username=admin,
            notes=notes,
        )

        # Transmit to Central SaaS
        transmission_res = None
        try:
            saas_client = SaaSClient()
            transmission_res = await saas_client.transmit_approved_submission(submission)
            approval_service.store.update_audit_transmission_status(request_id, "TRANSMITTED")
            logger.info(f"Successfully dispatched approved submission {request_id} to Central SaaS")
        except Exception as te:
            logger.warning(f"SaaS transmission note for {request_id}: {te}")
            approval_service.store.update_audit_transmission_status(request_id, f"PENDING_RETRY: {te}")

        return {
            "status": "APPROVED",
            "request_id": request_id,
            "approved_by": admin,
            "approved_payload_hash": submission.approved_payload_hash,
            "transmission": transmission_res,
            "submission": submission.model_dump(mode="json"),
        }
    except PolicyViolationBlockedError as pve:
        raise HTTPException(status_code=400, detail=str(pve))
    except IntegrityMismatchError as ime:
        raise HTTPException(status_code=409, detail=str(ime))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


# -------------------------------------------------------------------
# Privacy Attack Lab Endpoint
# -------------------------------------------------------------------
class AttackSimRequest(BaseModel):
    attack_type: str = "credential_leak"
    payload_text: str


@router.post("/lab/simulate-attack")
def simulate_privacy_attack(body: AttackSimRequest):
    """Interactive Privacy Attack Lab: tests pattern interception, regex, and AST masking."""
    from app.protection.masking import redact_text_patterns
    import hashlib

    original = body.payload_text
    sanitized = redact_text_patterns(original)

    findings = []
    if "[REDACTED_SECRET]" in sanitized:
        findings.append("API Key / Plaintext Password Neutralized")
    if "[REDACTED_TOKEN]" in sanitized:
        findings.append("JWT / Bearer Token Redacted")
    if "[REDACTED_DB_CREDENTIAL]" in sanitized:
        findings.append("Database Connection String Scrubbed")
    if "[REDACTED_PRIVATE_KEY]" in sanitized:
        findings.append("RSA / SSH Private Key Blocked")
    if "[REDACTED_EMAIL]" in sanitized:
        findings.append("Customer PII Email Redacted")

    return {
        "status": "NEUTRALIZED" if findings else "CLEAN",
        "attack_type": body.attack_type,
        "original_payload": original,
        "sanitized_payload": sanitized,
        "findings_neutralized": findings,
        "secrets_leakage_prevented": len(findings) > 0,
        "egress_allowed": True,
        "digest": hashlib.sha256(sanitized.encode("utf-8")).hexdigest(),
    }


@router.post("/approval/{request_id}/reject")
def reject_telemetry(
    request_id: str,
    body: DecisionPayload = None,
    admin: str = Depends(get_current_admin),
):
    """Explicit administrator rejection."""
    reason = body.notes if body else "Rejected by admin"
    try:
        approval_service.reject(
            request_id=request_id,
            admin_username=admin,
            reason=reason,
        )
        return {
            "status": "REJECTED",
            "request_id": request_id,
            "rejected_by": admin,
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


# -------------------------------------------------------------------
# Privacy Attack Lab Endpoint
# -------------------------------------------------------------------
class AttackSimRequest(BaseModel):
    attack_type: str = "credential_leak"
    payload_text: str


@router.post("/lab/simulate-attack")
def simulate_privacy_attack(body: AttackSimRequest):
    """Interactive Privacy Attack Lab: tests pattern interception, regex, and AST masking."""
    from app.protection.masking import redact_text_patterns
    import hashlib

    original = body.payload_text
    sanitized = redact_text_patterns(original)

    findings = []
    if "[REDACTED_SECRET]" in sanitized:
        findings.append("API Key / Plaintext Password Neutralized")
    if "[REDACTED_TOKEN]" in sanitized:
        findings.append("JWT / Bearer Token Redacted")
    if "[REDACTED_DB_CREDENTIAL]" in sanitized:
        findings.append("Database Connection String Scrubbed")
    if "[REDACTED_PRIVATE_KEY]" in sanitized:
        findings.append("RSA / SSH Private Key Blocked")
    if "[REDACTED_EMAIL]" in sanitized:
        findings.append("Customer PII Email Redacted")

    return {
        "status": "NEUTRALIZED" if findings else "CLEAN",
        "attack_type": body.attack_type,
        "original_payload": original,
        "sanitized_payload": sanitized,
        "findings_neutralized": findings,
        "secrets_leakage_prevented": len(findings) > 0,
        "egress_allowed": True,
        "digest": hashlib.sha256(sanitized.encode("utf-8")).hexdigest(),
    }
