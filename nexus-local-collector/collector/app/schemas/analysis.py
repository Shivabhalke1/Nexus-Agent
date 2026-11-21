"""Local Analysis Schema Definitions
NEXUS Local Collector - Pydantic v2 Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class AnomalySeverityEnum(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LocalAlert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique alert ID")
    title: str = Field(..., min_length=1, max_length=256, description="Concise alert title")
    description: str = Field(..., description="Concise explanation of detected abnormal condition")
    severity: AnomalySeverityEnum = Field(..., description="Alert severity level")
    scenario_type: str = Field(..., description="Scenario key: high_cpu, slow_api, backend_unavailable, etc.")
    source_id: str = Field(..., description="Source where anomaly was detected")
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metric_name: Optional[str] = Field(default=None, description="Associated metric name if applicable")
    observed_value: Optional[float] = Field(default=None, description="Measured abnormal value")
    threshold_value: Optional[float] = Field(default=None, description="Configured threshold that was breached")
    recommendation: Optional[str] = Field(default=None, description="Recommended remediation action")
