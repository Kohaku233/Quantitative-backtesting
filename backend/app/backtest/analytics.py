from __future__ import annotations

from datetime import UTC, datetime
from math import fsum, isfinite, sqrt

from backend.app.backtest.contracts import (
    BacktestExecutionResult,
    BacktestMetrics,
    MonthlyReturn,
    SeriesPoint,
)


_PERIODS_PER_YEAR = {
    "15m": 35040.0,
    "1h": 8760.0,
    "4h": 2190.0,
    "1d": 365.0,
}


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _equity_curve(result: BacktestExecutionResult) -> list[float]:
    return [snapshot.equity for snapshot in result.bar_snapshots]


def _returns(values: list[float]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(values, values[1:], strict=False):
        if previous <= 0 or current <= 0:
            continue
        returns.append((current / previous) - 1.0)
    return returns


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return fsum(values) / len(values)


def _sample_stddev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = fsum(values) / len(values)
    variance = fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return sqrt(variance)


def _downside_stddev(values: list[float]) -> float | None:
    downside = [min(value, 0.0) for value in values]
    if len(downside) < 2:
        return None
    stddev = _sample_stddev(downside)
    if stddev in (None, 0.0) or not isfinite(stddev):
        return None
    return stddev


def _annualized_return(total_return: float, actual_end: datetime, start: datetime) -> float | None:
    elapsed_seconds = (actual_end - start).total_seconds()
    if elapsed_seconds <= 0:
        return None
    if 1.0 + total_return <= 0:
        return -1.0
    year_fraction = elapsed_seconds / (365.0 * 24.0 * 3600.0)
    return (1.0 + total_return) ** (1.0 / year_fraction) - 1.0


def _max_drawdown(values: list[float]) -> float | None:
    if not values:
        return None
    peak = values[0]
    max_drawdown = 0.0
    for value in values[1:]:
        if value > peak:
            peak = value
            continue
        if peak > 0:
            drawdown = (value - peak) / peak
            if drawdown < max_drawdown:
                max_drawdown = drawdown
    return max_drawdown


def _average_trade_return(result: BacktestExecutionResult) -> float | None:
    if not result.trades:
        return None
    return fsum(trade.return_pct_on_margin for trade in result.trades) / len(result.trades)


def _average_holding_bars(result: BacktestExecutionResult) -> float | None:
    if not result.trades:
        return None
    return fsum(trade.holding_bars for trade in result.trades) / len(result.trades)


def _average_holding_time_seconds(result: BacktestExecutionResult) -> float | None:
    if not result.trades:
        return None
    return fsum(trade.holding_seconds for trade in result.trades) / len(result.trades)


def _win_rate(result: BacktestExecutionResult) -> float | None:
    if not result.trades:
        return None
    winners = sum(1 for trade in result.trades if trade.net_pnl > 0)
    return winners / len(result.trades)


def _profit_factor(result: BacktestExecutionResult) -> float | None:
    gross_profit = fsum(trade.net_pnl for trade in result.trades if trade.net_pnl > 0)
    gross_loss = fsum(trade.net_pnl for trade in result.trades if trade.net_pnl < 0)
    if gross_loss == 0:
        return None
    return gross_profit / abs(gross_loss)


def build_equity_series(result: BacktestExecutionResult) -> list[SeriesPoint]:
    return [SeriesPoint(timestamp=snapshot.timestamp, value=snapshot.equity) for snapshot in result.bar_snapshots]


def build_drawdown_series(result: BacktestExecutionResult) -> list[SeriesPoint]:
    series: list[SeriesPoint] = []
    peak: float | None = None
    for snapshot in result.bar_snapshots:
        peak = snapshot.equity if peak is None else max(peak, snapshot.equity)
        drawdown = 0.0 if peak == 0 else (snapshot.equity - peak) / peak
        series.append(SeriesPoint(timestamp=snapshot.timestamp, value=drawdown))
    return series


def build_monthly_returns(result: BacktestExecutionResult) -> list[MonthlyReturn]:
    if not result.bar_snapshots:
        return []

    grouped: dict[str, list[SeriesPoint]] = {}
    equity_series = build_equity_series(result)
    for point in equity_series:
        month_key = point.timestamp.strftime("%Y-%m")
        grouped.setdefault(month_key, []).append(point)

    monthly_returns: list[MonthlyReturn] = []
    previous_close = result.request.initial_capital
    for month_key in sorted(grouped):
        month_points = grouped[month_key]
        open_equity = previous_close
        close_equity = month_points[-1].value
        monthly_returns.append(MonthlyReturn(month=month_key, return_pct=(close_equity / open_equity) - 1.0))
        previous_close = close_equity
    return monthly_returns


def build_metrics(result: BacktestExecutionResult) -> BacktestMetrics:
    equity_curve = _equity_curve(result)
    returns = _returns(equity_curve)
    net_pnl = result.run.final_equity - result.request.initial_capital
    total_return = (net_pnl / result.request.initial_capital) if result.request.initial_capital else 0.0
    max_drawdown = _max_drawdown(equity_curve)
    sharpe = None
    sortino = None
    periods_per_year = _PERIODS_PER_YEAR[result.request.timeframe]
    if returns:
        return_mean = _mean(returns)
        return_stddev = _sample_stddev(returns)
        downside_deviation = _downside_stddev(returns)
        if return_mean is not None and return_stddev not in (None, 0.0) and isfinite(return_stddev):
            sharpe = (return_mean / return_stddev) * sqrt(periods_per_year)
        if return_mean is not None and downside_deviation is not None:
            sortino = (return_mean / downside_deviation) * sqrt(periods_per_year)

    annualized_return = _annualized_return(
        total_return,
        result.run.actual_end,
        result.run.effective_start or _parse_datetime(result.request.start),
    )
    calmar = None
    if annualized_return is not None and max_drawdown not in (None, 0.0):
        calmar = annualized_return / abs(max_drawdown)

    return BacktestMetrics(
        total_trades=len(result.trades),
        total_return=total_return,
        net_pnl=net_pnl,
        return_pct=total_return,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        sharpe=sharpe,
        sortino=sortino,
        calmar=calmar,
        win_rate=_win_rate(result),
        profit_factor=_profit_factor(result),
        average_trade_return=_average_trade_return(result),
        average_holding_time_seconds=_average_holding_time_seconds(result),
        average_holding_bars=_average_holding_bars(result),
    )
