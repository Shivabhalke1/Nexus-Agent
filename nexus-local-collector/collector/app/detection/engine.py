"""Sensitive Data Detection Engine
Traverses nested JSON structures and text logs to identify credentials,
secrets, PII, and sensitive keys without exposing raw values.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
from app.detection.rules import DEFAULT_DETECTION_RULES, DetectionRule, PASSWORD_KEY_REGEX
from app.schemas.detection import (
    DetectionResult,
    SensitiveCategoryEnum,
    SensitiveDataFinding,
)
from app.schemas.telemetry import TelemetryPayload
from app.core.logging_config import get_logger

logger = get_logger("detection_engine")


def mask_sample_safely(raw_str: str, max_chars: int = 16) -> str:
    """Generate a safe masked preview for audit without exposing the secret."""
    if not raw_str:
        return "[EMPTY]"
    if raw_str.startswith("[REDACTED_") and raw_str.endswith("]"):
        return raw_str
    length = len(raw_str)
    if length <= 4:
        return "****"
    if length <= 8:
        return f"{raw_str[:1]}***{raw_str[-1:]}"
    return f"{raw_str[:2]}***[REDACTED_LEN_{length}]***{raw_str[-2:]}"


class SensitiveDataDetector:
    """Detection engine for telemetry payloads and nested JSON trees."""

    def __init__(self, rules: Optional[List[DetectionRule]] = None):
        self.rules = rules or DEFAULT_DETECTION_RULES

    def scan_text(self, text: str, field_path: str) -> List[SensitiveDataFinding]:
        """Scan a string against all pattern-based rules."""
        findings: List[SensitiveDataFinding] = []
        if not text or not isinstance(text, str):
            return findings

        for rule in self.rules:
            if rule.pattern:
                matches = list(rule.pattern.finditer(text))
                for match in matches:
                    matched_group = match.group(0)
                    findings.append(
                        SensitiveDataFinding(
                            category=rule.category,
                            field_path=field_path,
                            rule_name=rule.name,
                            confidence=rule.confidence,
                            description=rule.description or f"Matched pattern for {rule.category.value}",
                            masked_sample=mask_sample_safely(matched_group),
                        )
                    )
        return findings

    def _traverse_data(
        self, data: Any, current_path: str, findings: List[SensitiveDataFinding]
    ) -> None:
        """Recursive crawler that traverses nested dicts and lists."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "sanitization_summary":
                    continue
                child_path = f"{current_path}.{key}" if current_path else key
                lower_key = str(key).lower()

                # 1. Structural Key Name Inspection
                for rule in self.rules:
                    if rule.key_patterns and any(kp in lower_key for kp in rule.key_patterns):
                        val_str = str(value) if value is not None else ""
                        findings.append(
                            SensitiveDataFinding(
                                category=rule.category,
                                field_path=child_path,
                                rule_name=rule.name,
                                confidence=rule.confidence,
                                description=f"Sensitive object key: '{key}'",
                                masked_sample=mask_sample_safely(val_str),
                            )
                        )
                        break

                # 2. Recurse down children
                self._traverse_data(value, child_path, findings)

        elif isinstance(data, list):
            for idx, item in enumerate(data):
                child_path = f"{current_path}[{idx}]"
                self._traverse_data(item, child_path, findings)

        elif isinstance(data, str):
            # Scan text contents for embedded patterns
            text_findings = self.scan_text(data, current_path)
            findings.extend(text_findings)

    def scan_payload(self, payload: TelemetryPayload) -> DetectionResult:
        """Scan a full TelemetryPayload object."""
        start_time = time.perf_counter()
        findings: List[SensitiveDataFinding] = []

        # Convert payload to dictionary for uniform structural scanning
        payload_dict = payload.model_dump(mode="json")
        self._traverse_data(payload_dict, "", findings)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Deduplicate findings by field_path and category
        unique_findings: List[SensitiveDataFinding] = []
        seen = set()
        for f in findings:
            key = (f.field_path, f.category)
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        logger.info(
            f"Detection scan completed: payload_id={payload.payload_id}, "
            f"findings={len(unique_findings)}, duration_ms={duration_ms:.2f}"
        )

        return DetectionResult(
            payload_id=payload.payload_id,
            has_sensitive_data=len(unique_findings) > 0,
            findings_count=len(unique_findings),
            findings=unique_findings,
            scan_duration_ms=duration_ms,
            scanned_at=datetime.now(timezone.utc),
        )

    def scan_dict(self, data: Dict[str, Any], payload_id: str = "custom") -> DetectionResult:
        """Scan an arbitrary nested dict."""
        start_time = time.perf_counter()
        findings: List[SensitiveDataFinding] = []

        self._traverse_data(data, "", findings)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return DetectionResult(
            payload_id=payload_id,
            has_sensitive_data=len(findings) > 0,
            findings_count=len(findings),
            findings=findings,
            scan_duration_ms=duration_ms,
            scanned_at=datetime.now(timezone.utc),
        )
