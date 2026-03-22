from datetime import UTC, datetime

import pytest

from backend.app.backtest.analytics import build_metrics
from backend.app.backtest.contracts import (
    BacktestExecutionResult,
    BacktestRequest,
    BarSnapshot,
    FundingEvent,
    MarketDataBundle,
    RunSummary,
    TradeRecord,
)
from backend.tests.backtest.test_engine import _make_funding, _make_klines


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def test_analytics_computes_sharpe_drawdown_and_average_trade_return() -> None:
    request = BacktestRequest(
        strategy_id="analytics",
        symbol="BTCUSDT",
        timeframe="1d",
        start="2024-01-01T00:00:00Z",
        end="2024-01-04T23:59:59Z",
        initial_capital=100.0,
        leverage=1.0,
        position_size_pct=1.0,
        fee_bps=0.0,
        slippage_bps=0.0,
        params={},
    )
    dataset = MarketDataBundle(
        symbol="BTCUSDT",
        timeframe="1d",
        klines=_make_klines(
            [
                {"open_time": "2024-01-01T00:00:00Z", "close_time": "2024-01-01T23:59:59Z", "open": 100.0, "high": 110.0, "low": 99.0, "close": 110.0, "volume": 1.0},
                {"open_time": "2024-01-02T00:00:00Z", "close_time": "2024-01-02T23:59:59Z", "open": 110.0, "high": 111.0, "low": 99.0, "close": 100.0, "volume": 1.0},
                {"open_time": "2024-01-03T00:00:00Z", "close_time": "2024-01-03T23:59:59Z", "open": 100.0, "high": 106.0, "low": 99.0, "close": 105.0, "volume": 1.0},
                {"open_time": "2024-01-04T00:00:00Z", "close_time": "2024-01-04T23:59:59Z", "open": 105.0, "high": 105.0, "low": 105.0, "close": 105.0, "volume": 1.0},
            ]
        ),
        funding_rates=_make_funding([]),
    )
    result = BacktestExecutionResult(
        request=request,
        dataset=dataset,
        run=RunSummary(
            status="completed",
            effective_start=_dt("2024-01-01T00:00:00Z"),
            effective_end=_dt("2024-01-04T00:00:00Z"),
            actual_end=_dt("2024-01-04T23:59:59Z"),
            final_equity=105.0,
        ),
        bar_snapshots=[
            BarSnapshot(timestamp=_dt("2024-01-01T23:59:59Z"), open=100.0, high=110.0, low=99.0, close=110.0, volume=1.0, free_cash=110.0, isolated_margin_balance=0.0, unrealized_pnl=0.0, equity=110.0),
            BarSnapshot(timestamp=_dt("2024-01-02T23:59:59Z"), open=110.0, high=111.0, low=99.0, close=100.0, volume=1.0, free_cash=100.0, isolated_margin_balance=0.0, unrealized_pnl=0.0, equity=100.0),
            BarSnapshot(timestamp=_dt("2024-01-03T23:59:59Z"), open=100.0, high=106.0, low=99.0, close=105.0, volume=1.0, free_cash=105.0, isolated_margin_balance=0.0, unrealized_pnl=0.0, equity=105.0),
            BarSnapshot(timestamp=_dt("2024-01-04T23:59:59Z"), open=105.0, high=105.0, low=105.0, close=105.0, volume=1.0, free_cash=105.0, isolated_margin_balance=0.0, unrealized_pnl=0.0, equity=105.0),
        ],
        trades=[
            TradeRecord(
                trade_id=1,
                side="long",
                entry_time=_dt("2024-01-01T00:00:00Z"),
                exit_time=_dt("2024-01-02T00:00:00Z"),
                entry_price=100.0,
                exit_price=105.0,
                quantity=1.0,
                notional=100.0,
                allocated_margin_at_entry=100.0,
                gross_pnl=5.0,
                fees=0.0,
                funding_pnl=0.0,
                net_pnl=5.0,
                return_pct_on_margin=0.05,
                holding_bars=1,
                holding_seconds=86400,
                exit_reason="signal_flat",
            ),
            TradeRecord(
                trade_id=2,
                side="short",
                entry_time=_dt("2024-01-03T00:00:00Z"),
                exit_time=_dt("2024-01-04T00:00:00Z"),
                entry_price=105.0,
                exit_price=107.1,
                quantity=1.0,
                notional=105.0,
                allocated_margin_at_entry=105.0,
                gross_pnl=-2.1,
                fees=0.0,
                funding_pnl=0.0,
                net_pnl=-2.1,
                return_pct_on_margin=-0.02,
                holding_bars=1,
                holding_seconds=86400,
                exit_reason="signal_flip",
            ),
        ],
        funding_events=[],
    )

    metrics = build_metrics(result)

    assert metrics.net_pnl == 5.0
    assert metrics.return_pct == 0.05
    assert metrics.max_drawdown == -0.09090909090909091
    assert metrics.sharpe == pytest.approx(-3.6468609984067673, rel=1e-12)
    assert metrics.average_trade_return == pytest.approx(0.015, rel=1e-12)
    assert metrics.win_rate == 0.5
    assert metrics.profit_factor == pytest.approx(2.380952380952381, rel=1e-12)
    assert metrics.average_holding_time_seconds == 86400.0
    assert metrics.annualized_return == pytest.approx(84.80826776414045, rel=1e-12)
