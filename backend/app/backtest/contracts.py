from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

import pandas as pd


PositionSide = Literal["long", "short"]
RunStatus = Literal["completed", "liquidated"]


@dataclass(slots=True)
class BacktestRequest:
    strategy_id: str
    symbol: str
    timeframe: str
    start: str
    end: str
    initial_capital: float
    leverage: float
    position_size_pct: float
    fee_bps: float
    slippage_bps: float
    params: dict[str, object]
    maintenance_margin_rate: float = 0.005


@dataclass(slots=True)
class MarketDataBundle:
    symbol: str
    timeframe: str
    klines: pd.DataFrame
    funding_rates: pd.DataFrame


@dataclass(slots=True)
class FundingEvent:
    timestamp: datetime
    funding_rate: float
    reference_price: float
    cash_flow: float
    applied_before_open_fill: bool


@dataclass(slots=True)
class TradeRecord:
    side: PositionSide
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    allocated_margin_at_entry: float
    gross_pnl: float
    fees: float
    funding_pnl: float
    net_pnl: float
    return_pct_on_margin: float
    holding_bars: int
    holding_seconds: float
    exit_reason: str
    trade_id: int
    notional: float


@dataclass(slots=True)
class BarSnapshot:
    timestamp: datetime
    free_cash: float
    isolated_margin_balance: float
    unrealized_pnl: float
    equity: float
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


@dataclass(slots=True)
class RunSummary:
    status: RunStatus
    actual_end: datetime
    final_equity: float
    effective_start: datetime | None = None
    effective_end: datetime | None = None


@dataclass(slots=True)
class Marker:
    timestamp: datetime
    price: float
    kind: str


@dataclass(slots=True)
class BacktestExecutionResult:
    request: BacktestRequest
    dataset: MarketDataBundle
    run: RunSummary
    bar_snapshots: list[BarSnapshot]
    trades: list[TradeRecord]
    funding_events: list[FundingEvent]
    markers: list[Marker] = field(default_factory=list)


@dataclass(slots=True)
class BacktestMetrics:
    total_trades: int
    total_return: float
    net_pnl: float
    return_pct: float
    annualized_return: float | None
    max_drawdown: float | None
    sharpe: float | None
    sortino: float | None
    calmar: float | None
    win_rate: float | None
    profit_factor: float | None
    average_trade_return: float | None
    average_holding_time_seconds: float | None
    average_holding_bars: float | None


@dataclass(slots=True)
class SeriesPoint:
    timestamp: datetime
    value: float


@dataclass(slots=True)
class MonthlyReturn:
    month: str
    return_pct: float
