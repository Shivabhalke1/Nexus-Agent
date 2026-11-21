"""REST endpoints to inspect, activate, and deactivate failure simulation scenarios."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.schemas.response import APIResponse
from app.failure_simulator.state import simulator_state
from app.failure_simulator.scenarios import cpu_burner, trigger_failed_logins

router = APIRouter(prefix="/simulator", tags=["Failure Simulator"])


class ActivateScenarioRequest(BaseModel):
    duration_seconds: int = Field(15, ge=1, le=300, description="Duration in seconds (max 300s)")
    delay_ms: Optional[int] = Field(None, ge=100, le=5000)
    target_endpoint: Optional[str] = None
    count: Optional[int] = Field(None, ge=1, le=50)


def verify_simulator_access(x_simulation_key: Optional[str] = Header(None)):
    """Ensure failure simulator is only invoked in allowed environments with valid key if set."""
    if not settings.ENABLE_FAILURE_SIMULATOR:
        raise UnauthorizedException("Failure Simulator is disabled in this environment.")
    if settings.SIMULATION_AUTH_KEY and x_simulation_key != settings.SIMULATION_AUTH_KEY:
        # In development mode, allow header or match default
        if x_simulation_key is None and settings.ENVIRONMENT == "development":
            return True
        elif x_simulation_key != settings.SIMULATION_AUTH_KEY:
            raise UnauthorizedException("Invalid or missing X-Simulation-Key header.")
    return True


@router.get("/status", response_model=APIResponse[Dict[str, Any]])
def get_simulator_status():
    """Retrieve the current active status and remaining duration of all 6 scenarios."""
    return APIResponse(
        success=True,
        message="Simulator status retrieved",
        data=simulator_state.get_status(),
    )


@router.post("/scenarios/{scenario_name}/activate", response_model=APIResponse[Dict[str, Any]])
def activate_scenario(
    scenario_name: str,
    body: ActivateScenarioRequest,
    request: Request,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_simulator_access),
):
    """Safely activate a designated failure scenario."""
    extra_params = {}
    if body.delay_ms is not None:
        extra_params["delay_ms"] = body.delay_ms
    if body.target_endpoint is not None:
        extra_params["target_endpoint"] = body.target_endpoint
    if body.count is not None:
        extra_params["count"] = body.count

    result = simulator_state.activate_scenario(
        scenario_name=scenario_name,
        duration_seconds=body.duration_seconds,
        **extra_params,
    )

    # Trigger background action if needed
    if scenario_name == "high_cpu":
        cpu_burner.start(duration_seconds=body.duration_seconds)
    elif scenario_name == "failed_logins":
        attempts = trigger_failed_logins(
            db=db,
            count=body.count or 5,
            request_id=getattr(request.state, "request_id", None),
        )
        result.update(attempts)

    # Instant event-driven push to Local Collector
    try:
        import asyncio, httpx
        async def _trigger_collector():
            await asyncio.sleep(0.5)
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    await client.post("http://127.0.0.1:8001/api/v1/pipeline/run")
            except Exception:
                pass
        asyncio.create_task(_trigger_collector())
    except Exception:
        pass

    return APIResponse(
        success=True,
        message=f"Scenario '{scenario_name}' activated successfully.",
        data=result,
    )


@router.post("/scenarios/{scenario_name}/deactivate", response_model=APIResponse[Dict[str, Any]])
def deactivate_scenario(
    scenario_name: str,
    _auth: bool = Depends(verify_simulator_access),
):
    """Deactivate a designated failure scenario."""
    if scenario_name == "high_cpu":
        cpu_burner.stop()

    result = simulator_state.deactivate_scenario(scenario_name)
    return APIResponse(
        success=True,
        message=f"Scenario '{scenario_name}' deactivated successfully.",
        data=result,
    )


@router.post("/reset", response_model=APIResponse[Dict[str, Any]])
def reset_all_scenarios(
    _auth: bool = Depends(verify_simulator_access),
):
    """Emergency reset: disarm all 6 scenarios immediately."""
    cpu_burner.stop()
    simulator_state.reset_all()
    return APIResponse(
        success=True,
        message="All failure scenarios have been safely stopped.",
        data=simulator_state.get_status(),
    )
