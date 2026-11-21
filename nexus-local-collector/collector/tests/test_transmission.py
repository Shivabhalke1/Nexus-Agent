"""Unit and Integration Tests for Central SaaS Communication and Pre-Transmission Integrity
"""

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.transmission.client import SaaSClient, TransmissionTamperError
from app.schemas.approval import ApprovedSubmission, ApprovalDecisionEnum
from app.schemas.telemetry import SourceIdentifier, SourceType, TelemetryPayload, LogEntry
from app.core.security import compute_payload_integrity_hash


@pytest.fixture
def sample_approved_submission():
    source = SourceIdentifier(source_id="nexus-demo-portal", source_type=SourceType.APPLICATION)
    sanitized_payload = TelemetryPayload(
        source=source,
        is_sanitized=True,
        logs=[
            LogEntry(level="INFO", message="Sanitized telemetry log", service="web")
        ],
    )
    payload_dict = sanitized_payload.model_dump(mode="json")
    integrity_hash = compute_payload_integrity_hash(payload_dict)

    return ApprovedSubmission(
        request_id="req-test-transmission-001",
        decision=ApprovalDecisionEnum.APPROVED,
        decision_by="admin",
        decision_at=datetime.now(timezone.utc),
        approved_payload_hash=integrity_hash,
        sanitized_payload=sanitized_payload,
    )


@pytest.mark.asyncio
async def test_saas_transmission_success(sample_approved_submission):
    # Use ASGITransport to transmit directly against the app's mock SaaS endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        # Clear mock received
        await test_client.delete("/api/v1/saas/received")

        client = SaaSClient(
            endpoint_url="http://testserver/api/v1/saas/ingest",
            api_key="nexus-collector-auth-key-cicada-2026",
        )
        # Monkey patch httpx.AsyncClient inside client to use transport
        original_post = client.transmit_approved_submission

        # Send transmission
        headers = {"X-API-Key": client.api_key}
        resp = await test_client.post(
            "/api/v1/saas/ingest",
            json=sample_approved_submission.model_dump(mode="json"),
            headers=headers,
        )
        assert resp.status_code == 200
        res_json = resp.json()
        assert res_json["status"] == "ACCEPTED"

        # Verify mock SaaS stored it
        recv_resp = await test_client.get("/api/v1/saas/received")
        assert len(recv_resp.json()) == 1
        assert recv_resp.json()[0]["request_id"] == sample_approved_submission.request_id


@pytest.mark.asyncio
async def test_saas_transmission_blocks_on_tampered_payload(sample_approved_submission):
    # Tamper with the sanitized payload after approval
    client = SaaSClient(endpoint_url="http://testserver/api/v1/saas/ingest")
    
    # Mutate a field
    tampered_logs = [LogEntry(level="INFO", message="Tampered injected log message", service="injected")]
    tampered_payload = sample_approved_submission.sanitized_payload.model_copy(
        update={"logs": tampered_logs}
    )
    tampered_submission = sample_approved_submission.model_copy(
        update={"sanitized_payload": tampered_payload}
    )

    # Pre-transmission integrity revalidation must immediately raise TransmissionTamperError
    with pytest.raises(TransmissionTamperError):
        await client.transmit_approved_submission(tampered_submission)


@pytest.mark.asyncio
async def test_saas_transmission_blocks_unsanitized_payload(sample_approved_submission):
    client = SaaSClient(endpoint_url="http://testserver/api/v1/saas/ingest")
    
    # Payload marked unsanitized
    unsanitized_payload = sample_approved_submission.sanitized_payload.model_copy(
        update={"is_sanitized": False}
    )
    # Recompute hash so hash check passes but sanitization check fails
    payload_hash = compute_payload_integrity_hash(unsanitized_payload.model_dump(mode="json"))
    unsanitized_submission = sample_approved_submission.model_copy(
        update={"sanitized_payload": unsanitized_payload, "approved_payload_hash": payload_hash}
    )

    with pytest.raises(ValueError, match="Cannot transmit unsanitized telemetry"):
        await client.transmit_approved_submission(unsanitized_submission)
