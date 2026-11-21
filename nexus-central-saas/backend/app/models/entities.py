"""SQLAlchemy 2.0 Database Models for NEXUS Central SaaS"""

from datetime import datetime, timezone
import json
from typing import Any, Dict
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="engineer")  # engineer, admin
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Collector(Base):
    __tablename__ = "collectors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collector_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    api_key = Column(String(256), nullable=False)
    environment = Column(String(64), default="production")
    last_seen_at = Column(DateTime, nullable=True)


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payload_id = Column(String(64), unique=True, nullable=False, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    source_id = Column(String(128), nullable=False, index=True)
    environment = Column(String(64), default="production")
    is_sanitized = Column(Boolean, default=True)
    payload_hash = Column(String(128), nullable=False)
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    payload_json = Column(Text, nullable=False)


class HealthSnapshotRecord(Base):
    __tablename__ = "health_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(128), nullable=False, index=True)
    overall_health = Column(String(32), nullable=False)  # Excellent, Good, Fair, Poor
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    avg_latency_ms = Column(Float, nullable=True)
    active_db_connections = Column(Integer, nullable=True)
    is_stale = Column(Boolean, default=False)
    calculated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class ActiveIncidentRecord(Base):
    __tablename__ = "active_incidents"

    incident_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), default="ACTIVE", index=True)  # ACTIVE, RESOLVED, RESOLVING
    scenario_type = Column(String(64), nullable=False, index=True)
    source_id = Column(String(128), nullable=False, index=True)
    service_name = Column(String(128), nullable=False)
    metric_name = Column(String(64), nullable=True)
    observed_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_operation_id = Column(String(64), nullable=True)


class ResolutionOperationRecord(Base):
    __tablename__ = "resolution_operations"

    operation_id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("active_incidents.incident_id"), nullable=False, index=True)
    operation_type = Column(String(64), nullable=False)
    parameters_json = Column(Text, default="{}")
    description = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING_APPROVAL", index=True)
    approved_by = Column(String(64), nullable=True)
    approval_reason = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
