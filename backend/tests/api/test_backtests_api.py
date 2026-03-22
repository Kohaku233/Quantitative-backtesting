from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.models.strategies import StrategyMetadata
from backend.app.strategies.base import BaseStrategyPlugin, StrategyValidationError


VALID_REQUEST = {
    "strategy_id": "sma_cross",
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "start": "2024-01-01T03:00:00Z",
    "end": "2024-01-01T08:59:59Z",
    "initial_capital": 10000,
    "leverage": 2,
    "fee_bps": 4,
    "slippage_bps": 2,
    "position_size_pct": 0.95,
    "params": {
        "fast_period": 2,
        "slow_period": 3,
    },
}


class TestSmaCrossStrategy(BaseStrategyPlugin):
    id = "sma_cross"
    name = "SMA Cross"
    description = "Long/short moving-average crossover strategy."
    supported_timeframes = ("1h",)
    required_lookback_bars = 3
    parameter_schema = [
        {
            "key": "fast_period",
            "label": "Fast Period",
            "type": "integer",
            "default": 2,
            "required": True,
            "min": 1,
            "max": 50,
        },
        {
            "key": "slow_period",
            "label": "Slow Period",
            "type": "integer",
            "default": 3,
            "required": True,
            "min": 2,
            "max": 50,
        },
    ]

    @classmethod
    def validate_params(cls, params: Mapping[str, Any]) -> dict[str, int]:
        fast_period = int(params["fast_period"])
        slow_period = int(params["slow_period"])
        if fast_period >= slow_period:
            raise StrategyValidationError("fast_period must be less than slow_period")
        return {
            "fast_period": fast_period,
            "slow_period": slow_period,
        }

    @classmethod
    def compute_indicators(
        cls,
        df: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "fast_sma": df["close"].rolling(int(params["fast_period"])).mean(),
                "slow_sma": df["close"].rolling(int(params["slow_period"])).mean(),
            },
            index=df.index,
        )

    @classmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        signals = pd.Series(0, index=df.index, dtype="int8")
        signals.loc[indicators["fast_sma"] > indicators["slow_sma"]] = 1
        signals.loc[indicators["fast_sma"] < indicators["slow_sma"]] = -1
        return signals


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _build_kline_rows() -> list[dict[str, object]]:
    open_times = [_dt("2024-01-01T00:00:00Z") + timedelta(hours=index) for index in range(9)]
    close_values = [100.0, 100.0, 100.0, 100.0, 102.0, 104.0, 103.0, 101.0, 99.0]

    rows: list[dict[str, object]] = []
    previous_close = close_values[0]
    for index, (open_time, close_price) in enumerate(zip(open_times, close_values, strict=True)):
        open_price = previous_close if index > 0 else close_price
        high_price = max(open_price, close_price) + 1.0
        low_price = min(open_price, close_price) - 1.0
        close_time = open_time + timedelta(minutes=59, seconds=59)
        rows.append(
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "open_time": _format_timestamp(open_time),
                "close_time": _format_timestamp(close_time),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 1000.0 + index,
            }
        )
        previous_close = close_price
    return rows


def _build_warmup_entry_kline_rows() -> list[dict[str, object]]:
    open_times = [_dt("2024-01-01T00:00:00Z") + timedelta(hours=index) for index in range(9)]
    close_values = [100.0, 100.0, 102.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]

    rows: list[dict[str, object]] = []
    previous_close = close_values[0]
    for index, (open_time, close_price) in enumerate(zip(open_times, close_values, strict=True)):
        open_price = previous_close if index > 0 else close_price
        close_time = open_time + timedelta(minutes=59, seconds=59)
        rows.append(
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "open_time": _format_timestamp(open_time),
                "close_time": _format_timestamp(close_time),
                "open": open_price,
                "high": max(open_price, close_price) + 1.0,
                "low": min(open_price, close_price) - 1.0,
                "close": close_price,
                "volume": 2000.0 + index,
            }
        )
        previous_close = close_price
    return rows


def _build_funding_rows() -> list[dict[str, object]]:
    return [
        {
            "symbol": "BTCUSDT",
            "funding_time": "2024-01-01T08:00:00Z",
            "funding_rate": 0.0001,
        }
    ]


