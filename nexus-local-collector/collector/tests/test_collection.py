"""Unit and Integration Tests for Telemetry Collection Engine
"""

import pytest
from app.collection.system_collector import SystemMetricsCollector
from app.collection.app_collector import ApplicationMetricsCollector
from app.collection.orchestrator import CollectionOrchestrator
from app.schemas.telemetry import TelemetryPayload, SystemMetricsData, ApplicationMetricsData


def test_system_metrics_collector():
    collector = SystemMetricsCollector()
    metrics = collector.collect()
    assert isinstance(metrics, SystemMetricsData)
    assert 0.0 <= metrics.cpu_utilization_percent <= 100.0
    assert 0.0 <= metrics.memory_utilization_percent <= 100.0
    assert metrics.memory_used_bytes > 0
    assert metrics.memory_total_bytes > 0
    assert 0.0 <= metrics.disk_utilization_percent <= 100.0
    assert metrics.network_bytes_sent >= 0
    assert metrics.network_bytes_recv >= 0


@pytest.mark.asyncio
async def test_app_metrics_collector_against_live_demo_portal():
    # The Demo Portal is currently running on localhost:8000
    collector = ApplicationMetricsCollector(base_url="http://localhost:8000")
    
    # Check health collection
    health = await collector.collect_health()
    assert isinstance(health, dict)
    assert health.get("status") in ("healthy", "degraded", "down")

    # Check metrics collection
    app_metrics = await collector.collect_metrics()
    assert isinstance(app_metrics, ApplicationMetricsData)
    assert app_metrics.service_name == "nexus-demo-portal"
    assert app_metrics.status in ("healthy", "degraded", "down")

    # Check events collection
    events = await collector.collect_events(limit=10)
    assert isinstance(events, list)


@pytest.mark.asyncio
async def test_app_metrics_collector_offline_fallback():
    # Target an unreachable port to test safety handling
    collector = ApplicationMetricsCollector(base_url="http://localhost:59999", timeout_seconds=0.5)
    
    health = await collector.collect_health()
    assert health["status"] in ("down", "unresponsive", "error")

    app_metrics = await collector.collect_metrics()
    assert app_metrics.service_name == "nexus-demo-portal"
    assert app_metrics.status in ("down", "unresponsive", "error")

    events = await collector.collect_events()
    assert events == []


@pytest.mark.asyncio
async def test_collection_orchestrator():
    orchestrator = CollectionOrchestrator()
    payload = await orchestrator.collect_batch(include_events=True)

    assert isinstance(payload, TelemetryPayload)
    assert payload.source.source_id == "nexus-demo-portal"
    assert payload.system_metrics is not None
    assert payload.application_metrics is not None
    assert payload.is_sanitized is False  # Must start raw/unsanitized
    assert "collector_version" in payload.metadata
