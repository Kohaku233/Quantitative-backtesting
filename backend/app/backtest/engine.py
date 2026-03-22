from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd

from backend.app.backtest.contracts import (
    BacktestExecutionResult,
    BacktestRequest,
    BarSnapshot,
    FundingEvent,
    MarketDataBundle,
    Marker,
    RunSummary,
    TradeRecord,
)
from backend.app.backtest.indicators import validate_signal_series
from backend.app.backtest.liquidation import calculate_liquidation_price
from backend.app.strategies.base import BaseStrategyPlugin, StrategyExecutionError


@dataclass(slots=True)
class OpenPosition:
    side: str
    quantity: float
    entry_price: float
    entry_time: datetime
    allocated_margin: float
    entry_fee: float
    funding_pnl: float
    entry_bar_index: int


def _to_datetime(value) -> datetime:
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().astimezone(UTC)
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    raise TypeError(f"Unsupported datetime value: {value!r}")


def _bar_close_time(bar: pd.Series) -> datetime:
    return _to_datetime(bar["close_time"])


def _position_unrealized(position: OpenPosition | None, mark_price: float) -> float:
    if position is None:
        return 0.0
    if position.side == "long":
        return position.quantity * (mark_price - position.entry_price)
    return position.quantity * (position.entry_price - mark_price)


def _total_equity(
    *,
    free_cash: float,
    isolated_margin_balance: float,
    position: OpenPosition | None,
    mark_price: float,
) -> float:
    return free_cash + isolated_margin_balance + _position_unrealized(position, mark_price)


def _apply_slippage(raw_price: float, *, side: str, is_entry: bool, slippage_bps: float) -> float:
    slippage_multiplier = slippage_bps / 10000.0
    is_buy = (side == "long" and is_entry) or (side == "short" and not is_entry)
    if is_buy:
        return raw_price * (1 + slippage_multiplier)
    return raw_price * (1 - slippage_multiplier)


def _calculate_fee(fill_price: float, quantity: float, fee_bps: float) -> float:
    return abs(fill_price * quantity) * fee_bps / 10000.0


def _funding_reference_price(dataset: MarketDataBundle, funding_time: datetime) -> float:
    eligible = dataset.klines[dataset.klines["close_time"] <= pd.Timestamp(funding_time)]
    if eligible.empty:
        raise StrategyExecutionError("No close price is available at or before funding time.")
    return float(eligible.iloc[-1]["close"])


def _open_position(
    *,
    current_equity: float,
    free_cash: float,
    request: BacktestRequest,
    side: str,
    raw_price: float,
    timestamp: datetime,
    bar_index: int,
) -> tuple[OpenPosition, float, float]:
    allocated_margin = current_equity * request.position_size_pct
    if allocated_margin <= 0:
        raise StrategyExecutionError("Position size must allocate positive margin.")

    fill_price = _apply_slippage(raw_price, side=side, is_entry=True, slippage_bps=request.slippage_bps)
    notional = allocated_margin * request.leverage
    quantity = notional / fill_price
    entry_fee = _calculate_fee(fill_price, quantity, request.fee_bps)

    if allocated_margin + entry_fee > current_equity:
        raise StrategyExecutionError("Entry requires more equity than is available.")

    free_cash -= allocated_margin + entry_fee
    position = OpenPosition(
        side=side,
        quantity=quantity,
        entry_price=fill_price,
        entry_time=timestamp,
        allocated_margin=allocated_margin,
        entry_fee=entry_fee,
        funding_pnl=0.0,
        entry_bar_index=bar_index,
    )
    return position, free_cash, allocated_margin


def _close_position(
    *,
    position: OpenPosition,
    free_cash: float,
    isolated_margin_balance: float,
    request: BacktestRequest,
    raw_price: float,
    timestamp: datetime,
    bar_index: int,
    exit_reason: str,
    apply_slippage: bool,
) -> tuple[TradeRecord, float]:
    fill_price = (
        _apply_slippage(raw_price, side=position.side, is_entry=False, slippage_bps=request.slippage_bps)
        if apply_slippage
        else raw_price
    )
    exit_fee = _calculate_fee(fill_price, position.quantity, request.fee_bps)
    if position.side == "long":
        realized_pnl = position.quantity * (fill_price - position.entry_price)
    else:
        realized_pnl = position.quantity * (position.entry_price - fill_price)

    settlement = max(isolated_margin_balance + realized_pnl - exit_fee, 0.0)
    free_cash += settlement
    net_pnl = realized_pnl + position.funding_pnl - position.entry_fee - exit_fee
    trade = TradeRecord(
        trade_id=0,
        side=position.side,
        entry_time=position.entry_time,
        exit_time=timestamp,
        entry_price=position.entry_price,
        exit_price=fill_price,
        quantity=position.quantity,
        notional=position.quantity * position.entry_price,
        allocated_margin_at_entry=position.allocated_margin,
        gross_pnl=realized_pnl,
        fees=position.entry_fee + exit_fee,
        funding_pnl=position.funding_pnl,
        net_pnl=net_pnl,
        return_pct_on_margin=(net_pnl / position.allocated_margin) if position.allocated_margin else 0.0,
        holding_bars=max(bar_index - position.entry_bar_index, 0),
        holding_seconds=max((timestamp - position.entry_time).total_seconds(), 0.0),
        exit_reason=exit_reason,
    )
    return trade, free_cash


