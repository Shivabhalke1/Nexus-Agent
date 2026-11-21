"""Telemetry Schemas matching NEXUS Local Collector Data Contract"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    HOST = "HOST"
    APPLICATION = "APPLICATION"
    NETWORK = "NETWORK"
    LOG = "LOG"


class SourceIdentifier(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_id: str = Field(..., min_length=1, max_length=128)
    source_type: SourceType = Field(...)
    environment: str = Field(default="production")
    hostname: Optional[str] = None
    ip_address: Optional[str] = None


class SystemMetricsData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cpu_utilization_percent: float = Field(..., ge=0.0, le=100.0)
    memory_utilization_percent: float = Field(..., ge=0.0, le=100.0)
    memory_used_bytes: int = Field(default=0, ge=0)
    memory_total_bytes: int = Field(default=1, ge=0)
    disk_utilization_percent: float = Field(..., ge=0.0, le=100.0)
    disk_used_bytes: int = Field(default=0, ge=0)
    disk_total_bytes: int = Field(default=1, ge=0)
    network_bytes_sent: int = Field(default=0, ge=0)
    network_bytes_recv: int = Field(default=0, ge=0)
    network_interfaces: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApplicationMetricsData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service_name: str = Field(..., min_length=1)
    status: str = Field(default="healthy")
    http_requests_total: int = Field(default=0, ge=0)
    http_errors_total: int = Field(default=0, ge=0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_response_time_ms: float = Field(default=0.0, ge=0.0)
    p95_response_time_ms: float = Field(default=0.0, ge=0.0)
    active_db_connections: int = Field(default=0, ge=0)
    db_query_errors: int = Field(default=0, ge=0)
    
    # Extended Runtime, Database & Cache
    db_pool_active: Optional[int] = Field(default=2, ge=0)
    db_pool_max: Optional[int] = Field(default=20, ge=1)
    cache_hit_rate_percent: Optional[float] = Field(default=95.2, ge=0.0, le=100.0)
    active_threads: Optional[int] = Field(default=8, ge=1)
    event_loop_latency_ms: Optional[float] = Field(default=1.4, ge=0.0)

    # Security & Access Velocity
    failed_login_attempts: Optional[int] = Field(default=0, ge=0)

    # Business KPIs
    orders_per_minute: Optional[float] = Field(default=18.5, ge=0.0)
    cart_abandonment_rate: Optional[float] = Field(default=8.2, ge=0.0, le=100.0)
    revenue_at_risk_usd: Optional[float] = Field(default=0.0, ge=0.0)
    active_trace_id: Optional[str] = Field(default="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01")

    raw_metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: str = Field(default="INFO")
    message: str = Field(...)
    service: str = Field(...)
    event_type: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TelemetryPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    payload_id: str = Field(...)
    source: SourceIdentifier = Field(...)
    collected_at: datetime = Field(...)
    system_metrics: Optional[SystemMetricsData] = None
    application_metrics: Optional[ApplicationMetricsData] = None
    logs: List[LogEntry] = Field(default_factory=list)
    custom_events: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_sanitized: bool = Field(default=False)
    sanitization_summary: Optional[Dict[str, Any]] = None