def _build_service(
    database_path: Path,
    *,
    seed_market_data: bool,
    kline_rows: list[dict[str, object]] | None = None,
):
    from backend.app.data.repository import DuckDbRepository
    from backend.app.services.backtest_service import BacktestService

    repository = DuckDbRepository(database_path)
    repository.initialize_schema()
    if seed_market_data:
        repository.upsert_klines(kline_rows or _build_kline_rows())
        repository.upsert_funding_rates(_build_funding_rows())

    metadata = StrategyMetadata(
        id=TestSmaCrossStrategy.id,
        name=TestSmaCrossStrategy.name,
        description=TestSmaCrossStrategy.description,
        supported_timeframes=list(TestSmaCrossStrategy.supported_timeframes),
        required_lookback_bars=TestSmaCrossStrategy.required_lookback_bars,
        parameter_schema=TestSmaCrossStrategy.parameter_schema,
    )
    return BacktestService(
        repository=repository,
        strategy_plugins_by_id={metadata.id: TestSmaCrossStrategy},
        strategy_metadata_by_id={metadata.id: metadata},
    )


@contextmanager
def _override_service(client, service) -> Iterator[None]:
    from backend.app.api import backtests as backtests_api

    client.app.dependency_overrides[backtests_api.get_backtest_service] = lambda: service
    try:
        yield
    finally:
        client.app.dependency_overrides.clear()


def test_run_endpoint_rejects_missing_coverage(client, tmp_path: Path) -> None:
    service = _build_service(tmp_path / "missing-coverage.duckdb", seed_market_data=False)

    with _override_service(client, service):
        response = client.post("/api/backtests/run", json=VALID_REQUEST)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "data_coverage_missing"


def test_run_endpoint_rejects_unknown_strategy(client, tmp_path: Path) -> None:
    service = _build_service(tmp_path / "unknown-strategy.duckdb", seed_market_data=True)

    with _override_service(client, service):
        response = client.post(
            "/api/backtests/run",
            json={**VALID_REQUEST, "strategy_id": "does_not_exist"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "strategy_not_found"


def test_run_endpoint_rejects_invalid_request_shape(client) -> None:
    response = client.post("/api/backtests/run", json={"strategy_id": "sma_cross"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_run_endpoint_rejects_invalid_strategy_params(client, tmp_path: Path) -> None:
    service = _build_service(tmp_path / "invalid-params.duckdb", seed_market_data=True)

    with _override_service(client, service):
        response = client.post(
            "/api/backtests/run",
            json={**VALID_REQUEST, "params": {"fast_period": 3, "slow_period": 2}},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "strategy_validation_error"
    assert response.json()["error"]["details"] == {"field": "fast_period"}


def test_run_endpoint_rejects_missing_strategy_param_as_validation_error(client, tmp_path: Path) -> None:
    service = _build_service(tmp_path / "missing-param.duckdb", seed_market_data=True)

    with _override_service(client, service):
        response = client.post(
            "/api/backtests/run",
            json={**VALID_REQUEST, "params": {"fast_period": 2}},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "strategy_validation_error"
    assert response.json()["error"]["details"] == {"field": "slow_period"}


def test_run_endpoint_returns_metrics_series_and_trade_rows(client, tmp_path: Path) -> None:
    service = _build_service(tmp_path / "seeded.duckdb", seed_market_data=True)

    with _override_service(client, service):
        response = client.post("/api/backtests/run", json=VALID_REQUEST)

    payload = response.json()

    assert response.status_code == 200
    assert payload["metrics"]["total_trades"] >= 1
    assert payload["run"]["status"] == "completed"
    assert payload["coverage"]["complete"] is True
    assert payload["series"]["market_bars"][0]["time"] == "2024-01-01T03:59:59Z"
    assert payload["series"]["equity_curve"][0]["time"] == "2024-01-01T03:59:59Z"
    assert payload["trades"][0]["trade_id"] == 1
    assert payload["markers"][0]["trade_id"] == 1


def test_run_endpoint_allows_last_warmup_signal_to_open_first_in_range_bar(client, tmp_path: Path) -> None:
    service = _build_service(
        tmp_path / "warmup-entry.duckdb",
        seed_market_data=True,
        kline_rows=_build_warmup_entry_kline_rows(),
    )

    with _override_service(client, service):
        response = client.post("/api/backtests/run", json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json()["trades"][0]["entry_time"] == "2024-01-01T03:00:00Z"


def test_run_endpoint_wraps_unexpected_engine_error(client, monkeypatch, tmp_path: Path) -> None:
    service = _build_service(tmp_path / "engine-error.duckdb", seed_market_data=True)

    def raise_runtime_error(*args, **kwargs) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "backend.app.services.backtest_service.run_backtest",
        raise_runtime_error,
    )

    with _override_service(client, service):
        response = client.post("/api/backtests/run", json=VALID_REQUEST)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "backtest_failed"
