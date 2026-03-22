from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from pydantic import field_validator, model_validator

from backend.app.models.common import JsonDict
from backend.app.models.data_sync import CoverageStatusResponse


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: JsonDict = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


def build_error_envelope(
    *,
    code: str,
    message: str,
    details: JsonDict | None = None,
) -> ErrorEnvelope:
    return ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or {},
        )
    )


class BacktestRunRequest(BaseModel):
    strategy_id: str
    symbol: Literal["BTCUSDT"]
    timeframe: Literal["15m", "1h", "4h", "1d"]
    start: str
    end: str
    initial_capital: float = Field(gt=0)
    leverage: float = Field(ge=1, le=20)
    fee_bps: float = Field(ge=0, le=100)
    slippage_bps: float = Field(ge=0, le=100)
    position_size_pct: float = Field(gt=0, le=1)
    params: JsonDict

    @field_validator("strategy_id")
    @classmethod
    def validate_strategy_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("strategy_id must not be empty")
        return normalized

    @field_validator("start", "end")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timestamp must include a timezone offset")
        return value

    @model_validator(mode="after")
    def validate_range(self):
        start = datetime.fromisoformat(self.start.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.end.replace("Z", "+00:00"))
        if end <= start:
            raise ValueError("end must be greater than start")
        return self


class BacktestRunInfo(BaseModel):
    symbol: str
    strategy_id: str
    timeframe: str
    start: str
    end: str
    effective_start: str
    effective_end: str
    actual_end: str
    status: Literal["completed", "liquidated"]


class BacktestStrategySummary(BaseModel):
    id: str
    name: str
    description: str


class BacktestSettings(BaseModel):
    initial_capital: float
    leverage: float
    fee_bps: float
    slippage_bps: float
    position_size_pct: float


class BacktestMetricsResponse(BaseModel):
    net_pnl: float
    return_pct: float
    annualized_return: float | None
    max_drawdown: float | None
    sharpe: float | None
    sortino: float | None
    calmar: float | None
    total_trades: int
    win_rate: float | None
    profit_factor: float | None
    average_trade_return: float | None
    average_holding_time_seconds: float | None


class MarketBar(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class EquityPoint(BaseModel):
    time: str
    equity: float


class DrawdownPoint(BaseModel):
    time: str
    drawdown: float


class BacktestSeries(BaseModel):
    market_bars: list[MarketBar]
    equity_curve: list[EquityPoint]
    drawdown_curve: list[DrawdownPoint]


class MonthlyReturnRow(BaseModel):
    month: str
    return_pct: float


class TradeRow(BaseModel):
    trade_id: int
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    allocated_margin_at_entry: float
    notional: float
    gross_pnl: float
    fees: float
    funding_pnl: float
    net_pnl: float
    return_pct_on_margin: float
    holding_bars: int
    holding_seconds: float
    exit_reason: str


class MarkerRow(BaseModel):
    time: str
    price: float
    action: str
    trade_id: int


class BacktestRunResponse(BaseModel):
    run: BacktestRunInfo
    strategy: BacktestStrategySummary
    settings: BacktestSettings
    metrics: BacktestMetricsResponse
    series: BacktestSeries
    monthly_returns: list[MonthlyReturnRow]
    trades: list[TradeRow]
    markers: list[MarkerRow]
    coverage: CoverageStatusResponse
