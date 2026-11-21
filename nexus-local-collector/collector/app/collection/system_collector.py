"""System Metrics Collector using psutil
Collects host CPU, memory, disk, and network interface metrics.
"""

from datetime import datetime, timezone
import psutil
from app.schemas.telemetry import SystemMetricsData
from app.core.logging_config import get_logger

logger = get_logger("system_collector")


class SystemMetricsCollector:
    """Collects host-level resource utilization metrics."""

    def __init__(self, disk_path: str = "/"):
        self.disk_path = disk_path

    def collect(self) -> SystemMetricsData:
        """Collect host system metrics with safety fallbacks."""
        try:
            # CPU utilization (non-blocking snapshot or short sampling)
            cpu_percent = float(psutil.cpu_percent(interval=0.1))

            # Virtual Memory
            vmem = psutil.virtual_memory()
            mem_percent = float(vmem.percent)
            mem_used = int(vmem.used)
            mem_total = int(vmem.total)

            # Disk Usage
            try:
                disk = psutil.disk_usage(self.disk_path)
                disk_percent = float(disk.percent)
                disk_used = int(disk.used)
                disk_total = int(disk.total)
            except Exception as disk_err:
                logger.warning(f"Could not read disk usage for {self.disk_path}: {disk_err}")
                disk_percent = 0.0
                disk_used = 0
                disk_total = 0

            # Network I/O
            net_io = psutil.net_io_counters()
            bytes_sent = int(net_io.bytes_sent) if net_io else 0
            bytes_recv = int(net_io.bytes_recv) if net_io else 0

            # Per-interface summary (top non-loopback interfaces)
            interfaces = {}
            try:
                per_nic = psutil.net_io_counters(pernic=True)
                for nic_name, nic_io in per_nic.items():
                    interfaces[nic_name] = {
                        "bytes_sent": int(nic_io.bytes_sent),
                        "bytes_recv": int(nic_io.bytes_recv),
                        "packets_sent": int(nic_io.packets_sent),
                        "packets_recv": int(nic_io.packets_recv),
                        "errin": int(nic_io.errin),
                        "errout": int(nic_io.errout),
                    }
            except Exception as nic_err:
                logger.debug(f"Could not collect per-interface network stats: {nic_err}")

            return SystemMetricsData(
                cpu_utilization_percent=min(100.0, max(0.0, cpu_percent)),
                memory_utilization_percent=min(100.0, max(0.0, mem_percent)),
                memory_used_bytes=mem_used,
                memory_total_bytes=mem_total,
                disk_utilization_percent=min(100.0, max(0.0, disk_percent)),
                disk_used_bytes=disk_used,
                disk_total_bytes=disk_total,
                network_bytes_sent=bytes_sent,
                network_bytes_recv=bytes_recv,
                network_interfaces=interfaces,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error during system metrics collection: {e}")
            # Safe zero-state fallback
            return SystemMetricsData(
                cpu_utilization_percent=0.0,
                memory_utilization_percent=0.0,
                memory_used_bytes=0,
                memory_total_bytes=1,
                disk_utilization_percent=0.0,
                disk_used_bytes=0,
                disk_total_bytes=1,
                network_bytes_sent=0,
                network_bytes_recv=0,
                network_interfaces={},
                timestamp=datetime.now(timezone.utc),
            )
