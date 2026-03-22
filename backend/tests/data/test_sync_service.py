import anyio
import httpx

from backend.app.data.repository import DuckDbRepository
from backend.app.data.sync_service import DataSyncService, SyncFailedError
from backend.app.models.data_sync import DataSyncRequest


class RetryOnceBinanceClient:
    def __init__(self) -> None:
        self.kline_calls = 0

    async def fetch_klines(self, **_: object) -> list[dict[str, object]]:
        self.kline_calls += 1
        if self.kline_calls == 1:
            raise RuntimeError("429: retry me")
        return [
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "open_time": "2024-01-01T00:00:00Z",
                "close_time": "2024-01-01T00:59:59Z",
                "open": 42000.0,
                "high": 42100.0,
                "low": 41950.0,
                "close": 42050.0,
                "volume": 100.0,
            }
        ]

    async def fetch_funding_rates(self, **_: object) -> list[dict[str, object]]:
        return [
            {
                "symbol": "BTCUSDT",
                "funding_time": "2024-01-01T00:00:00Z",
                "funding_rate": 0.0001,
            }
        ]


class NoDataBinanceClient:
    async def fetch_klines(self, **_: object) -> list[dict[str, object]]:
        return []

    async def fetch_funding_rates(self, **_: object) -> list[dict[str, object]]:
        return []


class FundingFailureBinanceClient:
    async def fetch_klines(self, **_: object) -> list[dict[str, object]]:
        return [
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "open_time": "2024-01-01T00:00:00Z",
                "close_time": "2024-01-01T00:59:59Z",
                "open": 42000.0,
                "high": 42100.0,
                "low": 41950.0,
                "close": 42050.0,
                "volume": 100.0,
            }
        ]

    async def fetch_funding_rates(self, **_: object) -> list[dict[str, object]]:
        raise RuntimeError("500: funding fetch failed")


class TransportFailureBinanceClient:
    async def fetch_klines(self, **_: object) -> list[dict[str, object]]:
        request = httpx.Request("GET", "https://fapi.binance.com/fapi/v1/klines")
        raise httpx.ConnectError("network unreachable", request=request)

    async def fetch_funding_rates(self, **_: object) -> list[dict[str, object]]:
        return []


class HttpxRetryBinanceClient:
    def __init__(self) -> None:
        self.kline_calls = 0

    async def fetch_klines(self, **_: object) -> list[dict[str, object]]:
        self.kline_calls += 1
        if self.kline_calls == 1:
            request = httpx.Request("GET", "https://fapi.binance.com/fapi/v1/klines")
            response = httpx.Response(status_code=429, request=request)
            raise httpx.HTTPStatusError("429 Too Many Requests", request=request, response=response)
        return [
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "open_time": "2024-01-01T00:00:00Z",
                "close_time": "2024-01-01T00:59:59Z",
                "open": 42000.0,
                "high": 42100.0,
                "low": 41950.0,
                "close": 42050.0,
                "volume": 100.0,
            }
        ]

    async def fetch_funding_rates(self, **_: object) -> list[dict[str, object]]:
        return [
            {
                "symbol": "BTCUSDT",
                "funding_time": "2024-01-01T00:00:00Z",
                "funding_rate": 0.0001,
            }
        ]


class AlwaysRetryableBinanceClient:
    async def fetch_klines(self, **_: object) -> list[dict[str, object]]:
        raise RuntimeError("429: retry me")

    async def fetch_funding_rates(self, **_: object) -> list[dict[str, object]]:
        return []


REQUEST = DataSyncRequest(
    strategy_id="sma_cross",
    symbol="BTCUSDT",
    timeframe="1h",
    start="2024-01-01T00:00:00Z",
    end="2024-01-01T00:59:59Z",
)


def test_sync_service_retries_and_upserts_without_duplicates(tmp_path) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()
    service = DataSyncService(
        repository=repository,
        binance_client=RetryOnceBinanceClient(),
        strategy_lookback_by_id={"sma_cross": 0},
        retry_delays=[0, 0, 0, 0, 0],
    )

    result = anyio.run(service.sync_market_data, REQUEST)

    assert result.status == "completed"
    assert repository.count_rows("klines") == 1


def test_sync_service_retries_http_status_errors(tmp_path) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()
    service = DataSyncService(
        repository=repository,
        binance_client=HttpxRetryBinanceClient(),
        strategy_lookback_by_id={"sma_cross": 0},
        retry_delays=[0, 0, 0, 0, 0],
    )

    result = anyio.run(service.sync_market_data, REQUEST)

    assert result.status == "completed"
    assert repository.count_rows("klines") == 1


def test_sync_service_returns_no_data_available(tmp_path) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()
    service = DataSyncService(
        repository=repository,
        binance_client=NoDataBinanceClient(),
        strategy_lookback_by_id={"sma_cross": 0},
        retry_delays=[0, 0, 0, 0, 0],
    )

    result = anyio.run(service.sync_market_data, REQUEST)

    assert result.status == "no_data_available"
    assert result.coverage.complete is False


def test_sync_service_returns_sync_failed_when_funding_fetch_breaks(tmp_path) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()
    service = DataSyncService(
        repository=repository,
        binance_client=FundingFailureBinanceClient(),
        strategy_lookback_by_id={"sma_cross": 0},
        retry_delays=[0, 0, 0, 0, 0],
    )

    result = anyio.run(service.sync_market_data, REQUEST)

    assert result.status == "sync_failed"
    assert result.error is not None
    assert result.error.code == "sync_failed"


def test_sync_service_returns_sync_failed_on_transport_errors(tmp_path) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()
    service = DataSyncService(
        repository=repository,
        binance_client=TransportFailureBinanceClient(),
        strategy_lookback_by_id={"sma_cross": 0},
        retry_delays=[0, 0, 0, 0, 0],
    )

    result = anyio.run(service.sync_market_data, REQUEST)

    assert result.status == "sync_failed"
    assert result.error is not None
    assert result.error.code == "sync_failed"


def test_sync_service_skips_sleep_after_final_retry(tmp_path, monkeypatch) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()
    service = DataSyncService(
        repository=repository,
        binance_client=AlwaysRetryableBinanceClient(),
        strategy_lookback_by_id={"sma_cross": 0},
        retry_delays=[1, 2, 4],
    )
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("backend.app.data.sync_service.anyio.sleep", fake_sleep)

    result = anyio.run(service.sync_market_data, REQUEST)

    assert result.status == "sync_failed"
    assert sleeps == [1, 2]
