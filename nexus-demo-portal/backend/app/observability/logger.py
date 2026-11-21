"""Privacy-compliant structured logging formatting and sanitization."""
import json
import logging
import re
from typing import Any, Dict

# Patterns for sensitive data sanitization
SENSITIVE_KEYS = {"password", "secret", "token", "access_token", "authorization", "cookie", "card_number", "cvv"}
BEARER_PATTERN = re.compile(r"Bearer\s+([A-Za-z0-9\-\._~\+\/]+=*)", re.IGNORECASE)


def sanitize_value(key: str, value: Any) -> Any:
    """Mask sensitive values to prevent credential leakage into telemetry."""
    if any(k in key.lower() for k in SENSITIVE_KEYS):
        return "[REDACTED]"
    if isinstance(value, str):
        value = BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    return value


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize dictionary keys and values."""
    sanitized = {}
    for k, v in data.items():
        if isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_dict(item) if isinstance(item, dict) else sanitize_value(k, item) for item in v]
        else:
            sanitized[k] = sanitize_value(k, v)
    return sanitized


class StructuredJsonFormatter(logging.Formatter):
    """Custom logging formatter outputting clean, parseable JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Inject extra attributes if present
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if hasattr(record, "endpoint"):
            log_obj["endpoint"] = getattr(record, "endpoint")
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = getattr(record, "duration_ms")
        if hasattr(record, "status_code"):
            log_obj["status_code"] = getattr(record, "status_code")

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(sanitize_dict(log_obj))
