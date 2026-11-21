"""Masking and Redaction Tokens and Replacers
Defines standard redaction tokens and replacement regex helpers.
"""

import re
from typing import Any, Dict
from app.detection.rules import (
    EMAIL_REGEX,
    BEARER_TOKEN_REGEX,
    JWT_REGEX,
    API_KEY_REGEX,
    DB_URI_REGEX,
    PRIVATE_KEY_REGEX,
    PASSWORD_KEY_REGEX,
)

REDACTION_EMAIL = "[REDACTED_EMAIL]"
REDACTION_SECRET = "[REDACTED_SECRET]"
REDACTION_TOKEN = "[REDACTED_TOKEN]"
REDACTION_DB_CREDENTIAL = "[REDACTED_DB_CREDENTIAL]"
REDACTION_PRIVATE_KEY = "[REDACTED_PRIVATE_KEY]"


PASSWORD_ASSIGNMENT_REGEX = re.compile(
    r"(?i)(?:password|passwd|pwd|passphrase|secret|client_secret|api_secret)[\s:=]+['\"]?([^\s'\"&,]+)['\"]?"
)


def redact_text_patterns(text: str) -> str:
    """Mask known sensitive patterns embedded in free text or log messages."""
    if not text or not isinstance(text, str):
        return text

    # Redact private keys
    text = PRIVATE_KEY_REGEX.sub(REDACTION_PRIVATE_KEY, text)

    # Redact database credentials in URIs
    text = DB_URI_REGEX.sub(lambda m: m.group(0).replace(m.group(1), REDACTION_DB_CREDENTIAL), text)

    # Redact JWT tokens
    text = JWT_REGEX.sub(REDACTION_TOKEN, text)

    # Redact Bearer tokens
    text = BEARER_TOKEN_REGEX.sub(f"Bearer {REDACTION_TOKEN}", text)

    # Redact API key patterns
    text = API_KEY_REGEX.sub(lambda m: m.group(0).replace(m.group(1), REDACTION_SECRET), text)

    # Redact inline password/secret assignments
    text = PASSWORD_ASSIGNMENT_REGEX.sub(lambda m: m.group(0).replace(m.group(1), REDACTION_SECRET), text)

    # Redact email addresses
    text = EMAIL_REGEX.sub(REDACTION_EMAIL, text)

    return text
