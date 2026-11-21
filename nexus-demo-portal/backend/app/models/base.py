"""Base model with shared columns."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
