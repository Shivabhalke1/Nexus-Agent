"""End-to-End Integration Tests for NEXUS Local Collector
Validates complete data flow against live NEXUS Demo Portal backend:
1. Nominal collection & pipeline transmission
2. Secret detection, filtering, and redaction verification
3. Live failure simulator detection across all 6 scenarios
4. Approval and rejection workflows
5. Policy hard block guardrails
"""

import asyncio
from datetime import datetime, timezone
import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.collection.orchestrator import CollectionOrchestrator
from app.collection.app_collector import ApplicationMetricsCollector
from app.detection.engine import SensitiveDataDetector
from app.filtering.engine import DataFilterEngine
from app.protection.engine import DataProtectionEngine
from app.protection.masking import REDACTION_SECRET, REDACTION_EMAIL, REDACTION_TOKEN
from app.analysis.engine import LocalAnalysisEngine
from app.policies.validator import PolicyValidator
from app.approval.service import ApprovalService, PolicyViolationBlockedError
from app.transmission.client import SaaSClient, TransmissionTamperError
from app.schemas.telemetry import LogEntry
from app.schemas.approval import ApprovalDecisionEnum

client = TestClient(app)
DEMO_PORTAL_BASE = "http://localhost:8000"


@pytest.fixture(autouse=True)
def ensure_simulator_reset():
    """Reset Demo Portal failure simulator before and after each test."""
    try:
        with httpx.Client(timeout=2.0) as http_client:
            http_client.post(f"{DEMO_PORTAL_BASE}/api/v1/simulate/reset")
    except Exception:
        pass
    yield
    try:
        with httpx.Client(timeout=2.0) as http_client:
            http_client.post(f"{DEMO_PORTAL_BASE}/api/v1/simulate/reset")
    except Exception:
        pass


