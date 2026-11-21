"""Detection Rules Configuration and Registry
Defines pattern-based regexes and key-based sensitive matchers.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import List, Optional
from app.schemas.detection import SensitiveCategoryEnum


@dataclass
class DetectionRule:
    rule_id: str
    name: str
    category: SensitiveCategoryEnum
    pattern: Optional[re.Pattern] = None
    key_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.90
    description: str = ""


# Pre-compiled high-precision regular expressions
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE
)

BEARER_TOKEN_REGEX = re.compile(
    r"(?:Bearer|token)\s+([A-Za-z0-9\-\._~\+\/]{16,}=*)",
    re.IGNORECASE
)

JWT_REGEX = re.compile(
    r"\beyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b"
)

API_KEY_REGEX = re.compile(
    r"(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)[\s:=]+['\"]?([A-Za-z0-9_\-]{16,64})['\"]?"
)

DB_URI_REGEX = re.compile(
    r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|sqlite):\/\/[^:\s]+:([^@\s]+)@[^\s]+",
    re.IGNORECASE
)

PRIVATE_KEY_REGEX = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    re.IGNORECASE
)

PASSWORD_KEY_REGEX = re.compile(
    r"(?i)(password|passwd|pwd|passphrase|secret|client_secret|api_secret|api_key|apikey|access_key|auth_token|access_token|private_key)"
)


DEFAULT_DETECTION_RULES: List[DetectionRule] = [
    DetectionRule(
        rule_id="RULE-SECRET-KEY",
        name="Sensitive Key Name Matcher",
        category=SensitiveCategoryEnum.PASSWORD,
        key_patterns=["password", "passwd", "pwd", "secret", "client_secret", "api_secret"],
        confidence=0.95,
        description="Matched sensitive object key name",
    ),
    DetectionRule(
        rule_id="RULE-API-KEY",
        name="API Key Pattern Matcher",
        category=SensitiveCategoryEnum.API_KEY,
        pattern=API_KEY_REGEX,
        key_patterns=["api_key", "apikey", "access_key", "x-api-key"],
        confidence=0.90,
        description="Detected API Key assignment pattern or header",
    ),
    DetectionRule(
        rule_id="RULE-BEARER-TOKEN",
        name="Bearer Token Matcher",
        category=SensitiveCategoryEnum.ACCESS_TOKEN,
        pattern=BEARER_TOKEN_REGEX,
        confidence=0.92,
        description="Detected Authorization Bearer token header or string",
    ),
    DetectionRule(
        rule_id="RULE-JWT",
        name="JWT Token Pattern Matcher",
        category=SensitiveCategoryEnum.ACCESS_TOKEN,
        pattern=JWT_REGEX,
        confidence=0.98,
        description="Detected JSON Web Token format",
    ),
    DetectionRule(
        rule_id="RULE-EMAIL",
        name="Email Address Matcher",
        category=SensitiveCategoryEnum.EMAIL,
        pattern=EMAIL_REGEX,
        confidence=0.95,
        description="Detected email address format",
    ),
    DetectionRule(
        rule_id="RULE-DB-CREDENTIAL",
        name="Database Connection String Matcher",
        category=SensitiveCategoryEnum.DATABASE_CREDENTIAL,
        pattern=DB_URI_REGEX,
        confidence=0.99,
        description="Detected database credentials in URI string",
    ),
    DetectionRule(
        rule_id="RULE-PRIVATE-KEY",
        name="Private Key PEM Matcher",
        category=SensitiveCategoryEnum.SECRET_VALUE,
        pattern=PRIVATE_KEY_REGEX,
        confidence=1.00,
        description="Detected cryptographic private key block",
    ),
]
