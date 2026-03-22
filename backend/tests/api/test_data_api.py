from pathlib import Path

from backend.app.api import data as data_api
from backend.app.models.data_sync import (
    CoverageRange,
    CoverageSection,
    CoverageStatusResponse,
    DataSyncResponse,
    DownloadedRows,
    SyncError,
)


class FakeDataService:
    def get_status(self, request):
        return CoverageStatusResponse(
            symbol=request.symbol,
            strategy_id=request.strategy_id,
            timeframe=request.timeframe,
            requested_start=request.start,
            requested_end=request.end,
            effective_start="2024-01-01T00:00:00Z",
            effective_end="2024-01-03T23:00:00Z",
            complete=False,
            kline=CoverageSection(
                cached_start=None,
                cached_end=None,
                missing_ranges=[CoverageRange(start="2023-12-23T16:00:00Z", end="2024-01-03T23:00:00Z")],
            ),
            funding=CoverageSection(
                cached_start=None,
                cached_end=None,
                missing_ranges=[CoverageRange(start="2024-01-01T00:00:00Z", end="2024-01-03T16:00:00Z")],
            ),
        )

    async def sync_market_data(self, request):
        return DataSyncResponse(
            status="no_data_available",
            symbol=request.symbol,
            strategy_id=request.strategy_id,
            timeframe=request.timeframe,
            requested_start=request.start,
            requested_end=request.end,
            effective_start="2024-01-01T00:00:00Z",
            effective_end="2024-01-03T23:00:00Z",
            complete=False,
            downloaded=DownloadedRows(kline_rows=0, funding_rows=0),
            coverage=self.get_status(request),
        )


class FailingDataService(FakeDataService):
    async def sync_market_data(self, request):
        return DataSyncResponse(
            status="sync_failed",
            symbol=request.symbol,
            strategy_id=request.strategy_id,
            timeframe=request.timeframe,
            requested_start=request.start,
            requested_end=request.end,
            effective_start="2024-01-01T00:00:00Z",
            effective_end="2024-01-03T23:00:00Z",
            complete=False,
            downloaded=DownloadedRows(kline_rows=1, funding_rows=0),
            coverage=self.get_status(request),
            error=SyncError(code="sync_failed", message="Market data coverage remained incomplete after sync."),
        )


class UnknownStrategyDataService:
    def get_status(self, request):
        raise data_api.StrategyNotFoundError(request.strategy_id)

    async def sync_market_data(self, request):
        raise data_api.StrategyNotFoundError(request.strategy_id)


def test_status_endpoint_returns_nested_coverage_shape(client, monkeypatch) -> None:
    monkeypatch.setattr(data_api, "get_data_service", lambda: FakeDataService())

    response = client.get(
        "/api/data/status",
        params={
            "strategy_id": "sma_cross",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["kline"]["missing_ranges"][0]["start"] == "2023-12-23T16:00:00Z"


def test_sync_endpoint_returns_no_data_available_without_triggering_run(client, monkeypatch) -> None:
    monkeypatch.setattr(data_api, "get_data_service", lambda: FakeDataService())

    response = client.post(
        "/api/data/sync",
        json={
            "strategy_id": "sma_cross",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "no_data_available"
    assert response.json()["coverage"]["complete"] is False


def test_sync_endpoint_returns_sync_failed_error(client, monkeypatch) -> None:
    monkeypatch.setattr(data_api, "get_data_service", lambda: FailingDataService())

    response = client.post(
        "/api/data/sync",
        json={
            "strategy_id": "sma_cross",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "sync_failed"
    assert response.json()["error"]["code"] == "sync_failed"


def test_status_endpoint_rejects_unknown_strategy(client, monkeypatch) -> None:
    monkeypatch.setattr(data_api, "get_data_service", lambda: UnknownStrategyDataService())

    response = client.get(
        "/api/data/status",
        params={
            "strategy_id": "unknown_strategy",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "strategy_not_found"


def test_sync_endpoint_rejects_unknown_strategy(client, monkeypatch) -> None:
    monkeypatch.setattr(data_api, "get_data_service", lambda: UnknownStrategyDataService())

    response = client.post(
        "/api/data/sync",
        json={
            "strategy_id": "unknown_strategy",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "strategy_not_found"


def test_sync_endpoint_rejects_invalid_time_inputs(client) -> None:
    response = client.post(
        "/api/data/sync",
        json={
            "strategy_id": "sma_cross",
            "symbol": "BTCUSDT",
            "timeframe": "2h",
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-03T23:59:59Z",
        },
    )

    assert response.status_code == 422


def test_sync_endpoint_rejects_empty_identifiers(client) -> None:
    response = client.post(
        "/api/data/sync",
        json={
            "strategy_id": "",
            "symbol": "",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z",
        },
    )

    assert response.status_code == 422


def test_get_data_service_uses_project_root_database_path(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, Path] = {}

    class FakeRepository:
        def __init__(self, database_path: Path) -> None:
            captured["path"] = database_path

        def initialize_schema(self) -> None:
            return None

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(data_api, "DuckDbRepository", FakeRepository)
    monkeypatch.setattr(data_api, "BinancePublicClient", lambda: object())
    monkeypatch.setattr(data_api, "discover_strategies", lambda _: ([], []))
    data_api.get_data_service.cache_clear()

    data_api.get_data_service()

    assert captured["path"] == Path(data_api.__file__).resolve().parents[3] / "quantitative_backtesting.duckdb"
    data_api.get_data_service.cache_clear()
