"""Application event model for high-fidelity test instrumentation."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from app.models.base import BaseModel


def utc_now():
    return datetime.now(timezone.utc)


class ApplicationEvent(BaseModel):
    __tablename__ = "application_events"

    event_type = Column(String(64), index=True, nullable=False)
    request_id = Column(String(64), index=True, nullable=True)
    severity = Column(String(16), default="INFO", nullable=False)
    payload = Column(Text, nullable=True)  # JSON serialized data
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
