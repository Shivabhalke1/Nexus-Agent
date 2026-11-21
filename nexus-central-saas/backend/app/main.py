"""NEXUS Central SaaS FastAPI Application Entry Point"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from app.core.config import settings
from app.core.database import Base, engine
from app.api.auth import auth_router
from app.api.ingestion import ingestion_router
from app.api.health import health_router
from app.api.incidents import incidents_router
from app.api.approvals import approvals_router
from app.api.resolution import resolution_router
from app.api.ai import ai_router
from app.api.proof import proof_router

# Initialize database schema tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NEXUS Central SaaS",
    description="Centralized observability, system health monitoring, incident detection, engineer approval, and problem resolution platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(ingestion_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(resolution_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(proof_router, prefix="/api/v1")


@app.get("/health", tags=["Diagnostics"])
def health_check():
    """Central SaaS health check."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "database": "connected",
    }


@app.get("/status", tags=["Diagnostics"])
def service_status():
    """Operational status and feature configuration."""
    return {
        "service": settings.APP_NAME,
        "features": [
            "receive_data",
            "system_health_monitoring",
            "incident_detection",
            "engineer_approval",
            "resolve_problem",
            "ai_engine",
        ],
        "monitored_health_states": ["Excellent", "Good", "Fair", "Poor"],
        "collector_api_key_configured": bool(settings.COLLECTOR_API_KEY),
        "local_collector_url": settings.LOCAL_COLLECTOR_URL,
    }


# Frontend UI Serving
FRONTEND_HTML_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/index.html")
)


@app.get("/", include_in_schema=False)
@app.get("/ui", include_in_schema=False)
def serve_ui():
    """Serve the Central SaaS Dashboard Single-Page Application."""
    if os.path.exists(FRONTEND_HTML_PATH):
        return FileResponse(FRONTEND_HTML_PATH)
    return HTMLResponse(
        "<h3>NEXUS Central SaaS Frontend</h3><p>Dashboard UI template not found at expected path.</p>"
    )
