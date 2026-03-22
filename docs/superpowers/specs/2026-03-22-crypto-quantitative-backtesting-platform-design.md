# Crypto Quantitative Backtesting Platform Design

## Goal

Build a local web-based quantitative backtesting platform for crypto perpetual futures, starting with Binance USD-M `BTCUSDT` perpetual. The platform must let a user:

- Select a local strategy plugin from a shared interface.
- Configure strategy parameters in the browser.
- Select a custom backtest time range and timeframe.
- Run a backtest locally against Binance public historical data.
- View professional backtest outputs, including metrics such as max drawdown and Sharpe ratio.

The first version prioritizes result credibility, clear system boundaries, and a complete end-to-end workflow over breadth of market coverage.

## Product Scope

### In Scope

- Single market: Binance USD-M `BTCUSDT` perpetual.
- Local-only deployment.
- Browser-based UI.
- Strategy plugins discovered from local Python files.
- Custom backtest time range.
- Supported timeframes: `15m`, `1h`, `4h`, `1d`.
- Long and short perpetual futures backtests.
- Isolated margin, fixed leverage, single position model.
- User-configurable fee rate, slippage, initial capital, leverage, and position size percent.
- Historical kline and funding-rate sync from Binance public APIs.
- Local cache of historical market data.
- Professional analytics output:
  - Net PnL
  - Return %
  - Annualized Return
  - Max Drawdown
  - Sharpe Ratio
  - Sortino Ratio
  - Calmar Ratio
  - Win Rate
  - Profit Factor
  - Total Trades
  - Average Trade Return
  - Average Holding Time
- Result visualizations:
  - Kline chart with entry and exit markers
  - Equity curve
  - Drawdown curve
  - Monthly returns table
  - Trade list

### Out of Scope for V1

- Multiple trading pairs.
- Spot trading.
- Portfolio backtests.
- Parameter optimization and batch sweeps.
- Multi-position or hedged-position modes.
- Cross margin.
- Real-time trading or paper trading.
- Exchange private API keys.
- User accounts or multi-user permissions.
- Remote deployment infrastructure.
- Arbitrary user code upload from the browser.

## Design Principles

1. Backtest credibility is more important than feature count.
2. Strategy logic, market data, execution simulation, and analytics must remain separate modules.
3. The system must be able to grow to more markets and optimization workflows without rewriting the core interfaces.
4. The browser should configure and observe backtests, not own business logic.
5. All perpetual-specific settlement logic must live in platform code rather than inside user strategies.

## Architecture Overview

The system is a local monorepo with a Python backend and a React frontend.

### Frontend

- `React + Vite`
- Renders a single backtesting workspace page.
- Fetches available strategy metadata from the backend.
- Builds the strategy parameter form from backend-provided schema.
- Starts market-data sync and backtest runs through HTTP APIs.
- Displays charts, metrics, and trade tables.

### Backend API

- `FastAPI`
- Exposes endpoints for:
  - Strategy discovery
  - Data coverage inspection
  - Data synchronization
  - Backtest execution
  - Health checks
- Returns normalized JSON responses that are independent of the underlying backtesting framework.

### Strategy Plugin System

- Local Python files in `backend/strategies/` are auto-discovered.
- Each plugin implements a common base class and schema contract.
- Plugins only define indicators and signal generation.
- Plugins do not directly model orders, fees, funding, liquidation, or account state.

### Market Data Layer

- Downloads Binance public historical data on demand.
- Normalizes and caches kline and funding-rate history locally.
- Provides time-range-aware data access for backtests.

### Backtest Engine Layer

- All runtime perpetual execution, PnL settlement, funding, liquidation, and result contracts are owned by the platform's custom perpetual execution engine.
- Produces standardized fills, positions, cash-equity evolution, and trade logs.

### Analytics Layer

- Computes metrics, equity curve, drawdown curve, monthly returns, and trade summaries from the standardized backtest output.
- Keeps reporting logic separate from execution logic.

## Proposed Repository Layout

```text
backend/
  app/
    api/
    analytics/
    backtest/
    data/
    models/
    main.py
  strategies/
    __init__.py
    example_sma_cross.py
  tests/
    api/
    analytics/
    backtest/
    data/
    strategies/
frontend/
  src/
    components/
    features/backtest/
    lib/
    api/
    app/
  tests/
docs/
  superpowers/
    specs/
```

## Module Boundaries

### 1. Frontend Workspace

Responsibilities:

- Render the backtest configuration panel.
- Render strategy parameters from schema.
- Render data coverage and sync state.
- Render backtest results.
- Keep client-side state for the active run and the latest result.

Explicit non-responsibilities:

- No exchange logic.
- No strategy execution.
- No metric computation beyond lightweight formatting.

### 2. API Layer

Responsibilities:

- Input validation.
- Orchestration across data sync, strategy loading, backtest execution, and analytics.
- Returning stable response shapes.

Explicit non-responsibilities:

- No direct chart rendering logic.
- No embedded strategy definitions.

### 3. Strategy Plugin System

Responsibilities:

- Discover local strategy classes.
- Surface metadata and parameter schema.
- Validate parameter payloads.
- Produce standardized signals and optional indicator series.

Explicit non-responsibilities:

- No brokerage logic.
- No exchange fee logic.
- No funding or liquidation logic.

### 4. Data Layer

Responsibilities:

- Download missing kline and funding-rate data.
- Normalize timestamps and numeric types.
- Cache and query local history.
- Report local coverage ranges to the API layer.

Explicit non-responsibilities:

- No strategy execution.
- No metric calculation.

### 5. Backtest Execution Layer

Responsibilities:

- Apply signal timing rules.
- Simulate long and short perpetual positions.
- Apply isolated margin rules, leverage, fees, slippage, funding settlement, and liquidation.
- Emit trade events and account state changes.

Explicit non-responsibilities:

- No schema discovery.
- No browser response formatting beyond its internal result contract.

#### Internal Execution Result Contract

The execution engine must emit a single internal result object for the analytics layer with this shape:

```json
{
  "run": {
    "status": "completed",
    "effective_start": "2024-01-01T00:00:00Z",
    "effective_end": "2024-12-31T23:00:00Z",
    "actual_end": "2025-01-01T00:00:00Z"
  },
  "settings": {},
  "coverage": {},
  "bar_snapshots": [
    {
      "time": "2024-01-01T01:00:00Z",
      "open": 42200.0,
      "high": 42310.0,
      "low": 42180.0,
      "close": 42290.0,
      "volume": 1023.5,
      "free_cash": 10000.0,
      "isolated_margin_balance": 0.0,
      "unrealized_pnl": 0.0,
      "equity": 10000.0
    }
  ],
  "trades": [
    {
      "trade_id": 1,
      "side": "long",
      "entry_time": "2024-01-03T08:00:00Z",
      "exit_time": "2024-01-05T12:00:00Z",
      "entry_price": 43210.5,
      "exit_price": 44100.0,
      "quantity": 0.023,
      "allocated_margin_at_entry": 331.28,
      "notional": 993.84,
      "gross_pnl": 20.46,
      "fees": 0.8,
      "funding_pnl": -0.11,
      "net_pnl": 19.55,
      "return_pct_on_margin": 0.059,
      "holding_bars": 52,
      "holding_seconds": 187200,
      "exit_reason": "signal_flip"
    }
  ],
  "markers": [
    {
      "time": "2024-01-03T08:00:00Z",
      "price": 43210.5,
      "action": "entry_long",
      "trade_id": 1
    }
  ]
}
```

Analytics must consume only this contract and must not reach back into execution internals.

### 6. Analytics Layer

Responsibilities:

- Convert execution results into portfolio metrics and chart-ready series.
- Standardize reporting for the frontend.

Explicit non-responsibilities:

- No trade execution.
- No exchange sync.

## Trading and Execution Model

### Instrument

- Binance USD-M `BTCUSDT` perpetual futures.

### Account Model

- Single position at a time.
- Long or short.
- Isolated margin.
- Fixed user-selected leverage.
- Position sizing as a percent of current account equity.

#### Position Sizing Formula

For an opening trade:

- `equity_before_trade` = current total account equity before allocating new margin
- `position_size_pct` = user input in `(0, 1]`
- `allocated_margin` = `equity_before_trade * position_size_pct`
- `entry_notional` = `allocated_margin * leverage`
- `entry_quantity` = `entry_notional / entry_fill_price`

The platform must reject the order if:

- `allocated_margin <= 0`
- `allocated_margin > equity_before_trade`
- `allocated_margin + entry_fee > equity_before_trade`

V1 uses one open isolated position at a time. Entering the opposite side closes the existing position first, then opens the new one on the same next-bar-open execution step.

#### Flip Sizing Rule

When a long flips to short or a short flips to long on the same execution step:

1. close the existing position first
2. apply realized PnL, funding already posted to the isolated ledger, and exit fee
3. recompute `total_equity`
4. size the new position from that post-close `total_equity`

The new `allocated_margin` must never be based on pre-close equity.

#### Account Ledger Model

The engine must maintain exactly these balances:

- `free_cash`: cash not currently locked as isolated margin
- `isolated_margin_balance`: margin currently assigned to the open position, including posted funding cash flows
- `unrealized_pnl`: mark-to-market PnL on the open position at the current evaluation price

Derived values:

- `total_equity = free_cash + isolated_margin_balance + unrealized_pnl`

Balance transitions:

- On entry:
  - `free_cash -= allocated_margin + entry_fee`
  - `isolated_margin_balance = allocated_margin`
- On funding:
  - `isolated_margin_balance += funding_cash_flow`
- On exit:
  - `free_cash += isolated_margin_balance + realized_trade_pnl - exit_fee`
  - `isolated_margin_balance = 0`
  - `unrealized_pnl = 0`

Funding and fees must never be booked twice. `total_equity` changes because the underlying balances change; it is never updated independently.

### Signal Timing

- Strategies generate signals on the current bar close.
- Orders execute at the next bar open.

This rule is mandatory to avoid look-ahead bias.

### Time Boundary Normalization

The API accepts arbitrary UTC timestamps for `start` and `end`, but the effective bar range is normalized as follows:

- `effective_start_bar` = first bar whose `open_time >= start`
- `effective_end_bar` = last bar whose `close_time <= end`

If no full bars exist after normalization, the request is invalid.

All caching, funding alignment, strategy execution, and analytics must operate on the effective normalized range, not on partial bars.

Conventions:

- `effective_start` means the open timestamp of the first included bar
- `effective_end` means the open timestamp of the last included bar
- `actual_end` means the timestamp of the terminal accounting event for the run
  - for non-liquidated completed runs, this is the final included bar close timestamp after any forced close
  - for liquidated runs, this is the liquidation timestamp

