"""Failure scenario execution workers for CPU load, DB faults, and synthetic auth stress."""
import json
import math
import threading
import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.failure_simulator.state import simulator_state
from app.models.event import ApplicationEvent


# Background worker for High CPU Load
class CpuBurner:
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, duration_seconds: int):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._burn, args=(duration_seconds,), daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _burn(self, duration_seconds: int):
        end_time = time.time() + duration_seconds
        while self._running and time.time() < end_time:
            # Mathematical load
            for _ in range(50000):
                math.sqrt(12345.6789) * math.sin(0.54321)
            time.sleep(0.001)  # Brief yield to prevent thread lockup
        self._running = False
        simulator_state.deactivate_scenario("high_cpu")


cpu_burner = CpuBurner()


def trigger_failed_logins(db: Session, count: int = 5, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate synthetic failed login telemetry events for Local Collector testing."""
    events_generated = []
    for i in range(count):
        synthetic_email = f"attacker_synthetic_{i+1}@anomaly-simulation.test"
        event = ApplicationEvent(
            event_type="AUTH_LOGIN_FAILED",
            request_id=request_id or f"sim-login-{int(time.time())}-{i}",
            severity="WARNING",
            payload=json.dumps({
                "synthetic": True,
                "email_domain": "anomaly-simulation.test",
                "reason": "Controlled Authentication Stress Simulation",
                "attempt": i + 1,
            }),
        )
        db.add(event)
        events_generated.append(synthetic_email)

    db.commit()
    return {"attempts_generated": len(events_generated), "synthetic_targets": events_generated}
