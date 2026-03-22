from typing import Annotated

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.app.data.binance_client import BinancePublicClient
from backend.app.data.repository import DuckDbRepository
from backend.app.data.sync_service import DataSyncService, StrategyNotFoundError
from backend.app.db import get_database_path
from backend.app.models.data_sync import CoverageStatusResponse, DataSyncRequest, DataSyncResponse
from backend.app.strategies.discovery import discover_strategies


router = APIRouter()


def _strategy_not_found_response(strategy_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "strategy_not_found",
                "message": f"Strategy '{strategy_id}' was not found.",
                "details": {"strategy_id": strategy_id},
            }
        },
    )


@lru_cache
def get_data_service() -> DataSyncService:
    project_root = Path(__file__).resolve().parents[3]
    repository = DuckDbRepository(get_database_path(project_root))
    repository.initialize_schema()
    strategies, _ = discover_strategies(Path(__file__).resolve().parents[2] / "strategies")
    return DataSyncService(
        repository=repository,
        binance_client=BinancePublicClient(),
        strategy_lookback_by_id={
            strategy.id: strategy.required_lookback_bars for strategy in strategies
        },
    )


@router.get("/data/status", response_model=CoverageStatusResponse)
def get_data_status(
    request: Annotated[DataSyncRequest, Depends()],
) -> CoverageStatusResponse:
    try:
        return get_data_service().get_status(request)
    except StrategyNotFoundError as exc:
        return _strategy_not_found_response(exc.strategy_id)


@router.post("/data/sync", response_model=DataSyncResponse)
async def sync_data(request: DataSyncRequest):
    try:
        return await get_data_service().sync_market_data(request)
    except StrategyNotFoundError as exc:
        return _strategy_not_found_response(exc.strategy_id)