Duration-based metrics must use `actual_end`.

### Supported Position States

- Flat
- Long
- Short

State transitions allowed:

- Flat -> Long
- Flat -> Short
- Long -> Flat
- Short -> Flat
- Long -> Short via close then open
- Short -> Long via close then open

Signal handling rules:

- repeated `1` while already long = hold, no new trade
- repeated `-1` while already short = hold, no new trade
- `0` while already flat = no-op
- a signal on the final included bar with no next-bar open cannot open a new trade and is ignored

### Fee Model

- Fees are applied on both entry and exit.
- V1 defaults to taker-style fee assumptions.
- User can override fee basis points in the UI.

#### Fee Formula

- `fee = abs(fill_price * quantity) * (fee_bps / 10000)`

### Slippage Model

- Slippage is modeled as basis points on notional at entry and exit.
- User-configurable in the UI.

#### Fill Price Formula

For normal signal-driven executions, `raw_price` is the next bar open.

- long entry fill: `raw_price * (1 + slippage_bps / 10000)`
- long exit fill: `raw_price * (1 - slippage_bps / 10000)`
- short entry fill: `raw_price * (1 - slippage_bps / 10000)`
- short exit fill: `raw_price * (1 + slippage_bps / 10000)`

For end-of-range forced closes, `raw_price` is the final included bar close.

For liquidations, the configurable slippage model is not applied; the deterministic liquidation price is used directly and only the exit fee is charged.

### Funding Settlement

- Funding is sourced from Binance historical funding-rate data.
- If a position spans a funding timestamp, funding cash flow is applied to account equity.
- Long and short funding effects follow market convention.

#### Funding Settlement Rule

For each Binance funding record with timestamp `funding_time`:

- Funding is applied if a position is open at `funding_time`.
- The reference price is the latest available bar close at or before `funding_time`.
- `position_notional_at_funding = abs(position_quantity) * reference_price`
- Long funding cash flow = `-position_notional_at_funding * funding_rate`
- Short funding cash flow = `position_notional_at_funding * funding_rate`

Funding is posted directly into `isolated_margin_balance`. `total_equity` changes only through the derived ledger equation above.

#### Funding and Order Precedence

If a funding timestamp is exactly equal to a bar open timestamp that is also an order execution timestamp:

- first apply funding to any position that was already open before that bar
- then process entry, exit, or flip orders scheduled for that bar open

A newly opened position at that same timestamp does not receive or pay that funding event.

Funding timestamps that fall strictly inside a bar, not at its open, must also be applied in chronological order during that bar. V1 approximates those events using the latest available close at or before the funding timestamp as the reference price.

#### Within-Bar Event Order

For each included bar, process events in this order:

1. apply funding events timestamped exactly at that bar open to positions already open before the bar
2. execute scheduled exits, entries, or flips at the bar open
3. apply funding events whose timestamps fall strictly inside `(bar_open, bar_close]` in chronological order
4. if a position exists after step 3, it is eligible for liquidation during the same bar using the bar high/low rule
5. for non-final bars, sample mark-to-market equity at the bar close
6. if this is the final included bar and a position remains open, force-close it at the bar close per the end-of-range rule
7. record the final bar equity after step 6 has completed

### Liquidation

- The perpetual execution layer must model liquidation against isolated margin constraints.
- If account equity assigned to the isolated position falls below maintenance requirements as defined by the platform model, the run is marked liquidated and stops.

V1 does not need full exchange-grade liquidation ladder replication, but it must implement a deterministic and documented liquidation rule consistent with isolated leverage backtests.

#### Liquidation Rule

V1 uses the following deterministic isolated-margin model:

- `maintenance_margin_rate = 0.005`
- `maintenance_margin = current_position_notional * maintenance_margin_rate`
- `isolated_position_equity = isolated_margin_balance + unrealized_pnl_at_price`

Where:

- `current_position_notional = abs(position_quantity) * price`
- For a long, `unrealized_pnl_at_price = (price - entry_price) * position_quantity`
- For a short, `unrealized_pnl_at_price = (entry_price - price) * abs(position_quantity)`

Intrabar liquidation checks use:

- bar low for long positions
- bar high for short positions

If `isolated_position_equity <= maintenance_margin` at the intrabar liquidation check price, the position is liquidated.

For a long position with positive `quantity`:

- `liquidation_price_long = (entry_price * quantity - isolated_margin_balance) / (quantity * (1 - maintenance_margin_rate))`
- liquidate if `bar_low <= liquidation_price_long`

For a short position with positive `quantity = abs(position_quantity)`:

- `liquidation_price_short = (entry_price * quantity + isolated_margin_balance) / (quantity * (1 + maintenance_margin_rate))`
- liquidate if `bar_high >= liquidation_price_short`

The liquidation fill price is:

- `liquidation_price_long` for a long liquidation
- `liquidation_price_short` for a short liquidation

The backtest then:

- closes the position at the liquidation fill price
- applies exit fees
- settles the isolated ledger into free cash
- marks the run `status = "liquidated"`
- stops processing subsequent bars

This rule must be implemented exactly and documented in code comments and tests.

#### Post-Liquidation Ledger Settlement

On liquidation:

