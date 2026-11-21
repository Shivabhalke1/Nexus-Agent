"""AI Engine Schemas for Root Cause Analysis and Observability Intelligence"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIRootCauseCategory(str, Enum):
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    DATABASE_BOTTLENECK = "DATABASE_BOTTLENECK"
    APPLICATION_DEGRADATION = "APPLICATION_DEGRADATION"
    SECURITY_ANOMALY = "SECURITY_ANOMALY"
    NETWORK_SATURATION = "NETWORK_SATURATION"
    UNKNOWN = "UNKNOWN"


class AIIncidentAnalysis(BaseModel):
    analysis_id: str
    incident_id: str
    scenario_type: str
    category: AIRootCauseCategory
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    root_cause_summary: str
    technical_explanation: str
    contributing_factors: List[str]
    suggested_remediation: str
    recommended_operation: str
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str = "NEXUS-Cortex-AI-v1.0"


class AIHealthInsight(BaseModel):
    insight_id: str
    overall_health: str
    anomaly_probability: float
    executive_summary: str
    key_findings: List[str]
    ai_recommendations: List[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str = "NEXUS-Cortex-AI-v1.0"
