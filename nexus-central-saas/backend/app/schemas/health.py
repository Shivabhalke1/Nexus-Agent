"""System and Application Health Monitoring Schemas"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthStateEnum(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class MetricSnapshot(BaseModel):
    name: str
    value: float
    unit: str
    status: str = "normal"


class ServiceHealthDetail(BaseModel):
    service_name: str
    health_state: HealthStateEnum
    status_indicator: str  # healthy, degraded, down, stale
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    error_rate: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    active_db_connections: Optional[int] = None
    db_pool_active: Optional[int] = None
    db_pool_max: Optional[int] = None
    cache_hit_rate_percent: Optional[float] = None
    active_threads: Optional[int] = None
    event_loop_latency_ms: Optional[float] = None
    orders_per_minute: Optional[float] = None
    cart_abandonment_rate: Optional[float] = None
    revenue_at_risk_usd: Optional[float] = None
    active_trace_id: Optional[str] = None
    last_telemetry_at: Optional[datetime] = None
    is_stale: bool = False


class SystemHealthSummary(BaseModel):
    overall_health: HealthStateEnum
    active_services_count: int
    total_incidents_active: int
    last_received_at: Optional[datetime] = None
    collector_connected: bool = True
    is_telemetry_stale: bool = False
    services: List[ServiceHealthDetail] = Field(default_factory=list)
    system_metrics: Dict[str, Any] = Field(default_factory=dict)