- `realized_trade_pnl = unrealized_pnl_at_liquidation_price`
- `liquidation_settlement = isolated_margin_balance + realized_trade_pnl - exit_fee`
- `free_cash += max(liquidation_settlement, 0)`
- `isolated_margin_balance = 0`
- `unrealized_pnl = 0`
- `total_equity = free_cash`

Any negative isolated remainder is treated as fully lost capital from the isolated position and must not make `free_cash` go below zero.

For a liquidated run:

- `run.status = "liquidated"`
- `run.actual_end = liquidation_timestamp`
- all duration-based metrics, annualization, monthly returns, and the terminal equity curve point must use `actual_end`, not the originally requested end timestamp

## Strategy Plugin Contract

V1 uses local Python strategy files discovered from a dedicated directory.

Each plugin must declare:

- `id`
- `name`
- `description`
- `supported_timeframes`
- `required_lookback_bars`
- `parameter_schema`

Each plugin must implement:

- `validate_params(params) -> dict`
- `compute_indicators(df, params) -> pandas.DataFrame`
- `generate_signals(df, indicators, params) -> pandas.Series`

### Base Class Contract

The shared base class must expose this shape:

```python
class BaseStrategyPlugin(ABC):
    id: str
    name: str
    description: str
    supported_timeframes: tuple[str, ...]
    required_lookback_bars: int
    parameter_schema: list[dict[str, Any]]

    @classmethod
    @abstractmethod
    def validate_params(cls, params: Mapping[str, Any]) -> dict[str, Any]:
        ...

    @classmethod
    @abstractmethod
    def compute_indicators(
        cls,
        df: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.DataFrame:
        ...

    @classmethod
    @abstractmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        ...
```

### Signal Contract

`generate_signals` returns exactly one `pandas.Series` aligned to the bar data with a normalized target-position intent:

- `1` means long bias
- `-1` means short bias
- `0` means flat

The platform execution layer owns the conversion from signal intent to actual trades.

Signal requirements:

- index must equal `df.index`
- length must equal `len(df)`
- dtype must be integer-compatible
- values may only be `-1`, `0`, or `1`
- no missing values are allowed
- the first bar may emit a signal, but it can only be executed on the next bar open

If any of these rules are violated, the platform must raise a structured strategy execution error and abort the run.

### Warm-Up Rule

The engine must fetch and load `required_lookback_bars` additional bars before `effective_start_bar`.

- warm-up bars may be used for indicators and signal generation
- warm-up bars must not appear in reported `market_bars`, equity curves, drawdown curves, trades, monthly returns, or summary metrics
- if enough warm-up history is unavailable, the run must fail with `data_coverage_missing`

### Parameter Schema Contract

The parameter schema must be rich enough for the frontend to render a form without hard-coded per-strategy UI:

- field key
- label
- type
- default
- min/max where relevant
- enum options where relevant
- help text
- required flag

Each field object must include:

```json
{
  "key": "fast_period",
  "label": "Fast Period",
  "type": "integer",
  "default": 20,
  "required": true,
  "min": 1,
  "max": 500,
  "step": 1,
  "help": "Short moving average period."
}
```

Allowed `type` values in V1:

- `integer`
- `number`
- `boolean`
- `select`

For `select`, an `options` array is required.

### Trust Model

Strategy plugins are local trusted code loaded from disk. V1 does not attempt sandboxing.

### Exception Contract

- `validate_params` failures must raise `StrategyValidationError`
- indicator or signal generation failures must raise `StrategyExecutionError`
- the API layer must convert both into structured JSON errors
- plugin exceptions must not crash the API process

### Discovery Failure Rules

During plugin discovery:

- a file that fails to import is skipped and recorded as a discovery warning
- a class that does not satisfy the base contract is skipped and recorded as a discovery warning
- duplicate plugin `id` values invalidate all colliding plugins and are recorded as discovery warnings

`GET /api/strategies` must return:

- only valid, uniquely identified strategies
- a `discovery_warnings` array describing skipped files or duplicate ids

## Data Model

### Historical Klines

Each record must include at minimum:

- symbol
- timeframe
- open_time
- open
- high
- low
- close
- volume
- close_time

### Funding Rates

Each record must include at minimum:

- symbol
- funding_time
- funding_rate

### Backtest Request

Each run must be parameterized by:

- strategy id
- strategy params
- timeframe
- start time
- end time
- initial capital
- leverage
- fee basis points
- slippage basis points
- position size percent

### Backtest Result

The standardized result must include:

- run metadata
- strategy metadata
- resolved execution settings
- summary metrics
- equity curve series
- drawdown curve series
- monthly returns table
- trade list
- position markers for chart overlay
- run status
- data coverage summary used for the run

#### Response Object Contracts

`strategy` metadata must contain:

```json
{
  "id": "sma_cross",
  "name": "SMA Cross",
  "description": "Long/short moving-average crossover strategy."
}
```

