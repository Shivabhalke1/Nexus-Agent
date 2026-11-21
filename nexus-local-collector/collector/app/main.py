"""NEXUS Local Collector Application Entry Point."""
import logging
import os
from pathlib import Path
import sys
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import asyncio
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging_config import CollectorJsonFormatter
from app.api.v1.router import router as api_v1_router, execute_full_pipeline
from app.transmission.mock_saas import mock_saas_router

# Configure structured logging
logger = logging.getLogger(settings.APP_NAME)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(CollectorJsonFormatter())
logger.handlers = [handler]
logger.setLevel(settings.LOG_LEVEL)


async def background_monitoring_loop():
    """Continuously observes monitored services and automatically ingests anomalies into Human Approval queue."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return

    await asyncio.sleep(2)
    logger.info("Auto-Collection Engine: Active & Monitoring Demo Portal in Real-Time")
    while True:
        try:
            await execute_full_pipeline()
        except Exception as e:
            logger.debug(f"Auto-collection observation note: {e}")
        await asyncio.sleep(settings.COLLECTION_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_monitoring_loop())
    yield
    task.cancel()


app = FastAPI(
    title="NEXUS Local Collector",
    description="Privacy-first telemetry collection, inspection, sanitization, and human approval engine for NEXUS OBSERVE.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(mock_saas_router)  # Mock SaaS ingestion for self-contained testing & verification

# Locate static UI file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_FILE = BASE_DIR / "approval-interface" / "index.html"


@app.get("/", tags=["UI"])
@app.get("/ui", tags=["UI"])
def serve_ui():
    """Serve the interactive Human Approval dashboard."""
    if UI_FILE.exists():
        return FileResponse(UI_FILE)
    return JSONResponse(
        status_code=404,
        content={"error": "UI dashboard not found at expected path", "path": str(UI_FILE)},
    )


@app.get("/health", tags=["Diagnostics"])
@app.get("/api/v1/health", tags=["Diagnostics"])
def health_check():
    """Local Collector process health check."""
    return {
        "status": "healthy",
        "collector_id": settings.COLLECTOR_ID,
        "environment": settings.ENVIRONMENT,
        "service": settings.APP_NAME,
        "timestamp": time.time(),
        "human_approval_enforced": settings.REQUIRE_HUMAN_APPROVAL,
    }


@app.get("/status", tags=["Diagnostics"])
def collector_status():
    """Returns local collector operational state and target service configuration."""
    return {
        "collector_id": settings.COLLECTOR_ID,
        "monitored_targets": {
            "demo_portal_api": settings.DEMO_PORTAL_API_URL,
            "demo_portal_metrics": settings.DEMO_PORTAL_METRICS_URL,
            "demo_portal_health": settings.DEMO_PORTAL_HEALTH_URL,
        },
        "egress_target": settings.CENTRAL_SAAS_URL,
        "pipeline_stages": [
            "data_collection",
            "sensitive_data_detection",
            "data_filtering",
            "data_protection",
            "local_analysis",
            "policy_validation",
            "human_approval",
        ],
    }
