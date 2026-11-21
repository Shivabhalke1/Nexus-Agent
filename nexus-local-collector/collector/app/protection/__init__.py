"""Protection Package Exports"""

from app.protection.masking import (
    REDACTION_EMAIL,
    REDACTION_SECRET,
    REDACTION_TOKEN,
    REDACTION_DB_CREDENTIAL,
    REDACTION_PRIVATE_KEY,
    redact_text_patterns,
)
from app.protection.engine import (
    DataProtectionEngine,
    ProtectionVerificationError,
)

__all__ = [
    "REDACTION_EMAIL",
    "REDACTION_SECRET",
    "REDACTION_TOKEN",
    "REDACTION_DB_CREDENTIAL",
    "REDACTION_PRIVATE_KEY",
    "redact_text_patterns",
    "DataProtectionEngine",
    "ProtectionVerificationError",
]