`coverage summary` must contain:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "requested_start": "2024-01-01T00:00:00Z",
  "requested_end": "2024-12-31T23:59:59Z",
  "effective_start": "2024-01-01T00:00:00Z",
  "effective_end": "2024-12-31T23:00:00Z",
  "complete": true,
  "kline": {
    "cached_start": "2024-01-01T00:00:00Z",
    "cached_end": "2024-12-31T23:00:00Z",
    "missing_ranges": []
  },
  "funding": {
    "cached_start": "2024-01-01T00:00:00Z",
    "cached_end": "2024-12-31T16:00:00Z",
    "missing_ranges": []
  }
}
```

Each `trade list` row must contain:

```json
{
  "trade_id": 1,
  "side": "long",
  "entry_time": "2024-01-03T08:00:00Z",
  "exit_time": "2024-01-05T12:00:00Z",
  "entry_price": 43210.5,
  "exit_price": 44100.0,
  "quantity": 0.023,
  "allocated_margin_at_entry": 331.28,
  "notional": 993.84,
  "gross_pnl": 20.46,
  "fees": 0.8,
  "funding_pnl": -0.11,
  "net_pnl": 19.55,
  "return_pct_on_margin": 0.059,
  "holding_bars": 52,
  "holding_seconds": 187200,
  "exit_reason": "signal_flip"
}
```

Each `position marker` must contain:

```json
{
  "time": "2024-01-03T08:00:00Z",
  "price": 43210.5,
  "action": "entry_long",
  "trade_id": 1
}
```

Each `market_bars` item must contain:

```json
{
  "time": "2024-01-01T01:00:00Z",
  "open": 42200.0,
  "high": 42310.0,
  "low": 42180.0,
  "close": 42290.0,
  "volume": 1023.5
}
```

Each `equity_curve` item must contain:

```json
{
  "time": "2024-01-01T01:00:00Z",
  "equity": 10000.0
}
```

Each `drawdown_curve` item must contain:

```json
{
  "time": "2024-01-01T01:00:00Z",
  "drawdown": 0.0
}
```

Each `monthly_returns` row must contain:

```json
{
  "month": "2024-01",
  "return_pct": 0.0312
}
```

## Data Source and Sync Behavior

### Public Exchange APIs

V1 uses Binance public futures endpoints for:

- historical klines
- historical funding rates

No private credentials are required.

### Sync Workflow

V1 uses explicit frontend-managed sync before run execution:

1. Frontend checks cache coverage through `GET /api/data/status`.
2. If required slices are missing, frontend calls `POST /api/data/sync`.
3. After successful sync, frontend calls `POST /api/backtests/run`.

`POST /api/backtests/run` does not auto-sync in V1. It requires complete cached kline and funding coverage for the effective normalized range plus any strategy-required warm-up bars.

### Sync Implementation Rules

- Kline sync paginates until the requested range is fully covered.
- Funding-rate sync paginates until the requested range is fully covered.
- On `429` or `5xx`, retry with exponential backoff of `1s`, `2s`, `4s`, `8s`, `16s`.
- After the final retry failure, the API must return a non-2xx error with code `sync_failed`.
- If the exchange returns no rows for an otherwise valid request, the backend must return a successful `no_data_available` sync response instead of silently succeeding.
- If funding coverage is still incomplete after sync, sync is considered failed and the backend must return a non-2xx `sync_failed` response.

### Cache Guarantees

- Sync operations must be idempotent.
- Duplicate bars and duplicate funding records must not be stored.
- Timestamp handling must be consistent and timezone-safe.
- The system must be able to report what time coverage is already cached.

Coverage is considered complete only when:

- every required warm-up bar exists before `effective_start_bar` according to the selected strategy's `required_lookback_bars`
- every expected kline bar exists between `effective_start_bar` and `effective_end_bar` at the requested timeframe cadence
- every expected funding timestamp on Binance's 8-hour schedule exists for the effective range

If any internal gap exists, coverage is incomplete even if cached start and end timestamps appear continuous.

## API Design

### `GET /api/health`

Returns process health and basic dependency readiness.

### `GET /api/strategies`

Returns discovered strategy plugins and parameter schemas.

Example response shape:

```json
{
  "strategies": [
    {
      "id": "sma_cross",
      "name": "SMA Cross",
      "description": "Long/short moving-average crossover strategy.",
      "supported_timeframes": ["15m", "1h", "4h", "1d"],
      "parameter_schema": []
    }
  ],
  "discovery_warnings": [
    {
      "file": "broken_strategy.py",
      "reason": "ImportError: missing dependency"
    }
  ]
}
```

### `GET /api/data/status`

Returns local cache coverage for:

- `BTCUSDT` by timeframe
- funding-rate coverage

Request query parameters:

- `symbol`
- `strategy_id`
- `timeframe`
- `start`
- `end`

The response is request-scoped for the normalized effective range plus any required warm-up bars for the selected strategy and must state whether coverage is complete.

Example response shape:

```json
{
  "symbol": "BTCUSDT",
  "strategy_id": "sma_cross",
  "timeframe": "1h",
  "requested_start": "2024-01-01T00:00:00Z",
  "requested_end": "2024-12-31T23:59:59Z",
  "effective_start": "2024-01-01T00:00:00Z",
  "effective_end": "2024-12-31T23:00:00Z",
  "complete": true,
  "kline": {
    "cached_start": "2024-01-01T00:00:00Z",
    "cached_end": "2024-12-31T23:00:00Z",
    "missing_ranges": []
  },
  "funding": {
    "cached_start": "2024-01-01T00:00:00Z",
    "cached_end": "2024-12-31T16:00:00Z",
    "missing_ranges": []
  }
}
```

### `POST /api/data/sync`

Accepts a requested timeframe and time range, then fills missing local data for that range.

Request shape:

```json
{
  "symbol": "BTCUSDT",
  "strategy_id": "sma_cross",
  "timeframe": "1h",
  "start": "2024-01-01T00:00:00Z",
  "end": "2024-12-31T23:59:59Z"
}
```

Response shape:

```json
{
  "status": "completed",
  "symbol": "BTCUSDT",
  "strategy_id": "sma_cross",
  "timeframe": "1h",
  "requested_start": "2024-01-01T00:00:00Z",
  "requested_end": "2024-12-31T23:59:59Z",
  "effective_start": "2024-01-01T00:00:00Z",
  "effective_end": "2024-12-31T23:00:00Z",
  "complete": true,
  "downloaded": {
    "kline_rows": 8784,
    "funding_rows": 1095
  },
  "coverage": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "requested_start": "2024-01-01T00:00:00Z",
    "requested_end": "2024-12-31T23:59:59Z",
    "effective_start": "2024-01-01T00:00:00Z",
    "effective_end": "2024-12-31T23:00:00Z",
    "complete": true,
    "kline": {
      "cached_start": "2024-01-01T00:00:00Z",
      "cached_end": "2024-12-31T23:00:00Z",
      "missing_ranges": []
    },
    "funding": {
      "cached_start": "2024-01-01T00:00:00Z",
      "cached_end": "2024-12-31T16:00:00Z",
      "missing_ranges": []
    }
  }
}
```

If sync returns `status = "no_data_available"`, the frontend must:

- stop the flow
- show a terminal empty-data message for the requested normalized range
- not call `POST /api/backtests/run`

Example `no_data_available` response:

```json
{
  "status": "no_data_available",
  "symbol": "BTCUSDT",
  "strategy_id": "sma_cross",
  "timeframe": "1h",
  "requested_start": "2024-01-01T00:00:00Z",
  "requested_end": "2024-01-02T00:00:00Z",
  "effective_start": "2024-01-01T00:00:00Z",
  "effective_end": "2024-01-01T23:00:00Z",
  "complete": false,
  "downloaded": {
    "kline_rows": 0,
    "funding_rows": 0
  },
  "coverage": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "requested_start": "2024-01-01T00:00:00Z",
    "requested_end": "2024-01-02T00:00:00Z",
    "effective_start": "2024-01-01T00:00:00Z",
    "effective_end": "2024-01-01T23:00:00Z",
    "complete": false,
    "kline": {
      "cached_start": null,
      "cached_end": null,
      "missing_ranges": [
        {
          "start": "2024-01-01T00:00:00Z",
          "end": "2024-01-01T23:00:00Z"
        }
      ]
    },
    "funding": {
      "cached_start": null,
      "cached_end": null,
      "missing_ranges": [
        {
          "start": "2024-01-01T00:00:00Z",
          "end": "2024-01-01T23:00:00Z"
        }
      ]
    }
  }
}
```

### `POST /api/backtests/run`

Accepts the normalized backtest request and returns the full normalized backtest result.

V1 can run synchronously in the request-response cycle.

Request shape:

```json
{
  "symbol": "BTCUSDT",
  "strategy_id": "sma_cross",
  "timeframe": "1h",
  "start": "2024-01-01T00:00:00Z",
  "end": "2024-12-31T23:59:59Z",
  "initial_capital": 10000,
  "leverage": 3,
  "fee_bps": 4,
  "slippage_bps": 2,
  "position_size_pct": 1.0,
  "params": {
    "fast_period": 20,
    "slow_period": 50
  }
}
```

Validation rules for this request:

- `symbol` must equal `BTCUSDT`
- `timeframe` must be one of `15m`, `1h`, `4h`, `1d`
- `start < end`
- `initial_capital > 0`
- `1 <= leverage <= 20`
- `0 <= fee_bps <= 100`
- `0 <= slippage_bps <= 100`
- `0 < position_size_pct <= 1`
- `strategy_id` must exist
- `timeframe` must be included in the selected strategy's `supported_timeframes`
- `params` must pass plugin validation
- complete kline and funding coverage must already exist for the effective normalized range plus any strategy-required warm-up bars

Response top-level shape:

Representative example only. List-valued fields such as `market_bars`, `equity_curve`, `drawdown_curve`, `monthly_returns`, `trades`, and `markers` are intentionally truncated to sample rows for brevity.

```json
{
  "run": {
    "symbol": "BTCUSDT",
    "strategy_id": "sma_cross",
    "timeframe": "1h",
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z",
    "effective_start": "2024-01-01T00:00:00Z",
    "effective_end": "2024-12-31T23:00:00Z",
    "actual_end": "2025-01-01T00:00:00Z",
    "status": "completed"
  },
  "strategy": {
    "id": "sma_cross",
    "name": "SMA Cross",
    "description": "Long/short moving-average crossover strategy."
  },
  "settings": {
    "initial_capital": 10000,
    "leverage": 3,
    "fee_bps": 4,
    "slippage_bps": 2,
    "position_size_pct": 1.0
  },
  "metrics": {
    "net_pnl": 1823.41,
    "return_pct": 0.182341,
    "annualized_return": 0.201233,
    "max_drawdown": -0.0921,
    "sharpe": 1.44,
    "sortino": 2.01,
    "calmar": 2.18,
    "total_trades": 18,
    "win_rate": 0.5556,
    "profit_factor": 1.73,
    "average_trade_return": 0.0142,
    "average_holding_time_seconds": 172800
  },
  "series": {
    "market_bars": [
      {
        "time": "2024-01-01T01:00:00Z",
        "open": 42200.0,
        "high": 42310.0,
        "low": 42180.0,
        "close": 42290.0,
        "volume": 1023.5
      }
    ],
    "equity_curve": [
      {
        "time": "2024-01-01T01:00:00Z",
        "equity": 10000.0
      }
    ],
    "drawdown_curve": [
      {
        "time": "2024-01-01T01:00:00Z",
        "drawdown": 0.0
      }
    ]
  },
  "monthly_returns": [
    {
      "month": "2024-01",
      "return_pct": 0.0312
    }
  ],
  "trades": [
    {
      "trade_id": 1,
      "side": "long",
      "entry_time": "2024-01-03T08:00:00Z",
      "exit_time": "2024-01-05T12:00:00Z",
      "entry_price": 43210.5,
      "exit_price": 44100.0,
      "quantity": 0.023,
      "allocated_margin_at_entry": 331.28,
      "notional": 993.84,
      "gross_pnl": 20.46,
      "fees": 0.8,
      "funding_pnl": -0.11,
      "net_pnl": 19.55,
      "return_pct_on_margin": 0.059,
      "holding_bars": 52,
      "holding_seconds": 187200,
      "exit_reason": "signal_flip"
    }
  ],
  "markers": [
    {
      "time": "2024-01-03T08:00:00Z",
      "price": 43210.5,
      "action": "entry_long",
      "trade_id": 1
    }
  ],
  "coverage": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "requested_start": "2024-01-01T00:00:00Z",
    "requested_end": "2024-12-31T23:59:59Z",
    "effective_start": "2024-01-01T00:00:00Z",
    "effective_end": "2024-12-31T23:00:00Z",
    "complete": true,
    "kline": {
      "cached_start": "2024-01-01T00:00:00Z",
      "cached_end": "2024-12-31T23:00:00Z",
      "missing_ranges": []
    },
    "funding": {
      "cached_start": "2024-01-01T00:00:00Z",
      "cached_end": "2024-12-31T16:00:00Z",
      "missing_ranges": []
    }
  }
}
```

## Frontend UX

V1 uses a single-page backtesting workspace.

### Main Regions

- Top configuration bar:
  - strategy
  - timeframe
  - start/end
  - initial capital
  - leverage
  - fee
  - slippage
  - position size percent
- Strategy parameter panel:
  - auto-generated from strategy schema
- Main visualization panel:
  - kline chart
  - trade markers
- Result panel:
  - summary metrics
- Lower detail area:
  - tabs for equity, drawdown, trades, monthly returns, data coverage

### Primary Flow

1. Load available strategies.
2. User selects a strategy.
3. Frontend renders strategy-specific parameters.
4. User selects time range and execution settings.
5. Frontend checks local data coverage.
6. If needed, frontend runs explicit sync.
7. Frontend starts backtest.
8. Result renders as metrics plus charts and tables.

#### Progress Semantics in V1

V1 does not introduce background jobs or streaming status APIs.

The frontend must therefore show phase-level loading states only:

- `Checking local data`
- `Syncing missing market data`
- `Running backtest`
- `Rendering result`

Those states are driven by sequential API calls and local UI state, not by server-side progress percentages.

### UX Priorities

- The main flow must be obvious without documentation.
- All execution assumptions must be visible to the user.
- Validation errors must be explicit and actionable.
- The UI should favor dense, analytical clarity over decorative marketing layout.

## Error Handling and Edge Cases

The system must explicitly handle:

- Unsupported timeframe request.
- Start time after end time.
- Strategy not found.
- Invalid strategy parameters.
- No data returned from exchange for the requested interval.
- Partial data coverage before sync.
- Binance API throttling or transient failures.
- Missing funding-rate points in a requested range.
- Strategy returns malformed signals.
- Backtest liquidates before the requested end time.
- Empty trade set.

### Error Handling Policy

- Validation errors return structured client errors.
- Exchange data failures return recoverable sync errors with context.
- Strategy execution errors return strategy-specific failure messages without crashing the service.
- Empty or degenerate runs still return a valid response object with clear status fields.

### Error Response Schema

All non-2xx API failures must use:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Human-readable summary.",
    "details": {}
  }
}
```

