"""Incident Detection Schemas"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class IncidentSeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    RESOLVING = "RESOLVING"


class IncidentRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    incident_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(...)
    description: str = Field(...)
    severity: IncidentSeverityEnum = Field(...)
    status: IncidentStatusEnum = Field(default=IncidentStatusEnum.ACTIVE)
    scenario_type: str = Field(...)
    source_id: str = Field(...)
    service_name: str = Field(...)
    metric_name: Optional[str] = None
    observed_value: Optional[float] = None
    threshold_value: Optional[float] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolution_operation_id: Optional[str] = None
