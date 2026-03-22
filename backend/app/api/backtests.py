from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.app.data.repository import DuckDbRepository
from backend.app.db import get_database_path
from backend.app.models.backtests import BacktestRunRequest, BacktestRunResponse, build_error_envelope
from backend.app.services.backtest_service import (
    BacktestDataCoverageMissingError,
    BacktestFailedError,
    BacktestService,
    BacktestStrategyExecutionServiceError,
    BacktestStrategyNotFoundError,
    BacktestStrategyValidationServiceError,
)
from backend.app.strategies.discovery import discover_strategy_registry


router = APIRouter()


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=build_error_envelope(code=code, message=message, details=details).model_dump(),
    )


@lru_cache
def get_backtest_service() -> BacktestService:
    project_root = Path(__file__).resolve().parents[3]
    repository = DuckDbRepository(get_database_path(project_root))
    repository.initialize_schema()
    strategy_plugins_by_id, strategy_metadata_by_id, _ = discover_strategy_registry(
        Path(__file__).resolve().parents[2] / "strategies"
    )
    return BacktestService(
        repository=repository,
        strategy_plugins_by_id=strategy_plugins_by_id,
        strategy_metadata_by_id=strategy_metadata_by_id,
    )


@router.post("/backtests/run", response_model=BacktestRunResponse)
def run_backtest_endpoint(
    request: BacktestRunRequest,
    service: Annotated[BacktestService, Depends(get_backtest_service)],
):
    try:
        return service.run(request)
    except BacktestStrategyNotFoundError as exc:
        return _error_response(
            status_code=404,
            code="strategy_not_found",
            message=f"Strategy '{exc.strategy_id}' was not found.",
            details={"strategy_id": exc.strategy_id},
        )
    except BacktestDataCoverageMissingError as exc:
        return _error_response(
            status_code=409,
            code="data_coverage_missing",
            message="Required market data coverage is incomplete for this run.",
            details={"coverage": exc.coverage.model_dump()},
        )
    except BacktestStrategyValidationServiceError as exc:
        return _error_response(
            status_code=422,
            code="strategy_validation_error",
            message=str(exc),
            details=exc.details,
        )
    except BacktestStrategyExecutionServiceError as exc:
        return _error_response(
            status_code=422,
            code="strategy_execution_error",
            message=str(exc),
            details=exc.details,
        )
    except BacktestFailedError as exc:
        return _error_response(
            status_code=500,
            code="backtest_failed",
            message=str(exc),
        )
