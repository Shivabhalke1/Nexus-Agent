"""Outbound Transmission Client for NEXUS Central SaaS
Re-validates cryptographic integrity immediately prior to transmission.
"""

from typing import Any, Dict, Optional
import httpx
from app.schemas.approval import ApprovedSubmission
from app.core.config import settings
from app.core.security import compute_payload_integrity_hash
from app.core.logging_config import get_logger

logger = get_logger("saas_client")


class TransmissionTamperError(Exception):
    """Raised when pre-transmission integrity revalidation fails."""
    pass


class SaaSClient:
    """Dispatches approved, sanitized telemetry payloads to Central SaaS."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 5.0,
    ):
        raw_url = endpoint_url or settings.CENTRAL_SAAS_URL
        if raw_url and "://localhost" in raw_url:
            raw_url = raw_url.replace("://localhost", "://127.0.0.1")
        self.endpoint_url = raw_url
        self.api_key = api_key or settings.CENTRAL_SAAS_API_KEY
        self.timeout_seconds = timeout_seconds

    async def transmit_approved_submission(
        self, submission: ApprovedSubmission
    ) -> Dict[str, Any]:
        """Re-validate integrity hash and dispatch telemetry to Central SaaS."""
        # 1. MANDATORY PRE-TRANSMISSION REVALIDATION
        current_dict = submission.sanitized_payload.model_dump(mode="json")
        revalidated_hash = compute_payload_integrity_hash(current_dict)

        if revalidated_hash != submission.approved_payload_hash:
            logger.critical(
                f"PRE-TRANSMISSION INTEGRITY FAILURE for request {submission.request_id}! "
                f"Approved hash: {submission.approved_payload_hash}, "
                f"Current payload hash: {revalidated_hash}. ABORTING TRANSMISSION."
            )
            raise TransmissionTamperError(
                f"Pre-transmission integrity mismatch: payload was mutated post-approval!"
            )

        # 2. Check sanitization flag
        if not submission.sanitized_payload.is_sanitized:
            logger.critical(f"ABORT: Attempted to transmit unsanitized payload {submission.sanitized_payload.payload_id}")
            raise ValueError("Cannot transmit unsanitized telemetry")

        # 3. Dispatch to SaaS
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": f"NEXUS-Local-Collector/{settings.COLLECTOR_VERSION}",
        }

        payload_json = submission.model_dump(mode="json")

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(
                self.endpoint_url,
                json=payload_json,
                headers=headers,
            )

            if resp.status_code in (200, 201, 202):
                logger.info(
                    f"Successfully transmitted approved telemetry {submission.request_id} to {self.endpoint_url}"
                )
                return resp.json()
            else:
                logger.error(
                    f"SaaS ingestion rejected transmission {submission.request_id} "
                    f"with HTTP status {resp.status_code}: {resp.text}"
                )
                raise RuntimeError(
                    f"SaaS transmission failed: HTTP {resp.status_code} - {resp.text}"
                )
