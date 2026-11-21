"""Policy Validation Engine
Evaluates telemetry payloads against privacy, security, and integrity rules.
Enforces hard blocking to prevent non-compliant data from reaching Human Approval.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from app.detection.engine import SensitiveDataDetector
from app.policies.rules import PolicyConfig, DEFAULT_POLICY_CONFIG
from app.schemas.policy import (
    PolicyValidationResult,
    PolicyViolation,
    ViolationSeverityEnum,
)
from app.schemas.telemetry import TelemetryPayload
from app.protection.masking import (
    REDACTION_EMAIL,
    REDACTION_SECRET,
    REDACTION_TOKEN,
    REDACTION_DB_CREDENTIAL,
    REDACTION_PRIVATE_KEY,
)
from app.core.logging_config import get_logger

logger = get_logger("policy_validator")


class PolicyValidator:
    """Validates outgoing payloads against strict compliance and privacy rules."""

    def __init__(
        self,
        config: Optional[PolicyConfig] = None,
        detector: Optional[SensitiveDataDetector] = None,
    ):
        self.config = config or DEFAULT_POLICY_CONFIG
        self.detector = detector or SensitiveDataDetector()

    def _check_prohibited_fields(
        self, data: Any, current_path: str, violations: List[PolicyViolation]
    ) -> None:
        """Inspect data tree for prohibited field names."""
        if isinstance(data, dict):
            for k, v in data.items():
                child_path = f"{current_path}.{k}" if current_path else k
                lower_k = str(k).lower()
                if lower_k in self.config.prohibited_fields:
                    violations.append(
                        PolicyViolation(
                            rule_id="POL-PROHIBITED-FIELD",
                            rule_name="Prohibited Field Check",
                            severity=ViolationSeverityEnum.BLOCK,
                            message=f"Payload contains prohibited field '{k}' at path '{child_path}'",
                            field_path=child_path,
                            details={"prohibited_field": k},
                        )
                    )
                self._check_prohibited_fields(v, child_path, violations)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                child_path = f"{current_path}[{idx}]"
                self._check_prohibited_fields(item, child_path, violations)

    def validate_payload(self, payload: TelemetryPayload) -> PolicyValidationResult:
        """Execute full policy validation pass on a TelemetryPayload."""
        violations: List[PolicyViolation] = []
        payload_dict = payload.model_dump(mode="json")
        serialized_json = json.dumps(payload_dict)
        size_bytes = len(serialized_json.encode("utf-8"))

        # -------------------------------------------------------------
        # Rule 1: Structural Integrity and Required Fields
        # -------------------------------------------------------------
        if not payload.payload_id:
            violations.append(
                PolicyViolation(
                    rule_id="POL-REQ-PAYLOAD-ID",
                    rule_name="Required Payload ID",
                    severity=ViolationSeverityEnum.BLOCK,
                    message="Missing mandatory payload_id",
                )
            )

        if not payload.source or not payload.source.source_id:
            violations.append(
                PolicyViolation(
                    rule_id="POL-REQ-SOURCE-ID",
                    rule_name="Required Source Identifier",
                    severity=ViolationSeverityEnum.BLOCK,
                    message="Missing mandatory source.source_id",
                )
            )

        # -------------------------------------------------------------
        # Rule 2: Mandatory Sanitization Enforcement
        # -------------------------------------------------------------
        if self.config.require_sanitization and not payload.is_sanitized:
            violations.append(
                PolicyViolation(
                    rule_id="POL-SANITIZATION-REQUIRED",
                    rule_name="Sanitization Required",
                    severity=ViolationSeverityEnum.BLOCK,
                    message="Payload is not marked as sanitized (is_sanitized=False). Must pass Data Protection pass before transmission.",
                )
            )

        # -------------------------------------------------------------
        # Rule 3: Zero Unredacted Sensitive Data Check
        # -------------------------------------------------------------
        detection_res = self.detector.scan_payload(payload)
        tokens = [
            REDACTION_EMAIL,
            REDACTION_SECRET,
            REDACTION_TOKEN,
            REDACTION_DB_CREDENTIAL,
            REDACTION_PRIVATE_KEY,
        ]
        unredacted_findings = [
            f for f in detection_res.findings
            if not (
                (f.masked_sample and f.masked_sample.startswith("[REDACTED_"))
                or any(t in (f.masked_sample or "") for t in tokens)
            )
        ]

        if unredacted_findings:
            for finding in unredacted_findings:
                violations.append(
                    PolicyViolation(
                        rule_id="POL-SENSITIVE-DATA-BLOCKED",
                        rule_name="Unredacted Sensitive Data Disallowed",
                        severity=ViolationSeverityEnum.BLOCK,
                        message=f"Unredacted sensitive data detected in {finding.field_path}: {finding.description}",
                        field_path=finding.field_path,
                        details={"category": finding.category.value, "rule_name": finding.rule_name},
                    )
                )

        # -------------------------------------------------------------
        # Rule 4: Prohibited Fields Check
        # -------------------------------------------------------------
        if self.config.disallow_prohibited_fields:
            self._check_prohibited_fields(payload_dict, "", violations)

        # -------------------------------------------------------------
        # Rule 5: Payload Size Limits
        # -------------------------------------------------------------
        if size_bytes > self.config.max_payload_size_bytes:
            violations.append(
                PolicyViolation(
                    rule_id="POL-PAYLOAD-SIZE-LIMIT",
                    rule_name="Payload Size Limit Exceeded",
                    severity=ViolationSeverityEnum.BLOCK,
                    message=f"Payload size {size_bytes} bytes exceeds configured limit of {self.config.max_payload_size_bytes} bytes",
                    details={"size_bytes": size_bytes, "limit_bytes": self.config.max_payload_size_bytes},
                )
            )

        # -------------------------------------------------------------
        # Rule 6: Batch Log Limits (Advisory Warning or Block)
        # -------------------------------------------------------------
        if len(payload.logs) > self.config.max_logs_count:
            violations.append(
                PolicyViolation(
                    rule_id="POL-LOG-COUNT-LIMIT",
                    rule_name="Log Count Exceeded",
                    severity=ViolationSeverityEnum.WARN,
                    message=f"Payload contains {len(payload.logs)} logs (recommended max: {self.config.max_logs_count})",
                    details={"count": len(payload.logs), "recommended_max": self.config.max_logs_count},
                )
            )

        # -------------------------------------------------------------
        # Compliance Decision
        # -------------------------------------------------------------
        has_blocking = any(v.severity == ViolationSeverityEnum.BLOCK for v in violations)
        is_compliant = not has_blocking
        can_be_approved = is_compliant  # Strictly False if any BLOCK exists

        logger.info(
            f"Policy validation for {payload.payload_id}: "
            f"is_compliant={is_compliant}, can_be_approved={can_be_approved}, "
            f"violations_count={len(violations)}"
        )

        return PolicyValidationResult(
            payload_id=payload.payload_id,
            is_compliant=is_compliant,
            can_be_approved=can_be_approved,
            violations=violations,
            validated_at=datetime.now(timezone.utc),
            policy_version="1.0.0",
        )
