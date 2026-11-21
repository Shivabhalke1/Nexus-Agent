"""Structured JSON logging configuration with privacy sanitization."""
import json
import logging
import re
from typing import Any, Dict

SENSITIVE_KEYS = {"password", "secret", "token", "access_token", "authorization", "cookie", "api_key", "credential"}
BEARER_PATTERN = re.compile(r"Bearer\s+([A-Za-z0-9\-\._~\+\/]+=*)", re.IGNORECASE)


def sanitize_value(key: str, value: Any) -> Any:
    """Mask any sensitive values from appearing in local application logs."""
    if any(k in key.lower() for k in SENSITIVE_KEYS):
        return "[REDACTED]"
    if isinstance(value, str):
        value = BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    return value


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively clean dictionaries."""
    sanitized = {}
    for k, v in data.items():
        if isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_dict(it) if isinstance(it, dict) else sanitize_value(k, it) for it in v]
        else:
            sanitized[k] = sanitize_value(k, v)
    return sanitized


class CollectorJsonFormatter(logging.Formatter):
    """Custom log formatter ensuring parseable JSON and zero credential leakage."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "collector_id": "collector-demo-001",
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "stage"):
            log_obj["stage"] = getattr(record, "stage")
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if hasattr(record, "status_code"):
            log_obj["status_code"] = getattr(record, "status_code")

        return json.dumps(sanitize_dict(log_obj))


def get_logger(name: str = "collector") -> logging.Logger:
    """Return a configured logger with CollectorJsonFormatter."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(CollectorJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