Allowed V1 error codes:

- `invalid_request`
- `strategy_not_found`
- `strategy_validation_error`
- `strategy_execution_error`
- `sync_failed`
- `backtest_failed`
- `data_coverage_missing`

Successful sync statuses:

- `completed`
- `no_data_available`

Successful backtest run statuses:

- `completed`
- `liquidated`

## Testing Strategy

V1 requires three test layers.

### 1. Backtest Core Tests

Must cover:

- fee application
- slippage application
- funding settlement
- next-bar-open execution timing
- long-to-short and short-to-long transitions
- isolated margin accounting
- liquidation handling
- position size percent behavior

These tests must use deterministic fixtures and assert exact equity and cash-flow outcomes.

### 2. Strategy System Tests

Must cover:

- plugin discovery
- schema loading
- broken plugin import skip behavior
- duplicate plugin id handling
- parameter validation
- malformed signal rejection
- empty-signal behavior

### 3. API and Frontend Tests

Must cover:

- strategy list rendering
- parameter form rendering from schema
- date-range submission
- data sync flow
- `sync_failed` handling
- `no_data_available` handling
- `data_coverage_missing` handling
- successful backtest rendering
- display of metrics, chart overlays, and trade list

## Metric Definitions

All portfolio return ratios in V1 use `risk_free_rate = 0`.

