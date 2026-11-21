"""Policy Validation Schema Definitions
NEXUS Local Collector - Pydantic v2 Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ViolationSeverityEnum(str, Enum):
    BLOCK = "BLOCK"
    WARN = "WARN"


class PolicyViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Descriptive name of the rule violated")
    severity: ViolationSeverityEnum = Field(..., description="BLOCK prevents approval/transmission; WARN is advisory")
    message: str = Field(..., description="Detailed explanation of the policy violation")
    field_path: Optional[str] = Field(default=None, description="Field path that triggered the violation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context or limits exceeded")


class PolicyValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload_id: str = Field(..., description="ID of validated payload")
    is_compliant: bool = Field(..., description="True if no BLOCK violations exist")
    can_be_approved: bool = Field(..., description="Strictly False if any BLOCK violations exist")
    violations: List[PolicyViolation] = Field(default_factory=list, description="All violations detected")
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: str = Field(default="1.0.0", description="Version of the policy rule set applied")


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="Unique identifier for the policy rule")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="What the policy checks")
    severity: ViolationSeverityEnum = Field(default=ViolationSeverityEnum.BLOCK)
    rule_type: str = Field(..., description="e.g. disallow_sensitive_data, payload_size_limit, prohibited_field")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters for the rule")
