"""Database engine, session factory, and lifecycle management."""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)

# Connection arguments adjustments for SQLite vs PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions with automatic commit/rollback."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        logger.error(f"Database transaction error: {str(exc)}", exc_info=True)
        raise
    finally:
        db.close()


def check_db_health() -> bool:
    """Check connectivity to database by running a minimal query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning(f"Database health check failed: {str(exc)}")
        return False
