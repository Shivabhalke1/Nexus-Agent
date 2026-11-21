"""FastAPI Application Entry Point with Observability and Controlled Failure Simulation."""
import logging
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.exceptions import AppException
from app.core.seed import seed_database
from app.api.v1.router import api_router
from app.middleware.observability import ObservabilityMiddleware
from app.middleware.simulator import FailureSimulatorMiddleware
from app.observability.metrics import metrics_collector
from app.observability.logger import StructuredJsonFormatter

# Configure structured JSON logging
logger = logging.getLogger(settings.SERVICE_NAME)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(StructuredJsonFormatter())
logger.handlers = [handler]
logger.setLevel(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing database tables and initial seed data."""
    logger.info("Initializing database schema and initial seed data...")
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_database(db)
        logger.info("Database initialized and verified successfully.")
    except Exception as exc:
        logger.error(f"Error during startup database initialization: {str(exc)}", exc_info=True)
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for NEXUS Demo Portal — observable dummy e-commerce and anomaly testing platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware execution order:
# 1. Failure Simulator Middleware (Inner: executes anomalies)
app.add_middleware(FailureSimulatorMiddleware)

# 2. Observability Middleware (Outer: measures end-to-end timing including simulation delay)
app.add_middleware(ObservabilityMiddleware)


# Root Prometheus Scraper Endpoint
@app.get("/metrics", tags=["Observability"])
def prometheus_metrics():
    """Prometheus-compatible plaintext metrics scraping endpoint."""
    metrics_text = metrics_collector.export_prometheus()
    return PlainTextResponse(content=metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")


# Root Health Check (mirror of /api/v1/health for standard health probes)
@app.get("/health", tags=["Health"])
async def root_health():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
    }


# Centralized Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"Application error: code={exc.error_code} message={exc.message}",
        extra={"request_id": request_id, "endpoint": request.url.path, "status_code": exc.status_code},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": request_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        f"Validation error on {request.url.path}",
        extra={"request_id": request_id, "endpoint": request.url.path, "status_code": 422},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": exc.errors(),
            },
            "request_id": request_id,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Database error on {request.url.path}: {str(exc)}",
        extra={"request_id": request_id, "endpoint": request.url.path, "status_code": 500},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database operation error occurred",
            },
            "request_id": request_id,
        },
    )


# Mount API v1 router
app.include_router(api_router)
