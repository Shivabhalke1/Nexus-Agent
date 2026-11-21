"""Sensitive Data Detection Schema Definitions
NEXUS Local Collector - Pydantic v2 Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class SensitiveCategoryEnum(str, Enum):
    PASSWORD = "PASSWORD"
    API_KEY = "API_KEY"
    ACCESS_TOKEN = "ACCESS_TOKEN"
    AUTH_HEADER = "AUTH_HEADER"
    EMAIL = "EMAIL"
    DATABASE_CREDENTIAL = "DATABASE_CREDENTIAL"
    SECRET_VALUE = "SECRET_VALUE"
    PII = "PII"
    PRIVATE_INFO = "PRIVATE_INFO"


class SensitiveDataFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID for this finding")
    category: SensitiveCategoryEnum = Field(..., description="Category of sensitive data detected")
    field_path: str = Field(..., description="Path/location within the payload, e.g. logs[0].attributes.token")
    rule_name: str = Field(..., description="Name of detection rule that triggered")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    description: str = Field(..., description="Safe description of what was detected (NO raw secrets)")
    masked_sample: Optional[str] = Field(default=None, description="Safely masked sample preview (never raw secret)")


class DetectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload_id: str = Field(..., description="ID of the scanned payload")
    has_sensitive_data: bool = Field(..., description="True if any sensitive findings were detected")
    findings_count: int = Field(default=0, ge=0, description="Count of findings")
    findings: List[SensitiveDataFinding] = Field(default_factory=list, description="List of sensitive findings")
    scan_duration_ms: float = Field(default=0.0, ge=0.0, description="Time taken to scan in milliseconds")
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
