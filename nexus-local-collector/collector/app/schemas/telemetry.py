"""Telemetry Schema Definitions
NEXUS Local Collector - Pydantic v2 Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(str, Enum):
    HOST = "HOST"
    APPLICATION = "APPLICATION"
    NETWORK = "NETWORK"
    LOG = "LOG"


class SourceIdentifier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1, max_length=128, description="Unique identifier for the monitored source")
    source_type: SourceType = Field(..., description="Type of source being monitored")
    environment: str = Field(default="production", min_length=1, max_length=64, description="Deployment environment")
    hostname: Optional[str] = Field(default=None, max_length=256)
    ip_address: Optional[str] = Field(default=None, max_length=64)


class MetricData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128, description="Metric name")
    value: float = Field(..., description="Numeric value of the metric")
    unit: str = Field(default="gauge", max_length=32, description="Unit of measurement")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dimensions: Dict[str, Any] = Field(default_factory=dict, description="Metric labels/dimensions")


class SystemMetricsData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu_utilization_percent: float = Field(..., ge=0.0, le=100.0, description="Host CPU utilization percentage")
    memory_utilization_percent: float = Field(..., ge=0.0, le=100.0, description="Host memory utilization percentage")
    memory_used_bytes: int = Field(..., ge=0, description="Used memory in bytes")
    memory_total_bytes: int = Field(..., ge=0, description="Total memory in bytes")
    disk_utilization_percent: float = Field(..., ge=0.0, le=100.0, description="Host disk utilization percentage")
    disk_used_bytes: int = Field(..., ge=0, description="Used disk in bytes")
    disk_total_bytes: int = Field(..., ge=0, description="Total disk in bytes")
    network_bytes_sent: int = Field(default=0, ge=0, description="Total bytes sent")
    network_bytes_recv: int = Field(default=0, ge=0, description="Total bytes received")
    network_interfaces: Dict[str, Any] = Field(default_factory=dict, description="Interface specific statistics")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApplicationMetricsData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: str = Field(..., min_length=1, max_length=128, description="Name of the application service")
    status: str = Field(default="healthy", max_length=32, description="Application status (healthy, degraded, down)")
    http_requests_total: int = Field(default=0, ge=0, description="Total HTTP requests processed")
    http_errors_total: int = Field(default=0, ge=0, description="Total HTTP 4xx/5xx errors")
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Error rate between 0.0 and 1.0")
    avg_response_time_ms: float = Field(default=0.0, ge=0.0, description="Average response latency in ms")
    p95_response_time_ms: float = Field(default=0.0, ge=0.0, description="95th percentile latency in ms")
    active_db_connections: int = Field(default=0, ge=0, description="Number of active DB connections")
    db_query_errors: int = Field(default=0, ge=0, description="Number of DB query failures")
    
    # Extended Runtime, Database & Cache
    db_pool_active: Optional[int] = Field(default=2, ge=0, description="Active database pool connections")
    db_pool_max: Optional[int] = Field(default=20, ge=1, description="Configured maximum pool connections")
    cache_hit_rate_percent: Optional[float] = Field(default=95.2, ge=0.0, le=100.0, description="Cache hit ratio")
    active_threads: Optional[int] = Field(default=8, ge=1, description="Active worker thread count")
    event_loop_latency_ms: Optional[float] = Field(default=1.4, ge=0.0, description="Async event loop latency")

    # Security & Access Velocity
    failed_login_attempts: Optional[int] = Field(default=0, ge=0, description="Failed authentication attempts")

    # Business KPIs
    orders_per_minute: Optional[float] = Field(default=18.5, ge=0.0, description="Checkout transaction velocity")
    cart_abandonment_rate: Optional[float] = Field(default=8.2, ge=0.0, le=100.0, description="Cart abandonment %")
    revenue_at_risk_usd: Optional[float] = Field(default=0.0, ge=0.0, description="Estimated revenue impact during anomaly")
    active_trace_id: Optional[str] = Field(default="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01", description="OpenTelemetry trace correlation ID")

    raw_metrics: Dict[str, Any] = Field(default_factory=dict, description="Raw structured metrics from application")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: str = Field(default="INFO", max_length=16, description="Log level (INFO, WARN, ERROR, CRITICAL)")
    message: str = Field(..., max_length=8192, description="Log message text")
    service: str = Field(..., max_length=128, description="Originating service name")
    event_type: Optional[str] = Field(default=None, max_length=64, description="Event classification")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Structured log attributes")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper_v


class TelemetryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID for this payload batch")
    source: SourceIdentifier = Field(..., description="Origin source identifier")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    system_metrics: Optional[SystemMetricsData] = Field(default=None, description="Host system telemetry")
    application_metrics: Optional[ApplicationMetricsData] = Field(default=None, description="App telemetry")
    logs: List[LogEntry] = Field(default_factory=list, description="Structured logs collected")
    custom_events: List[Dict[str, Any]] = Field(default_factory=list, description="Custom application events")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Collection metadata")
    is_sanitized: bool = Field(default=False, description="Flag indicating whether data protection has run")
    sanitization_summary: Optional[Dict[str, Any]] = Field(default=None, description="Summary of applied protections")