def run_backtest(
    *,
    dataset: MarketDataBundle,
    plugin: type[BaseStrategyPlugin],
    request: BacktestRequest,
) -> BacktestExecutionResult:
    if dataset.klines.empty:
        raise StrategyExecutionError("Market data bundle does not contain any bars.")
    validated_params = plugin.validate_params(request.params)
    indicators = plugin.compute_indicators(dataset.klines, validated_params)
    signals = validate_signal_series(
        plugin.generate_signals(dataset.klines, indicators, validated_params),
        dataset.klines.index,
    )

    funding_rows = list(dataset.funding_rates.reset_index().itertuples(index=False, name="FundingRow"))
    funding_pointer = 0
    free_cash = request.initial_capital
    isolated_margin_balance = 0.0
    position: OpenPosition | None = None
    trades: list[TradeRecord] = []
    funding_events: list[FundingEvent] = []
    bar_snapshots: list[BarSnapshot] = []
    markers: list[Marker] = []
    scheduled_signal: int | None = None

    bars = list(dataset.klines.iterrows())
    first_open_time = _to_datetime(bars[0][0])
    last_open_time = _to_datetime(bars[-1][0])
    last_close_time = _bar_close_time(dataset.klines.iloc[-1])

    def apply_funding(up_to: datetime, *, include_equal: bool, applied_before_open_fill: bool) -> None:
        nonlocal funding_pointer, isolated_margin_balance
        comparator = (lambda timestamp: timestamp <= up_to) if include_equal else (lambda timestamp: timestamp < up_to)
        while funding_pointer < len(funding_rows):
            funding_time = _to_datetime(funding_rows[funding_pointer].funding_time)
            if not comparator(funding_time):
                break

            if position is not None:
                reference_price = _funding_reference_price(dataset, funding_time)
                notional = abs(position.quantity) * reference_price
                funding_rate = float(funding_rows[funding_pointer].funding_rate)
                cash_flow = -notional * funding_rate if position.side == "long" else notional * funding_rate
                isolated_margin_balance += cash_flow
                position.funding_pnl += cash_flow
                funding_events.append(
                    FundingEvent(
                        timestamp=funding_time,
                        funding_rate=funding_rate,
                        reference_price=reference_price,
                        cash_flow=cash_flow,
                        applied_before_open_fill=applied_before_open_fill,
                    )
                )

            funding_pointer += 1

    for bar_index, (bar_open_index, bar) in enumerate(bars):
        bar_open_time = _to_datetime(bar_open_index)
        bar_close_time = _bar_close_time(bar)
        bar_open = float(bar["open"])
        bar_high = float(bar["high"])
        bar_low = float(bar["low"])
        bar_close = float(bar["close"])
        is_final_bar = bar_index == len(bars) - 1

        apply_funding(bar_open_time, include_equal=True, applied_before_open_fill=True)

        if scheduled_signal is not None:
            if position is None:
                if scheduled_signal == 1:
                    current_equity = _total_equity(
                        free_cash=free_cash,
                        isolated_margin_balance=isolated_margin_balance,
                        position=position,
                        mark_price=bar_open,
                    )
                    position, free_cash, isolated_margin_balance = _open_position(
                        current_equity=current_equity,
                        free_cash=free_cash,
                        request=request,
                        side="long",
                        raw_price=bar_open,
                        timestamp=bar_open_time,
                        bar_index=bar_index,
                    )
                    markers.append(Marker(timestamp=bar_open_time, price=position.entry_price, kind="entry_long"))
                elif scheduled_signal == -1:
                    current_equity = _total_equity(
                        free_cash=free_cash,
                        isolated_margin_balance=isolated_margin_balance,
                        position=position,
                        mark_price=bar_open,
                    )
                    position, free_cash, isolated_margin_balance = _open_position(
                        current_equity=current_equity,
                        free_cash=free_cash,
                        request=request,
                        side="short",
                        raw_price=bar_open,
                        timestamp=bar_open_time,
                        bar_index=bar_index,
                    )
                    markers.append(Marker(timestamp=bar_open_time, price=position.entry_price, kind="entry_short"))
            else:
                current_signal = 1 if position.side == "long" else -1
                if scheduled_signal == 0:
                    trade, free_cash = _close_position(
                        position=position,
                        free_cash=free_cash,
                        isolated_margin_balance=isolated_margin_balance,
                        request=request,
                        raw_price=bar_open,
                        timestamp=bar_open_time,
                        bar_index=bar_index,
                        exit_reason="signal_flat",
                        apply_slippage=True,
                    )
                    trades.append(trade)
                    trades[-1].trade_id = len(trades)
                    markers.append(Marker(timestamp=trade.exit_time, price=trade.exit_price, kind=f"exit_{trade.side}"))
                    position = None
                    isolated_margin_balance = 0.0
                elif scheduled_signal != current_signal:
                    trade, free_cash = _close_position(
                        position=position,
                        free_cash=free_cash,
                        isolated_margin_balance=isolated_margin_balance,
                        request=request,
                        raw_price=bar_open,
                        timestamp=bar_open_time,
                        bar_index=bar_index,
                        exit_reason="signal_flip",
                        apply_slippage=True,
                    )
                    trades.append(trade)
                    trades[-1].trade_id = len(trades)
                    markers.append(Marker(timestamp=trade.exit_time, price=trade.exit_price, kind=f"exit_{trade.side}"))
                    position = None
                    isolated_margin_balance = 0.0
                    current_equity = _total_equity(
                        free_cash=free_cash,
                        isolated_margin_balance=isolated_margin_balance,
                        position=position,
                        mark_price=bar_open,
                    )
                    target_side = "long" if scheduled_signal == 1 else "short"
                    position, free_cash, isolated_margin_balance = _open_position(
                        current_equity=current_equity,
                        free_cash=free_cash,
                        request=request,
                        side=target_side,
                        raw_price=bar_open,
                        timestamp=bar_open_time,
                        bar_index=bar_index,
                    )
                    markers.append(Marker(timestamp=bar_open_time, price=position.entry_price, kind=f"entry_{position.side}"))

        apply_funding(bar_close_time, include_equal=True, applied_before_open_fill=False)

        if position is not None:
            liquidation_price = calculate_liquidation_price(
                position.side,
                position.entry_price,
                position.quantity,
                isolated_margin_balance,
                request.maintenance_margin_rate,
            )
            liquidated = (position.side == "long" and bar_low <= liquidation_price) or (
                position.side == "short" and bar_high >= liquidation_price
            )
            if liquidated:
                trade, free_cash = _close_position(
                    position=position,
                    free_cash=free_cash,
                    isolated_margin_balance=isolated_margin_balance,
                    request=request,
                    raw_price=liquidation_price,
                    timestamp=bar_open_time,
                    bar_index=bar_index,
                    exit_reason="liquidation",
                    apply_slippage=False,
                )
                trades.append(trade)
                trades[-1].trade_id = len(trades)
                markers.append(Marker(timestamp=trade.exit_time, price=trade.exit_price, kind=f"exit_{trade.side}"))
                position = None
                isolated_margin_balance = 0.0
                bar_snapshots.append(
                    BarSnapshot(
                        timestamp=bar_open_time,
                        open=bar_open,
                        high=bar_high,
                        low=bar_low,
                        close=bar_close,
                        volume=float(bar["volume"]),
                        free_cash=free_cash,
                        isolated_margin_balance=0.0,
                        unrealized_pnl=0.0,
                        equity=free_cash,
                    )
                )
                return BacktestExecutionResult(
                    request=request,
                    dataset=dataset,
                    run=RunSummary(
                        status="liquidated",
                        effective_start=first_open_time,
                        effective_end=last_open_time,
                        actual_end=bar_open_time,
                        final_equity=free_cash,
                    ),
                    bar_snapshots=bar_snapshots,
                    trades=trades,
                    funding_events=funding_events,
                    markers=markers,
                )

        if is_final_bar and position is not None:
            trade, free_cash = _close_position(
                position=position,
                free_cash=free_cash,
                isolated_margin_balance=isolated_margin_balance,
                request=request,
                raw_price=bar_close,
                timestamp=bar_close_time,
                bar_index=bar_index + 1,
                exit_reason="end_of_range",
                apply_slippage=True,
            )
            trades.append(trade)
            trades[-1].trade_id = len(trades)
            markers.append(Marker(timestamp=trade.exit_time, price=trade.exit_price, kind=f"exit_{trade.side}"))
            position = None
            isolated_margin_balance = 0.0

        unrealized_pnl = _position_unrealized(position, bar_close)
        bar_snapshots.append(
            BarSnapshot(
                timestamp=bar_close_time,
                open=bar_open,
                high=bar_high,
                low=bar_low,
                close=bar_close,
                volume=float(bar["volume"]),
                free_cash=free_cash,
                isolated_margin_balance=isolated_margin_balance,
                unrealized_pnl=unrealized_pnl,
                equity=free_cash + isolated_margin_balance + unrealized_pnl,
            )
        )

        scheduled_signal = None if is_final_bar else int(signals.iloc[bar_index])

    final_equity = bar_snapshots[-1].equity if bar_snapshots else request.initial_capital
    return BacktestExecutionResult(
        request=request,
        dataset=dataset,
        run=RunSummary(
            status="completed",
            effective_start=first_open_time,
            effective_end=last_open_time,
            actual_end=last_close_time,
            final_equity=final_equity,
        ),
        bar_snapshots=bar_snapshots,
        trades=trades,
        funding_events=funding_events,
        markers=markers,
    )
