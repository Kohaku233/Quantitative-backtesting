from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re

import pandas as pd

from backend.app.backtest.analytics import (
    build_drawdown_series,
    build_equity_series,
    build_metrics,
    build_monthly_returns,
)
from backend.app.backtest.contracts import (
    BacktestExecutionResult,
    BacktestRequest,
    MarketDataBundle,
)
from backend.app.backtest.engine import run_backtest
from backend.app.data.coverage import format_timestamp, parse_timestamp, shift_bars
from backend.app.data.repository import DuckDbRepository
from backend.app.models.backtests import (
    BacktestMetricsResponse,
    BacktestRunInfo,
    BacktestRunRequest,
    BacktestRunResponse,
    BacktestSeries,
    BacktestSettings,
    BacktestStrategySummary,
    DrawdownPoint,
    EquityPoint,
    MarkerRow,
    MarketBar,
    MonthlyReturnRow,
    TradeRow,
)
from backend.app.models.data_sync import CoverageStatusResponse, DataSyncRequest
from backend.app.models.strategies import StrategyMetadata
from backend.app.strategies.base import (
    BaseStrategyPlugin,
    StrategyExecutionError,
    StrategyValidationError,
)


class BacktestStrategyNotFoundError(LookupError):
    def __init__(self, strategy_id: str) -> None:
        super().__init__(strategy_id)
        self.strategy_id = strategy_id


class BacktestDataCoverageMissingError(RuntimeError):
    def __init__(self, coverage: CoverageStatusResponse) -> None:
        super().__init__("Required market data coverage is incomplete.")
        self.coverage = coverage


class BacktestStrategyValidationServiceError(ValueError):
    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class BacktestStrategyExecutionServiceError(RuntimeError):
    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class BacktestFailedError(RuntimeError):
    def __init__(self, message: str = "Backtest execution failed.") -> None:
        super().__init__(message)


def _validation_error_details(message: str) -> dict[str, object]:
    match = re.match(r"(?P<field>[A-Za-z_][A-Za-z0-9_]*)\b", message)
    if not match:
        return {}
    return {"field": match.group("field")}


def _coerce_validation_exception(exc: Exception) -> BacktestStrategyValidationServiceError:
    if isinstance(exc, KeyError):
        field = str(exc.args[0]) if exc.args else ""
        details = {"field": field} if field else {}
        message = f"{field} is required" if field else "A required strategy parameter is missing."
        return BacktestStrategyValidationServiceError(message, details=details)

    return BacktestStrategyValidationServiceError(
        str(exc),
        details=_validation_error_details(str(exc)),
    )


def _mask_warmup_signals(
    plugin: type[BaseStrategyPlugin],
    effective_start: pd.Timestamp,
) -> type[BaseStrategyPlugin]:
    class EffectiveRangePlugin(plugin):
        @classmethod
        def generate_signals(cls, df: pd.DataFrame, indicators: pd.DataFrame, params):
            signals = plugin.generate_signals(df, indicators, params).copy()
            next_open_times = pd.Series(list(df.index[1:]) + [pd.NaT], index=df.index)
            signals.loc[next_open_times.notna() & (next_open_times < effective_start)] = 0
            return signals

    return EffectiveRangePlugin


