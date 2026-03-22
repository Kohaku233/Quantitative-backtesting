from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from backend.app.backtest.contracts import BacktestRequest, MarketDataBundle
from backend.app.backtest.engine import run_backtest
from backend.app.backtest.analytics import build_metrics
from backend.app.strategies.base import BaseStrategyPlugin, StrategyExecutionError


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _make_klines(rows: list[dict[str, float | str]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
    frame = frame.set_index("open_time")
    frame.index.name = "open_time"
    return frame


def _make_funding(rows: list[dict[str, float | str]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["funding_rate"], index=pd.DatetimeIndex([], tz=UTC, name="funding_time"))
    frame = pd.DataFrame(rows)
    frame["funding_time"] = pd.to_datetime(frame["funding_time"], utc=True)
    frame = frame.set_index("funding_time")
    frame.index.name = "funding_time"
    return frame


class StaticSignalPlugin(BaseStrategyPlugin):
    id = "static"
    name = "Static"
    description = "Static signal plugin for engine tests."
    supported_timeframes = ("1h",)
    required_lookback_bars = 0
    parameter_schema: list[dict[str, object]] = []
    signal_values: list[int] = []

    @classmethod
    def validate_params(cls, params):
        return {}

    @classmethod
    def compute_indicators(cls, df: pd.DataFrame, params):
        return pd.DataFrame(index=df.index)

    @classmethod
    def generate_signals(cls, df: pd.DataFrame, indicators: pd.DataFrame, params):
        return pd.Series(cls.signal_values, index=df.index, dtype="int8")


class MalformedSignalPlugin(StaticSignalPlugin):
    id = "malformed"

    @classmethod
    def generate_signals(cls, df: pd.DataFrame, indicators: pd.DataFrame, params):
        return pd.Series([2] * len(df), index=df.index, dtype="int8")


class FractionalSignalPlugin(StaticSignalPlugin):
    id = "fractional"

    @classmethod
    def generate_signals(cls, df: pd.DataFrame, indicators: pd.DataFrame, params):
        return pd.Series([0.5] * len(df), index=df.index, dtype="float64")


def test_engine_executes_on_next_bar_open_and_applies_costs() -> None:
    StaticSignalPlugin.signal_values = [1, 0, 0]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 105.0, "low": 99.0, "close": 104.0, "volume": 10.0},
                {"open_time": "2024-01-01T02:00:00Z", "close_time": "2024-01-01T02:59:59Z", "open": 104.0, "high": 106.0, "low": 103.0, "close": 105.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T02:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.04,
        fee_bps=10.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert result.trades[0].entry_time.isoformat() == "2024-01-01T01:00:00+00:00"
    assert result.trades[0].fees == pytest.approx(0.816, rel=1e-6)
    assert result.run.effective_start.isoformat() == "2024-01-01T00:00:00+00:00"
    assert result.run.effective_end.isoformat() == "2024-01-01T02:00:00+00:00"
    assert result.bar_snapshots[1].open == 100.0
    assert result.bar_snapshots[1].high == 105.0
    assert result.bar_snapshots[1].low == 99.0
    assert result.bar_snapshots[1].close == 104.0
    assert result.bar_snapshots[1].equity == pytest.approx(10015.6, rel=1e-6)
    assert [marker.kind for marker in result.markers] == ["entry_long", "exit_long"]


def test_engine_flips_using_post_close_equity() -> None:
    StaticSignalPlugin.signal_values = [1, -1, 0, 0]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 111.0, "low": 99.0, "close": 110.0, "volume": 10.0},
                {"open_time": "2024-01-01T02:00:00Z", "close_time": "2024-01-01T02:59:59Z", "open": 110.0, "high": 111.0, "low": 108.0, "close": 109.0, "volume": 10.0},
                {"open_time": "2024-01-01T03:00:00Z", "close_time": "2024-01-01T03:59:59Z", "open": 109.0, "high": 109.0, "low": 105.0, "close": 106.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T03:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert result.trades[0].exit_reason == "signal_flip"
    assert result.trades[1].allocated_margin_at_entry == pytest.approx(1010.0, rel=1e-6)


def test_funding_and_bar_open_ordering_follow_spec() -> None:
    StaticSignalPlugin.signal_values = [1, 0, 0]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0, "volume": 10.0},
                {"open_time": "2024-01-01T02:00:00Z", "close_time": "2024-01-01T02:59:59Z", "open": 101.0, "high": 102.0, "low": 100.0, "close": 101.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding(
            [
                {"funding_time": "2024-01-01T02:00:00Z", "funding_rate": 0.01},
            ]
        ),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T02:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert result.funding_events[0].applied_before_open_fill is True
    assert result.trades[0].funding_pnl == pytest.approx(-10.2, rel=1e-6)


def test_engine_forces_close_at_final_bar_and_uses_terminal_close_for_actual_end() -> None:
    StaticSignalPlugin.signal_values = [1, 1]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 106.0, "low": 99.0, "close": 105.0, "volume": 10.0},
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
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert result.run.status == "completed"
    assert result.run.actual_end.isoformat() == "2024-01-01T01:59:59+00:00"
    assert result.trades[-1].exit_reason == "end_of_range"


def test_engine_rejects_malformed_signal_series() -> None:
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="malformed",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T01:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    with pytest.raises(StrategyExecutionError):
        run_backtest(dataset=dataset, plugin=MalformedSignalPlugin, request=request)


def test_engine_rejects_fractional_signal_series() -> None:
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="fractional",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T01:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    with pytest.raises(StrategyExecutionError):
        run_backtest(dataset=dataset, plugin=FractionalSignalPlugin, request=request)


def test_engine_allows_empty_trade_set_and_returns_full_result() -> None:
    StaticSignalPlugin.signal_values = [0, 0, 0]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T02:00:00Z", "close_time": "2024-01-01T02:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T02:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)
    metrics = build_metrics(result)

    assert result.trades == []
    assert metrics.total_trades == 0


def test_same_side_repeat_signals_do_not_create_new_trade() -> None:
    StaticSignalPlugin.signal_values = [1, 1, 0, 0]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0, "volume": 10.0},
                {"open_time": "2024-01-01T02:00:00Z", "close_time": "2024-01-01T02:59:59Z", "open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0, "volume": 10.0},
                {"open_time": "2024-01-01T03:00:00Z", "close_time": "2024-01-01T03:59:59Z", "open": 102.0, "high": 102.0, "low": 100.0, "close": 101.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T03:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert len(result.trades) == 1


def test_flat_signal_while_flat_keeps_balances_unchanged() -> None:
    StaticSignalPlugin.signal_values = [0, 0, 0]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T02:00:00Z", "close_time": "2024-01-01T02:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T02:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert all(snapshot.free_cash == 10000.0 for snapshot in result.bar_snapshots)
    assert all(snapshot.isolated_margin_balance == 0.0 for snapshot in result.bar_snapshots)
    assert all(snapshot.equity == 10000.0 for snapshot in result.bar_snapshots)


def test_funding_uses_latest_close_at_or_before_timestamp() -> None:
    StaticSignalPlugin.signal_values = [1, 1, 0]
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T00:59:59Z", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 10.0},
                {"open_time": "2024-01-01T01:00:00Z", "close_time": "2024-01-01T01:59:59Z", "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0, "volume": 10.0},
                {"open_time": "2024-01-01T02:00:00Z", "close_time": "2024-01-01T02:59:59Z", "open": 102.0, "high": 104.0, "low": 101.0, "close": 103.0, "volume": 10.0},
            ]
        ),
        funding_rates=_make_funding(
            [
                {"funding_time": "2024-01-01T02:30:00Z", "funding_rate": 0.01},
            ]
        ),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T02:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    result = run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)

    assert result.funding_events[0].reference_price == 102.0


def test_engine_rejects_empty_market_data_bundle() -> None:
    empty_klines = pd.DataFrame(
        columns=["close_time", "open", "high", "low", "close", "volume"],
        index=pd.DatetimeIndex([], tz=UTC, name="open_time"),
    )
    empty_klines["close_time"] = pd.to_datetime(empty_klines["close_time"], utc=True)
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1h",
        klines=empty_klines,
        funding_rates=_make_funding([]),
    )
    request = BacktestRequest(
        strategy_id="static",
        symbol="BTCUSDT",
        timeframe="1h",
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T00:59:59Z",
        initial_capital=10000.0,
        leverage=1.0,
        position_size_pct=0.1,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )

    with pytest.raises(StrategyExecutionError):
        run_backtest(dataset=dataset, plugin=StaticSignalPlugin, request=request)
