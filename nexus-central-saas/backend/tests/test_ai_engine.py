"""Tests for Integrated AI Engine (Feature: AI-Driven Root Cause & Observability Intelligence)"""

from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.entities import ActiveIncidentRecord

client = TestClient(app)


def test_ai_status_endpoint():
    resp = client.get("/api/v1/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert "NEXUS Cortex AI" in data["engine_name"]
    assert "Root Cause Analysis (RCA)" in data["capabilities"]
    assert "high_cpu" in data["supported_scenarios"]


def test_ai_analyze_incident():
    db = SessionLocal()
    test_id = f"inc_ai_{uuid4().hex[:8]}"
    # Create a test incident
    inc = ActiveIncidentRecord(
        incident_id=test_id,
        title="High CPU Saturation",
        description="CPU reached 94%",
        severity="CRITICAL",
        status="ACTIVE",
        scenario_type="high_cpu",
        source_id="nexus-demo-portal",
        service_name="demo-portal",
        metric_name="cpu_utilization_percent",
        observed_value=94.5,
        threshold_value=85.0,
    )
    db.add(inc)
    db.commit()
    db.close()

    resp = client.post(f"/api/v1/ai/analyze-incident/{test_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_id"] == test_id
    assert data["category"] == "RESOURCE_EXHAUSTION"
    assert data["confidence_score"] >= 0.85
    assert "NEXUS-Cortex-AI" in data["model_version"]
    assert data["recommended_operation"] == "SCALE_REPLICAS"
    assert len(data["contributing_factors"]) > 0

    # Cleanup
    db = SessionLocal()
    db.query(ActiveIncidentRecord).filter(ActiveIncidentRecord.incident_id == test_id).delete()
    db.commit()
    db.close()


def test_ai_health_insights():
    resp = client.get("/api/v1/ai/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert "executive_summary" in data
    assert "anomaly_probability" in data
    assert isinstance(data["key_findings"], list)
    assert isinstance(data["ai_recommendations"], list)
