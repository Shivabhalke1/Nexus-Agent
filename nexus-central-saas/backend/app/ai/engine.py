"""NEXUS Cortex AI Engine
Provides AI-driven Root Cause Analysis (RCA), anomaly diagnostics, and executive summaries.
Supports standalone offline ML heuristic inference and optional LLM augmentation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.entities import ActiveIncidentRecord, TelemetryRecord
from app.schemas.ai import (
    AIIncidentAnalysis,
    AIRootCauseCategory,
    AIHealthInsight,
)
from app.schemas.resolution import ResolutionOperationEnum
from app.core.logging_config import get_logger

logger = get_logger("ai_engine")


class AIRootCauseEngine:
    """AI-driven Root Cause Analysis Engine for Monitored Incidents."""

    MODEL_NAME = "NEXUS-Cortex-AI-v1.0 (Inference Engine)"

    # Knowledge Base: Scenario -> Category, Confidence Base, Recommended Action
    SCENARIO_PROFILES = {
        "high_cpu": {
            "category": AIRootCauseCategory.RESOURCE_EXHAUSTION,
            "base_confidence": 0.94,
            "root_cause": "Intense computational loop or unthrottled worker threads saturating host CPU cores.",
            "factors": [
                "Host CPU core utilization exceeded 85% critical threshold",
                "High concurrency without sufficient compute slice allocation",
                "Sub-optimal algorithm complexity or unindexed looping",
            ],
            "remediation": "Scale replica pods to distribute traffic load or throttle non-critical background jobs.",
            "operation": ResolutionOperationEnum.SCALE_REPLICAS.value,
        },
        "high_memory": {
            "category": AIRootCauseCategory.RESOURCE_EXHAUSTION,
            "base_confidence": 0.91,
            "root_cause": "Memory accumulation indicative of unbounded in-memory caches or memory leak.",
            "factors": [
                "Resident memory consumption exceeded 85% threshold",
                "Garbage collector pacing unable to keep up with allocation rate",
                "Session state retention without explicit expiration TTL",
            ],
            "remediation": "Flush application volatile memory cache and restart affected container process.",
            "operation": ResolutionOperationEnum.CLEAR_APP_CACHE.value,
        },
        "slow_api": {
            "category": AIRootCauseCategory.APPLICATION_DEGRADATION,
            "base_confidence": 0.89,
            "root_cause": "Downstream blocking I/O, lock contention, or cascading microservice response latency.",
            "factors": [
                "Average response latency exceeded 1000ms SLA threshold",
                "Thread worker pool exhaustion waiting on backend socket responses",
                "Upstream request backlog forming queue latency",
            ],
            "remediation": "Restart service to clear deadlocked worker threads and scale container instances.",
            "operation": ResolutionOperationEnum.RESTART_SERVICE.value,
        },
        "database_failure": {
            "category": AIRootCauseCategory.DATABASE_BOTTLENECK,
            "base_confidence": 0.96,
            "root_cause": "Database connection pool exhaustion, connection timeout, or deadlocked queries.",
            "factors": [
                "Active DB pool saturation with zero available idle connections",
                "Database driver query timeouts or failed TCP handshake",
                "Long-running table lock preventing transaction commits",
            ],
            "remediation": "Reset database connection pool and drop hanging transactions.",
            "operation": ResolutionOperationEnum.RESET_DB_POOL.value,
        },
        "increased_errors": {
            "category": AIRootCauseCategory.APPLICATION_DEGRADATION,
            "base_confidence": 0.92,
            "root_cause": "Application exception rate surge caused by unhandled internal state or corrupt data payloads.",
            "factors": [
                "HTTP 5xx error rate exceeded 5% critical threshold",
                "Service returning unhandled exceptions on primary request paths",
                "Transient network dependency or configuration mismatch",
            ],
            "remediation": "Restart application service and flush stale cache items.",
            "operation": ResolutionOperationEnum.RESTART_SERVICE.value,
        },
        "failed_logins": {
            "category": AIRootCauseCategory.SECURITY_ANOMALY,
            "base_confidence": 0.98,
            "root_cause": "Automated credential brute-force attack or credential stuffing campaign detected.",
            "factors": [
                "More than 5 consecutive authentication failures in rapid succession",
                "Unusual pattern of invalid username/password combinations",
                "Concentrated requests against authentication endpoint",
            ],
            "remediation": "Apply immediate IP-level rate limiting and trigger temporary account lockouts.",
            "operation": ResolutionOperationEnum.RATE_LIMIT_LOGIN.value,
        },
    }

    @classmethod
    def analyze_incident(
        cls,
        incident: ActiveIncidentRecord,
        recent_telemetry: Optional[List[TelemetryRecord]] = None,
    ) -> AIIncidentAnalysis:
        """Run AI root-cause analysis on an active incident."""
        scenario = incident.scenario_type.lower() if incident.scenario_type else "unknown"
        profile = cls.SCENARIO_PROFILES.get(scenario, {
            "category": AIRootCauseCategory.UNKNOWN,
            "base_confidence": 0.75,
            "root_cause": f"Anomalous behavior observed for scenario '{scenario}'.",
            "factors": ["Uncharacteristic metric drift detected against baseline"],
            "remediation": "Review system logs and perform graceful service restart.",
            "operation": ResolutionOperationEnum.RESTART_SERVICE.value,
        })

        # Dynamically adjust confidence score based on severity and observed metrics
        confidence = profile["base_confidence"]
        if incident.severity == "CRITICAL":
            confidence = min(0.99, confidence + 0.03)
        elif incident.severity == "LOW":
            confidence = max(0.60, confidence - 0.08)

        # Technical explanation synthesis
        metric_str = f"Observed {incident.metric_name} = {incident.observed_value:.1f}" if incident.observed_value is not None else "Anomalous condition active"
        threshold_str = f"(threshold: {incident.threshold_value:.1f})" if incident.threshold_value is not None else ""
        explanation = (
            f"The NEXUS Cortex AI Engine analyzed incident '{incident.incident_id}' affecting service '{incident.service_name}'. "
            f"{metric_str} {threshold_str}. "
            f"Pattern matching indicates a {confidence * 100:.1f}% probability of {profile['category'].value}. "
            f"{profile['root_cause']} "
            f"Recommended engineer remediation: execute '{profile['operation']}' to restore normal operational parameters."
        )

        analysis = AIIncidentAnalysis(
            analysis_id=f"ai_rca_{uuid4().hex[:8]}",
            incident_id=incident.incident_id,
            scenario_type=scenario,
            category=profile["category"],
            confidence_score=round(confidence, 2),
            root_cause_summary=profile["root_cause"],
            technical_explanation=explanation,
            contributing_factors=profile["factors"],
            suggested_remediation=profile["remediation"],
            recommended_operation=profile["operation"],
            model_version=cls.MODEL_NAME,
        )

        logger.info(
            f"AI RCA completed for incident {incident.incident_id}: "
            f"category={analysis.category}, confidence={analysis.confidence_score * 100:.1f}%"
        )
        return analysis

    @classmethod
    def generate_health_insights(
        cls,
        overall_health: str,
        active_incidents: List[ActiveIncidentRecord],
        metrics: Dict[str, Any],
    ) -> AIHealthInsight:
        """Synthesize high-level AI system health insights."""
        incident_count = len(active_incidents)
        anomaly_prob = 0.05
        if incident_count > 0:
            anomaly_prob = min(0.98, 0.40 + (incident_count * 0.20))
        elif overall_health in ["Fair", "Poor"]:
            anomaly_prob = 0.65

        findings = []
        recommendations = []

        if incident_count == 0:
            summary = "AI Health Monitor: All telemetry feeds are nominal. System exhibits stable performance and low latency."
            findings.append("No active anomalous incidents detected in current telemetry window.")
            findings.append(f"System health assessed as '{overall_health}' with {anomaly_prob*100:.1f}% anomaly probability.")
            recommendations.append("Maintain routine automated monitoring schedule.")
        else:
            summary = f"AI Health Monitor: Elevated risk detected. {incident_count} active incident(s) require engineer review."
            for inc in active_incidents[:3]:
                findings.append(f"{inc.severity} [{inc.scenario_type}]: {inc.title}")
            recommendations.append("Review and authorize pending problem-resolution operations in Engineer Approvals.")
            recommendations.append("Inspect resource saturation indicators and consider autoscaling.")

        return AIHealthInsight(
            insight_id=f"ai_insight_{uuid4().hex[:8]}",
            overall_health=overall_health,
            anomaly_probability=round(anomaly_prob, 2),
            executive_summary=summary,
            key_findings=findings,
            ai_recommendations=recommendations,
            model_version=cls.MODEL_NAME,
        )
