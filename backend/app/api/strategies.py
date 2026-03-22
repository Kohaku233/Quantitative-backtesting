from pathlib import Path

from fastapi import APIRouter

from backend.app.models.strategies import StrategiesResponse
from backend.app.strategies.discovery import discover_strategies


router = APIRouter()
STRATEGIES_DIRECTORY = Path(__file__).resolve().parents[2] / "strategies"


@router.get("/strategies", response_model=StrategiesResponse)
def list_strategies() -> StrategiesResponse:
    strategies, discovery_warnings = discover_strategies(STRATEGIES_DIRECTORY)
    return StrategiesResponse(
        strategies=strategies,
        discovery_warnings=discovery_warnings,
    )
