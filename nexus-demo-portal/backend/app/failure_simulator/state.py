"""In-memory state and safety controller for Controlled Failure Simulation."""
import time
import threading
from typing import Dict, Any, Optional

MAX_DURATION = 300  # Global safety limit: 5 minutes max


class SimulatorStateManager:
    """Thread-safe simulator state manager enforcing auto-expiration and safety limits."""

    def __init__(self):
        self._lock = threading.Lock()
        self.scenarios: Dict[str, Dict[str, Any]] = {
            "high_cpu": {"active": False, "duration": 15, "started_at": None, "expires_at": None},
            "slow_api": {"active": False, "delay_ms": 1500, "target_endpoint": "/api/v1/products", "expires_at": None},
            "backend_unavailable": {"active": False, "target_endpoint": "/api/v1/products", "expires_at": None},
            "database_failure": {"active": False, "expires_at": None},
            "increased_errors": {"active": False, "error_rate": 1.0, "target_endpoint": "/api/v1/products", "expires_at": None},
            "failed_logins": {"active": False, "count": 5, "last_run_at": None},
        }

    def _auto_expire_locked(self):
        """Check and deactivate expired scenarios."""
        now = time.time()
        for name, data in self.scenarios.items():
            if data.get("active") and data.get("expires_at"):
                if now >= data["expires_at"]:
                    data["active"] = False
                    data["expires_at"] = None

    def get_status(self) -> Dict[str, Any]:
        """Return the current active status of all 6 failure scenarios."""
        with self._lock:
            self._auto_expire_locked()
            status_copy = {}
            for name, data in self.scenarios.items():
                copy_d = dict(data)
                if copy_d.get("expires_at"):
                    copy_d["remaining_seconds"] = max(0, int(copy_d["expires_at"] - time.time()))
                else:
                    copy_d["remaining_seconds"] = 0
                status_copy[name] = copy_d
            return status_copy

    def activate_scenario(self, scenario_name: str, duration_seconds: int = 30, **kwargs) -> Dict[str, Any]:
        """Activate a designated failure scenario with an enforced timeout."""
        with self._lock:
            self._auto_expire_locked()
            if scenario_name not in self.scenarios:
                raise ValueError(f"Unknown scenario '{scenario_name}'")

            duration = min(max(1, duration_seconds), MAX_DURATION)
            now = time.time()
            data = self.scenarios[scenario_name]
            data["active"] = True
            data["started_at"] = now
            data["expires_at"] = now + duration

            # Update specific parameters
            for k, v in kwargs.items():
                if k in data and k not in {"active", "started_at", "expires_at"}:
                    data[k] = v

            return dict(data)

    def deactivate_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Deactivate a designated failure scenario."""
        with self._lock:
            if scenario_name not in self.scenarios:
                raise ValueError(f"Unknown scenario '{scenario_name}'")

            data = self.scenarios[scenario_name]
            data["active"] = False
            data["expires_at"] = None
            return dict(data)

    def reset_all(self):
        """Emergency reset: immediately disarm all failure scenarios."""
        with self._lock:
            for data in self.scenarios.values():
                data["active"] = False
                data["expires_at"] = None


# Global singleton instance
simulator_state = SimulatorStateManager()
