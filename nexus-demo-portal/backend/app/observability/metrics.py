"""Thread-safe Metrics Collector capturing host and application telemetry."""
import os
import threading
import time
from typing import Dict, Any, List
from collections import defaultdict
import psutil

START_TIME = time.time()


class MetricsCollector:
    """In-memory sliding window and cumulative telemetry metrics collector."""

    def __init__(self):
        self._lock = threading.Lock()
        self.total_requests = 0
        self.total_errors = 0
        self.requests_by_endpoint: Dict[str, int] = defaultdict(int)
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.total_duration_ms = 0.0
        self.min_duration_ms = float("inf")
        self.max_duration_ms = 0.0
        self.duration_buckets = {
            "le_10ms": 0,
            "le_50ms": 0,
            "le_100ms": 0,
            "le_250ms": 0,
            "le_500ms": 0,
            "le_1000ms": 0,
            "gt_1000ms": 0,
        }

    def record_request(self, endpoint: str, status_code: int, duration_ms: float):
        """Record an API request event thread-safely."""
        with self._lock:
            self.total_requests += 1
            self.requests_by_endpoint[endpoint] += 1
            self.status_codes[status_code] += 1
            self.total_duration_ms += duration_ms

            if duration_ms < self.min_duration_ms:
                self.min_duration_ms = duration_ms
            if duration_ms > self.max_duration_ms:
                self.max_duration_ms = duration_ms

            if status_code >= 400:
                self.total_errors += 1

            # Bucket latency
            if duration_ms <= 10:
                self.duration_buckets["le_10ms"] += 1
            elif duration_ms <= 50:
                self.duration_buckets["le_50ms"] += 1
            elif duration_ms <= 100:
                self.duration_buckets["le_100ms"] += 1
            elif duration_ms <= 250:
                self.duration_buckets["le_250ms"] += 1
            elif duration_ms <= 500:
                self.duration_buckets["le_500ms"] += 1
            elif duration_ms <= 1000:
                self.duration_buckets["le_1000ms"] += 1
            else:
                self.duration_buckets["gt_1000ms"] += 1

    def get_system_metrics(self) -> Dict[str, Any]:
        """Collect real-time host and process system telemetry via psutil."""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            process = psutil.Process(os.getpid())
            proc_mem = process.memory_info()

            return {
                "cpu_percent": cpu_percent,
                "memory_used_mb": round(mem.used / (1024 * 1024), 2),
                "memory_total_mb": round(mem.total / (1024 * 1024), 2),
                "memory_percent": mem.percent,
                "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "disk_percent": disk.percent,
                "process_memory_mb": round(proc_mem.rss / (1024 * 1024), 2),
                "process_threads": process.num_threads(),
                "uptime_seconds": round(time.time() - START_TIME, 2),
            }
        except Exception as exc:
            return {
                "error": f"Failed to inspect host telemetry: {str(exc)}",
                "uptime_seconds": round(time.time() - START_TIME, 2),
            }

    def get_application_metrics(self) -> Dict[str, Any]:
        """Return application-level metrics snapshot."""
        with self._lock:
            avg_duration = round(self.total_duration_ms / self.total_requests, 2) if self.total_requests > 0 else 0.0
            error_rate = round((self.total_errors / self.total_requests) * 100, 2) if self.total_requests > 0 else 0.0

            return {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate_percent": error_rate,
                "avg_response_time_ms": avg_duration,
                "min_response_time_ms": self.min_duration_ms if self.min_duration_ms != float("inf") else 0.0,
                "max_response_time_ms": self.max_duration_ms,
                "requests_by_endpoint": dict(self.requests_by_endpoint),
                "status_codes": dict(self.status_codes),
                "latency_distribution": dict(self.duration_buckets),
            }

    def export_prometheus(self) -> str:
        """Export metrics formatted for Prometheus scrapers."""
        app_m = self.get_application_metrics()
        sys_m = self.get_system_metrics()

        lines = [
            "# HELP nexus_requests_total Total number of HTTP requests processed.",
            "# TYPE nexus_requests_total counter",
            f"nexus_requests_total {app_m['total_requests']}",
            "",
            "# HELP nexus_errors_total Total number of HTTP errors (status >= 400).",
            "# TYPE nexus_errors_total counter",
            f"nexus_errors_total {app_m['total_errors']}",
            "",
            "# HELP nexus_response_time_avg_ms Average HTTP response time in milliseconds.",
            "# TYPE nexus_response_time_avg_ms gauge",
            f"nexus_response_time_avg_ms {app_m['avg_response_time_ms']}",
            "",
            "# HELP nexus_system_cpu_percent Host CPU utilization percentage.",
            "# TYPE nexus_system_cpu_percent gauge",
            f"nexus_system_cpu_percent {sys_m.get('cpu_percent', 0.0)}",
            "",
            "# HELP nexus_system_memory_percent Host memory utilization percentage.",
            "# TYPE nexus_system_memory_percent gauge",
            f"nexus_system_memory_percent {sys_m.get('memory_percent', 0.0)}",
            "",
            "# HELP nexus_system_uptime_seconds Application uptime in seconds.",
            "# TYPE nexus_system_uptime_seconds gauge",
            f"nexus_system_uptime_seconds {sys_m.get('uptime_seconds', 0.0)}",
        ]

        # Break down per status code
        lines.append("")
        lines.append("# HELP nexus_http_requests_by_status HTTP requests partitioned by status code.")
        lines.append("# TYPE nexus_http_requests_by_status counter")
        for sc, count in app_m["status_codes"].items():
            lines.append(f'nexus_http_requests_by_status{{status="{sc}"}} {count}')

        return "\n".join(lines) + "\n"


# Global singleton metrics collector
metrics_collector = MetricsCollector()
