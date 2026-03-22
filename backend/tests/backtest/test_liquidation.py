import pytest

from backend.app.backtest.contracts import BacktestRequest, MarketDataBundle
from backend.app.backtest.engine import run_backtest
from backend.app.backtest.liquidation import calculate_liquidation_price
from backend.tests.backtest.test_engine import StaticSignalPlugin, _make_funding, _make_klines


def test_calculate_liquidation_price_for_long_and_short() -> None:
    assert calculate_liquidation_price("long", 100.0, 10.0, 100.0, 0.005) == pytest.approx(90.4522613065, rel=1e-9)
    assert calculate_liquidation_price("short", 100.0, 10.0, 100.0, 0.005) == pytest.approx(109.4527363184, rel=1e-9)


def test_liquidation_stops_run_and_sets_actual_end() -> None:
    StaticSignalPlugin.signal_values = [1, 1]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 101.0, "low": 90.0, "close": 95.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T01:59:59Z",
        initial_capital=1000.0,
        leverage=10.0,
        position_size_pct=1.0,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert result.run.status == "liquidated"
    assert result.run.actual_end.isoformat() == "2024-01-01T01:00:00+00:00"
    assert result.run.final_equity == pytest.approx(45.2261306533, rel=1e-6)