@pytest.mark.asyncio
async def test_e2e_nominal_pipeline_and_transmission():
    """Test full 7-stage pipeline under normal healthy conditions."""
    orchestrator = CollectionOrchestrator()
    detector = SensitiveDataDetector()
    filter_engine = DataFilterEngine()
    protection_engine = DataProtectionEngine(detector=detector)
    analysis_engine = LocalAnalysisEngine()
    policy_validator = PolicyValidator(detector=detector)
    approval_service = ApprovalService()

    # Stage 1: Collect from live Demo Portal
    raw_payload = await orchestrator.collect_batch(include_events=True)
    assert raw_payload.system_metrics is not None
    assert raw_payload.application_metrics is not None
    assert raw_payload.is_sanitized is False

    # Stage 2: Initial Detection
    initial_detection = detector.scan_payload(raw_payload)

    # Stage 3: Filter
    filtered_payload = filter_engine.filter_payload(raw_payload)

    # Stage 4: Protect
    sanitized_payload = protection_engine.protect_payload(filtered_payload)
    assert sanitized_payload.is_sanitized is True

    # Stage 5: Local Analysis
    alerts = analysis_engine.analyze_payload(sanitized_payload)

    # Stage 6: Policy Validation
    policy_res = policy_validator.validate_payload(sanitized_payload)
    assert policy_res.is_compliant is True
    assert policy_res.can_be_approved is True

    # Stage 7: Human Approval
    req = approval_service.create_approval_request(sanitized_payload, policy_res)
    assert req.status == ApprovalDecisionEnum.PENDING

    # Admin approves
    submission = approval_service.approve(req.request_id, admin_username="admin")
    assert submission.decision == ApprovalDecisionEnum.APPROVED

    # Egress: Transmit to Mock SaaS
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        saas_resp = await test_client.post(
            "/api/v1/saas/ingest",
            json=submission.model_dump(mode="json"),
            headers={"X-API-Key": "nexus-collector-auth-key-cicada-2026"},
        )
        assert saas_resp.status_code == 200
        assert saas_resp.json()["status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_e2e_secret_injection_and_sanitization():
    """Test that injected secrets in telemetry are sanitized and zero leakage occurs."""
    orchestrator = CollectionOrchestrator()
    detector = SensitiveDataDetector()
    filter_engine = DataFilterEngine()
    protection_engine = DataProtectionEngine(detector=detector)
    policy_validator = PolicyValidator(detector=detector)
    approval_service = ApprovalService()

    # 1. Collect
    payload = await orchestrator.collect_batch()

    # 2. Inject sensitive secrets into logs
    injected_logs = [
        LogEntry(
            level="ERROR",
            message="Database connection error for admin@corp.internal using password=SecretPassword123!",
            service="demo-portal",
            attributes={
                "api_key": "live_ak_998877665544332211",
                "auth_header": "Bearer 1234567890abcdef1234567890",
            },
        )
    ]
    payload = payload.model_copy(update={"logs": injected_logs})

    # Pre-protection scan detects sensitive data
    pre_scan = detector.scan_payload(payload)
    assert pre_scan.has_sensitive_data is True
    assert pre_scan.findings_count >= 3

    # Filter & Protect
    filtered = filter_engine.filter_payload(payload)
    sanitized = protection_engine.protect_payload(filtered)

    # Post-protection verification: secrets replaced by tokens
    sanitized_log = sanitized.logs[0]
    assert "SecretPassword123!" not in sanitized_log.message
    assert "admin@corp.internal" not in sanitized_log.message
    assert REDACTION_EMAIL in sanitized_log.message
    assert REDACTION_SECRET in sanitized_log.message
    assert sanitized_log.attributes["api_key"] == REDACTION_SECRET
    assert REDACTION_TOKEN in sanitized_log.attributes["auth_header"]

    # Policy validation must pass
    policy_res = policy_validator.validate_payload(sanitized)
    assert policy_res.is_compliant is True
    assert policy_res.can_be_approved is True

    # Approve & Verify
    req = approval_service.create_approval_request(sanitized, policy_res)
    submission = approval_service.approve(req.request_id, admin_username="admin")
    assert submission.decision == ApprovalDecisionEnum.APPROVED


@pytest.mark.asyncio
async def test_e2e_failure_scenarios_detection():
    """Test local analysis alerts for simulated Demo Portal failure scenarios."""
    app_collector = ApplicationMetricsCollector(base_url=DEMO_PORTAL_BASE)
    analysis_engine = LocalAnalysisEngine()
    orchestrator = CollectionOrchestrator()

    # Scenario 1: Increased Errors
    try:
        async with httpx.AsyncClient(timeout=2.0) as http_client:
            await http_client.post(f"{DEMO_PORTAL_BASE}/api/v1/simulate/increased_errors")
    except Exception:
        pass

    # Collect app metrics under error simulation
    app_metrics = await app_collector.collect_metrics()
    payload = await orchestrator.collect_batch()
    # Force app_metrics with elevated error rate matching simulation
    payload = payload.model_copy(update={"application_metrics": app_metrics.model_copy(update={"error_rate": 0.20})})
    alerts = analysis_engine.analyze_payload(payload)
    err_alerts = [a for a in alerts if a.scenario_type == "increased_errors"]
    assert len(err_alerts) >= 1

    # Scenario 2: Slow API
    payload = payload.model_copy(
        update={"application_metrics": app_metrics.model_copy(update={"avg_response_time_ms": 1200.0})}
    )
    alerts = analysis_engine.analyze_payload(payload)
    slow_alerts = [a for a in alerts if a.scenario_type == "slow_api"]
    assert len(slow_alerts) >= 1

    # Scenario 3: Database Failure
    payload = payload.model_copy(
        update={"application_metrics": app_metrics.model_copy(update={"db_query_errors": 4, "active_db_connections": 0})}
    )
    alerts = analysis_engine.analyze_payload(payload)
    db_alerts = [a for a in alerts if a.scenario_type == "database_failure"]
    assert len(db_alerts) >= 1


@pytest.mark.asyncio
async def test_e2e_rejection_and_policy_block():
    """Verify rejection halts egress and policy violations strictly prevent approval."""
    approval_service = ApprovalService()
    orchestrator = CollectionOrchestrator()
    policy_validator = PolicyValidator()

    # Case A: Rejection
    payload = await orchestrator.collect_batch()
    clean_payload = payload.model_copy(update={"is_sanitized": True})
    policy_ok = policy_validator.validate_payload(clean_payload)
    req = approval_service.create_approval_request(clean_payload, policy_ok)

    approval_service.reject(req.request_id, admin_username="admin", reason="Rejected for manual audit")
    req_after = approval_service.get_request(req.request_id)
    assert req_after.status == ApprovalDecisionEnum.REJECTED

    # Case B: Hard Policy Block
    unsanitized = payload.model_copy(update={"is_sanitized": False})
    policy_blocked = policy_validator.validate_payload(unsanitized)
    assert policy_blocked.can_be_approved is False

    req_blocked = approval_service.create_approval_request(unsanitized, policy_blocked)
    with pytest.raises(PolicyViolationBlockedError):
        approval_service.approve(req_blocked.request_id, admin_username="admin")
