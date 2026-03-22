from pathlib import Path

from backend.app.data.repository import DuckDbRepository
from backend.app.models.data_sync import DataSyncRequest


def test_repository_reports_missing_ranges_with_warmup_scope(tmp_path: Path) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()

    coverage = repository.get_coverage(
        request=DataSyncRequest(
            strategy_id="sma_cross",
            symbol="BTCUSDT",
            timeframe="1h",
            start="2024-01-01T00:00:00Z",
            end="2024-01-03T23:59:59Z",
        ),
        required_lookback_bars=200,
    )

    assert coverage.complete is False
    assert coverage.effective_start == "2024-01-01T00:00:00Z"
    assert coverage.effective_end == "2024-01-03T23:00:00Z"
    assert coverage.kline.missing_ranges[0].start == "2023-12-23T16:00:00Z"
    assert coverage.funding.missing_ranges[0].start == "2024-01-01T00:00:00Z"


def test_repository_upserts_duplicate_kline_rows(tmp_path: Path) -> None:
    repository = DuckDbRepository(tmp_path / "backtests.duckdb")
    repository.initialize_schema()

    row = {
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
    repository.upsert_klines([row, row])

    assert repository.count_rows("klines") == 1
