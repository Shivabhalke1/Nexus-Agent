"""Health schemas for service diagnostic reporting."""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ComponentHealth(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    timestamp: float
    components: Dict[str, ComponentHealth]