### Equity Curve

- Equity is sampled once per completed bar after applying realized fees, realized funding up to that timestamp, and mark-to-market unrealized PnL.
- For the final included bar, the sampled equity must be the post-forced-close equity if the end-of-range rule closes an open position.

### Bar Return Series

- `bar_return_t = (equity_t / equity_(t-1)) - 1`
- only compute `bar_return_t` when both `equity_t > 0` and `equity_(t-1) > 0`
- otherwise treat that bar return as undefined and exclude it from ratio calculations

### Annualization Factors

- `15m`: `35040`
- `1h`: `8760`
- `4h`: `2190`
- `1d`: `365`

### Annualized Return

- `elapsed_seconds = actual_end_timestamp - effective_start_timestamp`
- `year_fraction = elapsed_seconds / (365 * 24 * 3600)`
- `annualized_return = (ending_equity / starting_equity) ** (1 / year_fraction) - 1`

If `ending_equity <= 0`, `annualized_return = -1.0`.

### Net PnL

- `net_pnl = ending_equity - starting_equity`

### Return %

- `return_pct = net_pnl / starting_equity`

### Max Drawdown

- `drawdown_t = (equity_t - running_peak_t) / running_peak_t`
- `max_drawdown = min(drawdown_t)`

### Sharpe Ratio

