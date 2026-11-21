"""Thresholds Configuration for Local Telemetry Analysis
Defines operational anomaly limits for system and application metrics.
"""

from dataclasses import dataclass


@dataclass
class AnomalyThresholds:
    # Host System Thresholds
    cpu_percent_warn: float = 75.0
    cpu_percent_critical: float = 85.0
    memory_percent_warn: float = 80.0
    memory_percent_critical: float = 90.0
    disk_percent_warn: float = 85.0
    disk_percent_critical: float = 95.0

    # Application Thresholds (Matching Demo Portal Failure Modes)
    api_latency_ms_warn: float = 300.0
    api_latency_ms_critical: float = 800.0
    error_rate_warn: float = 0.05       # 5% error rate
    error_rate_critical: float = 0.15   # 15% error rate
    failed_logins_threshold: int = 3    # 3 or more failed logins in a collection batch
    db_errors_threshold: int = 1        # Any DB query failure triggers alert


DEFAULT_THRESHOLDS = AnomalyThresholds()
