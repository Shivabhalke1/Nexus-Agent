"""Permitted Resolution Operations Registry (Feature 5)"""

from typing import Any, Dict, List
from app.schemas.resolution import ResolutionOperationEnum

PERMITTED_OPERATIONS: Dict[str, Dict[str, Any]] = {
    ResolutionOperationEnum.RESTART_SERVICE.value: {
        "operation_type": ResolutionOperationEnum.RESTART_SERVICE.value,
        "name": "Restart Service",
        "description": "Gracefully restarts target service worker process or container",
        "allowed_parameters": ["service", "grace_period_seconds"],
        "default_parameters": {"grace_period_seconds": 10},
    },
    ResolutionOperationEnum.SCALE_REPLICAS.value: {
        "operation_type": ResolutionOperationEnum.SCALE_REPLICAS.value,
        "name": "Scale Worker Replicas",
        "description": "Adjusts application worker instance count between 1 and 10",
        "allowed_parameters": ["replicas"],
        "default_parameters": {"replicas": 2},
    },
    ResolutionOperationEnum.RESET_DB_POOL.value: {
        "operation_type": ResolutionOperationEnum.RESET_DB_POOL.value,
        "name": "Reset Database Connection Pool",
        "description": "Flushes stale connections and re-establishes healthy pool sockets",
        "allowed_parameters": ["timeout_seconds"],
        "default_parameters": {"timeout_seconds": 5},
    },
    ResolutionOperationEnum.CLEAR_APP_CACHE.value: {
        "operation_type": ResolutionOperationEnum.CLEAR_APP_CACHE.value,
        "name": "Flush Application Memory Cache",
        "description": "Purges in-memory cached responses and temporary buffers",
        "allowed_parameters": ["cache_tier"],
        "default_parameters": {"cache_tier": "all"},
    },
    ResolutionOperationEnum.RATE_LIMIT_LOGIN.value: {
        "operation_type": ResolutionOperationEnum.RATE_LIMIT_LOGIN.value,
        "name": "Enable Strict Authentication Rate Limiting",
        "description": "Throttles repeated authentication attempts from suspicious IP sources",
        "allowed_parameters": ["max_attempts_per_minute"],
        "default_parameters": {"max_attempts_per_minute": 5},
    },
    ResolutionOperationEnum.RESET_FAILURE_SIMULATOR.value: {
        "operation_type": ResolutionOperationEnum.RESET_FAILURE_SIMULATOR.value,
        "name": "Reset Demo Failure Simulator",
        "description": "Calls Demo Portal simulator reset endpoint to clear simulated faults",
        "allowed_parameters": ["target_url"],
        "default_parameters": {"target_url": "http://localhost:8000/api/v1/simulate/reset"},
    },
}


def get_permitted_operations() -> List[Dict[str, Any]]:
    """Return all configured permitted resolution operations."""
    return list(PERMITTED_OPERATIONS.values())
