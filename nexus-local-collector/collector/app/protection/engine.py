"""Data Protection Engine
Masks and redacts sensitive information, credentials, and PII across telemetry payloads.
Performs strict post-protection verification before marking payload as sanitized.
"""

from typing import Any, Dict, List, Tuple
from app.detection.engine import SensitiveDataDetector
from app.detection.rules import PASSWORD_KEY_REGEX
from app.protection.masking import (
    REDACTION_EMAIL,
    REDACTION_SECRET,
    REDACTION_TOKEN,
    REDACTION_DB_CREDENTIAL,
    REDACTION_PRIVATE_KEY,
    redact_text_patterns,
)
from app.schemas.telemetry import TelemetryPayload, LogEntry
from app.core.logging_config import get_logger

logger = get_logger("protection_engine")


class ProtectionVerificationError(Exception):
    """Raised when sensitive data remains in payload after protection pass."""
    pass


class DataProtectionEngine:
    """Applies redaction and masking to telemetry payloads."""

    def __init__(self, detector: SensitiveDataDetector = None):
        self.detector = detector or SensitiveDataDetector()

    def _sanitize_data(self, data: Any, current_key: str = "") -> Tuple[Any, Dict[str, int]]:
        """Recursively redact sensitive keys and values in nested dicts/lists."""
        counts = {
            "secrets_redacted": 0,
            "emails_masked": 0,
            "tokens_redacted": 0,
            "keys_redacted": 0,
        }

        # Check if the key itself designates a sensitive field (password, secret, token)
        if current_key and PASSWORD_KEY_REGEX.search(current_key):
            counts["secrets_redacted"] += 1
            counts["keys_redacted"] += 1
            return REDACTION_SECRET, counts

        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                sanitized_val, sub_counts = self._sanitize_data(v, current_key=k)
                cleaned[k] = sanitized_val
                for ck in counts:
                    counts[ck] += sub_counts[ck]
            return cleaned, counts

        elif isinstance(data, list):
            cleaned_list = []
            for item in data:
                sanitized_val, sub_counts = self._sanitize_data(item, current_key=current_key)
                cleaned_list.append(sanitized_val)
                for ck in counts:
                    counts[ck] += sub_counts[ck]
            return cleaned_list, counts

        elif isinstance(data, str):
            orig_data = data
            redacted_str = redact_text_patterns(data)
            if REDACTION_EMAIL in redacted_str and REDACTION_EMAIL not in orig_data:
                counts["emails_masked"] += 1
            if REDACTION_SECRET in redacted_str and REDACTION_SECRET not in orig_data:
                counts["secrets_redacted"] += 1
            if REDACTION_TOKEN in redacted_str and REDACTION_TOKEN not in orig_data:
                counts["tokens_redacted"] += 1
            return redacted_str, counts

        return data, counts

    def protect_payload(self, payload: TelemetryPayload) -> TelemetryPayload:
        """Sanitize payload and verify that no sensitive data remains."""
        total_counts = {
            "secrets_redacted": 0,
            "emails_masked": 0,
            "tokens_redacted": 0,
            "keys_redacted": 0,
        }

        # 1. Protect Logs
        sanitized_logs: List[LogEntry] = []
        for log in payload.logs:
            clean_msg, msg_counts = self._sanitize_data(log.message)
            clean_attrs, attr_counts = self._sanitize_data(log.attributes)
            for k in total_counts:
                total_counts[k] += msg_counts[k] + attr_counts[k]

            sanitized_logs.append(
                LogEntry(
                    timestamp=log.timestamp,
                    level=log.level,
                    message=clean_msg,
                    service=log.service,
                    event_type=log.event_type,
                    attributes=clean_attrs,
                )
            )

        # 2. Protect Application Raw Metrics if present
        app_metrics = payload.application_metrics
        if app_metrics and app_metrics.raw_metrics:
            clean_raw, raw_counts = self._sanitize_data(app_metrics.raw_metrics)
            for k in total_counts:
                total_counts[k] += raw_counts[k]
            app_metrics = app_metrics.model_copy(update={"raw_metrics": clean_raw})

        # 3. Protect Metadata
        clean_meta, meta_counts = self._sanitize_data(payload.metadata)
        for k in total_counts:
            total_counts[k] += meta_counts[k]

        total_modifications = sum(total_counts.values())
        sanitization_summary = {
            **total_counts,
            "total_fields_modified": total_modifications,
            "protection_verified": True,
        }

        sanitized_payload = payload.model_copy(
            update={
                "logs": sanitized_logs,
                "application_metrics": app_metrics,
                "metadata": clean_meta,
                "is_sanitized": True,
                "sanitization_summary": sanitization_summary,
            }
        )

        # 4. Protection Verification Check
        verification_result = self.detector.scan_payload(sanitized_payload)
        # Note: REDACTION tokens are benign placeholders; any finding matching a non-redacted secret is an error.
        tokens = [
            REDACTION_EMAIL,
            REDACTION_SECRET,
            REDACTION_TOKEN,
            REDACTION_DB_CREDENTIAL,
            REDACTION_PRIVATE_KEY,
        ]
        remaining_unredacted = [
            f for f in verification_result.findings
            if not (
                (f.masked_sample and f.masked_sample.startswith("[REDACTED_"))
                or any(t in (f.masked_sample or "") for t in tokens)
            )
        ]

        if remaining_unredacted:
            logger.error(
                f"Protection verification failed for {payload.payload_id}: "
                f"{len(remaining_unredacted)} unredacted findings remain!"
            )
            raise ProtectionVerificationError(
                f"Protection verification failed: {len(remaining_unredacted)} sensitive items remaining"
            )

        logger.info(
            f"Protection complete for payload {payload.payload_id}: "
            f"modified={total_modifications}, verified=True"
        )
        return sanitized_payload