- `sharpe = mean(bar_returns) / std(bar_returns, ddof=1) * sqrt(periods_per_year)`
- If fewer than 2 valid `bar_returns` exist, return `null`
- If the denominator is `0`, undefined, or non-finite, return `null`

### Sortino Ratio

- downside returns are `min(bar_return, 0)`
- `sortino = mean(bar_returns) / std(downside_returns, ddof=1) * sqrt(periods_per_year)`
- If fewer than 2 valid `bar_returns` exist, return `null`
- If downside deviation is `0`, undefined, or non-finite, return `null`

### Calmar Ratio

- `calmar = annualized_return / abs(max_drawdown)`
- If `max_drawdown == 0`, return `null`

### Empty or Degenerate Runs

- Count metrics return `0`
- Ratio metrics that are mathematically undefined return `null`
- An empty trade set is valid if the strategy never enters
- The response must still include a full result object

### End-of-Range Rule

If a position is still open at the end of the requested range:

- force-close it at the final available bar close within the requested range
- apply configured slippage and exit fee
- mark the trade `exit_reason = "end_of_range"`

This forced close happens after any funding events strictly earlier than or equal to the final bar timestamp have been applied.

All summary metrics, monthly returns, and the final equity-curve point must use the post-forced-close final bar equity.

If `POST /api/backtests/run` is called before the required effective range plus any strategy-required warm-up bars are fully cached, the API must fail with `data_coverage_missing` and must not attempt implicit synchronization.

### Trade-Derived Metrics

Closed-trade definitions:

- `total_trades = number of closed trades`
- `winning_trades = count of closed trades where net_pnl > 0`
- `losing_trades = count of closed trades where net_pnl < 0`
- `gross_profit = sum(net_pnl for trades where net_pnl > 0)`
- `gross_loss = sum(net_pnl for trades where net_pnl < 0)`
- `trade_return_pct_on_margin = net_pnl / allocated_margin_at_entry`

Metric formulas:

- `win_rate = winning_trades / total_trades`
- `profit_factor = gross_profit / abs(gross_loss)`
- `average_trade_return = mean(trade_return_pct_on_margin)`
- `average_holding_time_seconds = mean(holding_seconds)`

Undefined-case handling:

- if `total_trades == 0`, `win_rate = null`
- if `gross_loss == 0`, `profit_factor = null`
- if `total_trades == 0`, `average_trade_return = null`
- if `total_trades == 0`, `average_holding_time_seconds = null`

### Monthly Returns

Monthly returns use UTC calendar months.

For each UTC month intersecting the effective range:

- `month_open_equity` = the latest equity immediately before the first included bar of that month, or `starting_equity` if none exists within the effective range
- `month_close_equity` = the equity at the final included bar close of that month after all events for that bar are processed
- `monthly_return_pct = (month_close_equity / month_open_equity) - 1`

Partial first and last months are included using the same rule.

## Why This Architecture

This design deliberately keeps the core units independently understandable:

- Strategies define signals.
- Data layer provides historical inputs.
- Execution layer turns signals into perpetual-futures outcomes.
- Analytics layer turns outcomes into professional reporting.
- Frontend configures runs and displays results.

Those boundaries reduce coupling, keep the platform testable, and avoid locking the entire codebase to one framework's internal object model.

## Future Extensions

These are explicitly deferred, not partially designed in V1:

- More symbols
- Spot and futures side-by-side
- Parameter optimization jobs
- Walk-forward analysis
- Portfolio-level backtests
- Strategy comparison dashboard
- Multi-position engines
- Async task queue for long-running runs
- Optional Backtesting.py compatibility adapter outside the runtime product path

## Decision Summary

V1 will be a local web platform for Binance `BTCUSDT` perpetual backtesting with:

- `FastAPI` backend
- `React + Vite` frontend
- local strategy plugin discovery
- Binance public historical data sync
- local cached market data
- custom perpetual execution engine for runtime backtests
- isolated margin, fixed leverage, long/short support
- fees, slippage, and funding included in results
- professional metrics and charted outputs

This scope is intentionally narrow enough for a single implementation plan while still producing a credible quantitative backtesting product.