def _market_bars(frame: pd.DataFrame) -> list[MarketBar]:
    return [
        MarketBar(
            time=format_timestamp(row["close_time"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
        for _, row in frame.iterrows()
    ]


def _equity_curve(result: BacktestExecutionResult) -> list[EquityPoint]:
    return [
        EquityPoint(time=format_timestamp(point.timestamp), equity=point.value)
        for point in build_equity_series(result)
    ]


def _drawdown_curve(result: BacktestExecutionResult) -> list[DrawdownPoint]:
    return [
        DrawdownPoint(time=format_timestamp(point.timestamp), drawdown=point.value)
        for point in build_drawdown_series(result)
    ]


def _monthly_returns(result: BacktestExecutionResult) -> list[MonthlyReturnRow]:
    return [
        MonthlyReturnRow(month=row.month, return_pct=row.return_pct)
        for row in build_monthly_returns(result)
    ]


def _trade_rows(result: BacktestExecutionResult) -> list[TradeRow]:
    return [
        TradeRow(
            trade_id=trade.trade_id,
            side=trade.side,
            entry_time=format_timestamp(trade.entry_time),
            exit_time=format_timestamp(trade.exit_time),
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            quantity=trade.quantity,
            allocated_margin_at_entry=trade.allocated_margin_at_entry,
            notional=trade.notional,
            gross_pnl=trade.gross_pnl,
            fees=trade.fees,
            funding_pnl=trade.funding_pnl,
            net_pnl=trade.net_pnl,
            return_pct_on_margin=trade.return_pct_on_margin,
            holding_bars=trade.holding_bars,
            holding_seconds=trade.holding_seconds,
            exit_reason=trade.exit_reason,
        )
        for trade in result.trades
    ]


def _marker_rows(result: BacktestExecutionResult) -> list[MarkerRow]:
    markers: list[MarkerRow] = []
    for trade in result.trades:
        markers.append(
            MarkerRow(
                time=format_timestamp(trade.entry_time),
                price=trade.entry_price,
                action=f"entry_{trade.side}",
                trade_id=trade.trade_id,
            )
        )
        markers.append(
            MarkerRow(
                time=format_timestamp(trade.exit_time),
                price=trade.exit_price,
                action=f"exit_{trade.side}",
                trade_id=trade.trade_id,
            )
        )
    return markers


def _trim_execution_result(
    *,
    result: BacktestExecutionResult,
    effective_start: pd.Timestamp,
    effective_end: pd.Timestamp,
) -> BacktestExecutionResult:
    trimmed_dataset = replace(
        result.dataset,
        klines=result.dataset.klines[result.dataset.klines.index >= effective_start].copy(),
        funding_rates=result.dataset.funding_rates[result.dataset.funding_rates.index >= effective_start].copy(),
    )
    trimmed_run = replace(
        result.run,
        effective_start=effective_start.to_pydatetime(),
        effective_end=effective_end.to_pydatetime(),
    )
    return replace(
        result,
        dataset=trimmed_dataset,
        run=trimmed_run,
        bar_snapshots=[
            snapshot for snapshot in result.bar_snapshots if snapshot.timestamp >= effective_start.to_pydatetime()
        ],
        funding_events=[
            event for event in result.funding_events if event.timestamp >= effective_start.to_pydatetime()
        ],
    )


class BacktestService:
    def __init__(
        self,
        *,
        repository: DuckDbRepository,
        strategy_plugins_by_id: dict[str, type[BaseStrategyPlugin]],
        strategy_metadata_by_id: dict[str, StrategyMetadata],
    ) -> None:
        self.repository = repository
        self.strategy_plugins_by_id = strategy_plugins_by_id
        self.strategy_metadata_by_id = strategy_metadata_by_id

    def _resolve_strategy(
        self,
        strategy_id: str,
    ) -> tuple[type[BaseStrategyPlugin], StrategyMetadata]:
        plugin = self.strategy_plugins_by_id.get(strategy_id)
        metadata = self.strategy_metadata_by_id.get(strategy_id)
        if plugin is None or metadata is None:
            raise BacktestStrategyNotFoundError(strategy_id)
        return plugin, metadata

    def _coverage_for_request(
        self,
        request: BacktestRunRequest,
        metadata: StrategyMetadata,
    ) -> CoverageStatusResponse:
        return self.repository.get_coverage(
            request=DataSyncRequest(
                strategy_id=request.strategy_id,
                symbol=request.symbol,
                timeframe=request.timeframe,
                start=request.start,
                end=request.end,
            ),
            required_lookback_bars=metadata.required_lookback_bars,
        )

    def run(self, request: BacktestRunRequest) -> BacktestRunResponse:
        plugin, metadata = self._resolve_strategy(request.strategy_id)
        if request.timeframe not in metadata.supported_timeframes:
            raise BacktestStrategyValidationServiceError(
                f"timeframe '{request.timeframe}' is not supported by strategy '{request.strategy_id}'",
                details={"field": "timeframe"},
            )

        try:
            plugin.validate_params(request.params)
        except (KeyError, TypeError, ValueError, StrategyValidationError) as exc:
            raise _coerce_validation_exception(exc) from exc

        coverage = self._coverage_for_request(request, metadata)
        if not coverage.complete:
            raise BacktestDataCoverageMissingError(coverage)

        effective_start = pd.Timestamp(parse_timestamp(coverage.effective_start))
        effective_end = pd.Timestamp(parse_timestamp(coverage.effective_end))
        warmup_start = shift_bars(
            effective_start.to_pydatetime(),
            request.timeframe,
            metadata.required_lookback_bars,
        )
        dataset = MarketDataBundle(
            symbol=request.symbol,
            timeframe=request.timeframe,
            klines=self.repository.load_klines(
                symbol=request.symbol,
                timeframe=request.timeframe,
                start=warmup_start,
                end=effective_end.to_pydatetime(),
            ),
            funding_rates=self.repository.load_funding_rates(
                symbol=request.symbol,
                start=effective_start.to_pydatetime(),
                end=effective_end.to_pydatetime(),
            ),
        )

        execution_plugin = _mask_warmup_signals(plugin, effective_start)
        engine_request = BacktestRequest(
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            initial_capital=request.initial_capital,
            leverage=request.leverage,
            position_size_pct=request.position_size_pct,
            fee_bps=request.fee_bps,
            slippage_bps=request.slippage_bps,
            params=dict(request.params),
        )

        try:
            execution_result = run_backtest(
                dataset=dataset,
                plugin=execution_plugin,
                request=engine_request,
            )
        except (KeyError, TypeError, ValueError, StrategyValidationError) as exc:
            raise _coerce_validation_exception(exc) from exc
        except StrategyExecutionError as exc:
            raise BacktestStrategyExecutionServiceError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise BacktestFailedError() from exc

        trimmed_result = _trim_execution_result(
            result=execution_result,
            effective_start=effective_start,
            effective_end=effective_end,
        )
        metrics = build_metrics(trimmed_result)

        return BacktestRunResponse(
            run=BacktestRunInfo(
                symbol=request.symbol,
                strategy_id=request.strategy_id,
                timeframe=request.timeframe,
                start=request.start,
                end=request.end,
                effective_start=format_timestamp(trimmed_result.run.effective_start),
                effective_end=format_timestamp(trimmed_result.run.effective_end),
                actual_end=format_timestamp(trimmed_result.run.actual_end),
                status=trimmed_result.run.status,
            ),
            strategy=BacktestStrategySummary(
                id=metadata.id,
                name=metadata.name,
                description=metadata.description,
            ),
            settings=BacktestSettings(
                initial_capital=request.initial_capital,
                leverage=request.leverage,
                fee_bps=request.fee_bps,
                slippage_bps=request.slippage_bps,
                position_size_pct=request.position_size_pct,
            ),
            metrics=BacktestMetricsResponse(
                net_pnl=metrics.net_pnl,
                return_pct=metrics.return_pct,
                annualized_return=metrics.annualized_return,
                max_drawdown=metrics.max_drawdown,
                sharpe=metrics.sharpe,
                sortino=metrics.sortino,
                calmar=metrics.calmar,
                total_trades=metrics.total_trades,
                win_rate=metrics.win_rate,
                profit_factor=metrics.profit_factor,
                average_trade_return=metrics.average_trade_return,
                average_holding_time_seconds=metrics.average_holding_time_seconds,
            ),
            series=BacktestSeries(
                market_bars=_market_bars(trimmed_result.dataset.klines),
                equity_curve=_equity_curve(trimmed_result),
                drawdown_curve=_drawdown_curve(trimmed_result),
            ),
            monthly_returns=_monthly_returns(trimmed_result),
            trades=_trade_rows(trimmed_result),
            markers=_marker_rows(trimmed_result),
            coverage=coverage,
        )
