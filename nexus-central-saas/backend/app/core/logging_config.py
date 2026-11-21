"""Structured JSON logging configuration for NEXUS Central SaaS"""

import json
import logging
import sys

SENSITIVE_KEYS = {"password", "secret", "token", "access_token", "authorization", "api_key", "cookie"}


class SaasJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON without credential leakage."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "nexus-central-saas",
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_obj)


def get_logger(name: str = "central_saas") -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(SaasJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
