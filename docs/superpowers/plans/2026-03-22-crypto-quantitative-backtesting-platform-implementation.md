# Crypto Quantitative Backtesting Platform Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web-based Binance `BTCUSDT` perpetual futures backtesting platform with strategy plugins, explicit market-data sync, credible perpetual execution rules, professional analytics, and a React workspace UI.

**Architecture:** The backend is a FastAPI application with isolated modules for strategy discovery, Binance data synchronization, local DuckDB caching, perpetual backtest execution, and analytics serialization. The frontend is a React + Vite single-page workspace that drives explicit data sync, submits backtest runs, and renders kline, equity, drawdown, metrics, and trade detail views from backend contracts.

**Tech Stack:** Python 3.14 local interpreter -> `.venv`, FastAPI, Pydantic v2, pandas, duckdb, httpx, pytest, React, TypeScript, Vite, Lightweight Charts, Playwright, npm.

---

## File Structure

### Root

- Create: `.gitignore`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `package-lock.json`

### Backend Application

- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/api/strategies.py`
- Create: `backend/app/api/data.py`
- Create: `backend/app/api/backtests.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/common.py`
- Create: `backend/app/models/strategies.py`
- Create: `backend/app/models/data_sync.py`
- Create: `backend/app/models/backtests.py`
- Create: `backend/app/strategies/base.py`
- Create: `backend/app/strategies/discovery.py`
- Create: `backend/app/data/binance_client.py`
- Create: `backend/app/data/coverage.py`
- Create: `backend/app/data/repository.py`
- Create: `backend/app/data/sync_service.py`
- Create: `backend/app/backtest/contracts.py`
- Create: `backend/app/backtest/indicators.py`
- Create: `backend/app/backtest/engine.py`
- Create: `backend/app/backtest/liquidation.py`
- Create: `backend/app/backtest/analytics.py`
- Create: `backend/app/services/backtest_service.py`
- Create: `backend/app/db.py`

### Local Strategy Plugins

- Create: `backend/strategies/__init__.py`
- Create: `backend/strategies/sma_cross.py`

### Backend Tests

- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health_api.py`
- Create: `backend/tests/strategies/test_discovery.py`
- Create: `backend/tests/data/test_repository.py`
- Create: `backend/tests/data/test_sync_service.py`
- Create: `backend/tests/backtest/test_engine.py`
- Create: `backend/tests/backtest/test_liquidation.py`
- Create: `backend/tests/backtest/test_analytics.py`
- Create: `backend/tests/api/test_strategies_api.py`
- Create: `backend/tests/api/test_data_api.py`
- Create: `backend/tests/api/test_backtests_api.py`

### Frontend

- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/formatters.ts`
- Create: `frontend/src/hooks/useStrategies.ts`
- Create: `frontend/src/hooks/useCoverage.ts`
- Create: `frontend/src/hooks/useRunBacktest.ts`
- Create: `frontend/src/types/contracts.ts`
- Create: `frontend/src/components/TopBar.tsx`
- Create: `frontend/src/components/StrategyPanel.tsx`
- Create: `frontend/src/components/KlineChart.tsx`
- Create: `frontend/src/components/MetricsGrid.tsx`
- Create: `frontend/src/components/EquityChart.tsx`
- Create: `frontend/src/components/DrawdownChart.tsx`
- Create: `frontend/src/components/TradesTable.tsx`
- Create: `frontend/src/components/MonthlyReturnsTable.tsx`
- Create: `frontend/src/components/DataCoveragePanel.tsx`
- Create: `frontend/src/components/StatusBanner.tsx`
- Create: `frontend/src/components/EmptyState.tsx`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/test/msw.ts`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/tests/e2e/backtest-workspace.spec.ts`

### Execution Notes

- Use `D:\python3.14\python.exe` only to create `.venv`; all later Python commands must use `.\.venv\Scripts\python.exe`.
- Use npm everywhere on the frontend and root Node tasks.
- After each task commit, push to `origin codex/quant-backtesting-platform`.

## Chunk 1: Foundation, Strategy Plugins, and Market Data

### Task 1: Scaffold the repo, toolchains, and baseline app shells

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `backend/tests/conftest.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/db.py`
- Create: `backend/tests/test_health_api.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/App.test.tsx`
- Test: `backend/tests/test_health_api.py`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write the failing backend and frontend smoke tests**

```python
from fastapi.testclient import TestClient
from backend.app.main import create_app

def test_health_endpoint_reports_ok():
    client = TestClient(create_app())
    assert client.get("/api/health").json() == {"status": "ok"}
```

```tsx
import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders workspace shell", () => {
  render(<App />);
  expect(screen.getByText(/quantitative backtesting workspace/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the smoke tests to confirm the repo has no implementation yet**

Run: `D:\python3.14\python.exe -m pytest backend/tests/test_health_api.py -q`  
Expected: FAIL with import or file-not-found errors

Run: `npm --prefix frontend test -- --runInBand`  
Expected: FAIL because the frontend package does not exist yet

- [ ] **Step 3: Create the baseline toolchain and app shell**

```toml
[project]
name = "crypto-quant-backtesting"
version = "0.1.0"
dependencies = ["fastapi", "uvicorn", "pydantic", "duckdb", "pandas", "httpx"]
```

```python
def create_app() -> FastAPI:
    app = FastAPI(title="Crypto Quantitative Backtesting Platform")
    app.include_router(health_router, prefix="/api")
    return app
```

```tsx
export default function App() {
  return <main><h1>Quantitative Backtesting Workspace</h1></main>;
}
```

- [ ] **Step 4: Install dependencies and run the smoke tests again**

Run: `D:\python3.14\python.exe -m venv .venv`  
Expected: `.venv` directory created

Run: `.\.venv\Scripts\python.exe -m pip install -e .[dev]`  
Expected: installs backend and pytest extras without errors

Run: `npm install`  
Expected: root Node scripts installed

Run: `npm --prefix frontend install`  
Expected: frontend dependencies installed

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/test_health_api.py -q`  
Expected: PASS

Run: `npm --prefix frontend test -- --runInBand`  
Expected: PASS

- [ ] **Step 5: Commit and push the scaffold**

```bash
git add .gitignore README.md pyproject.toml package.json package-lock.json backend frontend
git commit -m "feat: scaffold crypto backtesting workspace"
git push -u origin codex/quant-backtesting-platform
```

### Task 2: Define strategy contracts and local plugin discovery

**Files:**
- Create: `backend/app/models/common.py`
- Create: `backend/app/models/strategies.py`
- Create: `backend/app/strategies/base.py`
- Create: `backend/app/strategies/discovery.py`
- Create: `backend/strategies/__init__.py`
- Create: `backend/strategies/sma_cross.py`
- Create: `backend/tests/strategies/test_discovery.py`
- Create: `backend/tests/api/test_strategies_api.py`
- Modify: `backend/app/main.py`
- Create: `backend/app/api/strategies.py`

- [ ] **Step 1: Write failing tests for plugin discovery and strategy listing**

```python
def test_discovery_skips_invalid_plugins_and_returns_warnings():
    strategies, warnings = discover_strategies(Path("backend/strategies"))
    assert [strategy.id for strategy in strategies] == ["sma_cross"]
    assert {"file": "broken_plugin.py", "reason": "ImportError: missing dependency"} in warnings
    assert {"file": "duplicate_sma_cross.py", "reason": "duplicate id 'sma_cross'"} in warnings
```

```python
def test_strategies_api_returns_schema_and_warnings(client):
    payload = client.get("/api/strategies").json()
    assert payload["strategies"] == [
        {
            "id": "sma_cross",
            "name": "SMA Cross",
            "description": "Long/short moving-average crossover strategy.",
            "supported_timeframes": ["15m", "1h", "4h", "1d"],
            "required_lookback_bars": 200,
            "parameter_schema": [
                {
                    "key": "fast_period",
                    "label": "Fast Period",
                    "type": "integer",
                    "default": 20,
                    "required": True,
                    "min": 1,
                    "max": 500,
                    "step": 1,
                    "help": "Short moving average period."
                },
                {
                    "key": "slow_period",
                    "label": "Slow Period",
                    "type": "integer",
                    "default": 50,
                    "required": True,
                    "min": 2,
                    "max": 500,
                    "step": 1,
                    "help": "Long moving average period."
                }
            ]
        }
    ]
    assert payload["discovery_warnings"] == [
        {"file": "broken_plugin.py", "reason": "ImportError: missing dependency"},
        {"file": "duplicate_sma_cross.py", "reason": "duplicate id 'sma_cross'"}
    ]
```

- [ ] **Step 2: Run the discovery tests to verify the contract is not implemented**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/strategies/test_discovery.py backend/tests/api/test_strategies_api.py -q`  
Expected: FAIL with missing models, routers, or strategy modules

- [ ] **Step 3: Implement the strategy base contract, discovery, and sample plugin**

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
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def compute_indicators(cls, df: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        raise NotImplementedError
```

```python
class SmaCrossStrategy(BaseStrategyPlugin):
    id = "sma_cross"
    supported_timeframes = ("15m", "1h", "4h", "1d")
    required_lookback_bars = 200

    @classmethod
    def validate_params(cls, params: Mapping[str, Any]) -> dict[str, Any]:
        fast = int(params["fast_period"])
        slow = int(params["slow_period"])
        if fast >= slow:
            raise StrategyValidationError("fast_period must be less than slow_period")
        return {"fast_period": fast, "slow_period": slow}

    @classmethod
    def compute_indicators(cls, df: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "fast_sma": df["close"].rolling(params["fast_period"]).mean(),
                "slow_sma": df["close"].rolling(params["slow_period"]).mean(),
            },
            index=df.index,
        )

    @classmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        signals = pd.Series(0, index=df.index, dtype="int8")
        signals.loc[indicators["fast_sma"] > indicators["slow_sma"]] = 1
        signals.loc[indicators["fast_sma"] < indicators["slow_sma"]] = -1
        return signals
```

- [ ] **Step 3a: Preserve spec-required discovery behavior**

Implement discovery so that:
- import failures are skipped and appended to `discovery_warnings` as `{file, reason}`
- invalid contracts are skipped and appended to `discovery_warnings` as `{file, reason}`
- duplicate strategy ids cause all colliding plugins to be skipped and appended to `discovery_warnings` as `{file, reason}`
- `generate_signals` output must be aligned to `df.index` and contain only `-1`, `0`, or `1`

- [ ] **Step 4: Wire the strategies API and rerun the tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/strategies/test_discovery.py backend/tests/api/test_strategies_api.py -q`  
Expected: PASS

- [ ] **Step 5: Commit and push the strategy plugin system**

```bash
git add backend/app/models/common.py backend/app/models/strategies.py backend/app/strategies backend/strategies backend/app/api/strategies.py backend/app/main.py backend/tests/strategies/test_discovery.py backend/tests/api/test_strategies_api.py
git commit -m "feat: add strategy discovery and metadata api"
git push origin codex/quant-backtesting-platform
```

### Task 3: Implement DuckDB storage, Binance data sync, and coverage APIs

**Files:**
- Create: `backend/app/models/data_sync.py`
- Create: `backend/app/data/binance_client.py`
- Create: `backend/app/data/repository.py`
- Create: `backend/app/data/coverage.py`
- Create: `backend/app/data/sync_service.py`
- Create: `backend/app/api/data.py`
- Create: `backend/tests/data/test_repository.py`
- Create: `backend/tests/data/test_sync_service.py`
- Create: `backend/tests/api/test_data_api.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/db.py`

- [ ] **Step 1: Write failing tests for cache coverage, sync semantics, and data APIs**

```python
def test_status_reports_missing_ranges_with_warmup_strategy_scope(status_client):
    payload = status_client.get(
        "/api/data/status",
        params={
            "strategy_id": "sma_cross",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z"
        },
    ).json()
    assert payload["complete"] is False
    assert payload["effective_start"] == "2024-01-01T00:00:00Z"
    assert payload["kline"]["missing_ranges"][0]["start"] == "2023-12-23T16:00:00Z"
    assert payload["funding"]["missing_ranges"] == []
```

```python
def test_sync_returns_no_data_available_without_triggering_run(sync_client, httpx_mock):
    payload = sync_client.post(
        "/api/data/sync",
        json={
            "strategy_id": "sma_cross",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-03T23:59:59Z"
        },
    ).json()
    assert payload["status"] == "no_data_available"
    assert payload["coverage"]["complete"] is False
```

```python
def test_sync_retries_429_and_upserts_without_duplicates(sync_service, httpx_mock):
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=200, json=[BINANCE_KLINE_ROW])
    result = anyio.run(sync_service.sync_market_data, DATA_SYNC_REQUEST)
    assert result.status == "completed"
    assert count_rows("klines", symbol="BTCUSDT", timeframe="1h") == 1
```

```python
def test_sync_returns_sync_failed_when_funding_gap_remains(sync_service, httpx_mock):
    httpx_mock.add_response(status_code=200, json=[BINANCE_KLINE_ROW])
    httpx_mock.add_response(status_code=500, json={"code": -1, "msg": "server error"})
    result = anyio.run(sync_service.sync_market_data, DATA_SYNC_REQUEST)
    assert result.status == "sync_failed"
    assert result.error.code == "sync_failed"
```

- [ ] **Step 2: Run the data tests to confirm repository and services are missing**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/data/test_repository.py backend/tests/data/test_sync_service.py backend/tests/api/test_data_api.py -q`  
Expected: FAIL with missing repository, coverage, or API implementations

- [ ] **Step 3: Implement DuckDB schema, Binance public API client, and sync service**

```python
CREATE TABLE IF NOT EXISTS klines (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open_time TIMESTAMP NOT NULL,
    close_time TIMESTAMP NOT NULL,
    open DOUBLE NOT NULL,
    high DOUBLE NOT NULL,
    low DOUBLE NOT NULL,
    close DOUBLE NOT NULL,
    volume DOUBLE NOT NULL,
    PRIMARY KEY(symbol, timeframe, open_time)
);

CREATE TABLE IF NOT EXISTS funding_rates (
    symbol TEXT NOT NULL,
    funding_time TIMESTAMP NOT NULL,
    funding_rate DOUBLE NOT NULL,
    PRIMARY KEY(symbol, funding_time)
);
```

```python
async def sync_market_data(request: DataSyncRequest) -> DataSyncResult:
    coverage_target = build_coverage_target(request=request)
    kline_gaps = coverage_service.find_missing_kline_ranges(coverage_target)
    funding_gaps = coverage_service.find_missing_funding_ranges(coverage_target)
    await binance_client.sync_klines(gaps=kline_gaps, retry_seconds=[1, 2, 4, 8, 16])
    await binance_client.sync_funding_rates(gaps=funding_gaps, retry_seconds=[1, 2, 4, 8, 16])
    final_coverage = coverage_service.get_status(coverage_target)
    return build_sync_result(request=request, coverage=final_coverage)
```

- [ ] **Step 3a: Explicitly implement gap detection rules from the spec**

Implement coverage checks so they independently verify:
- all required warm-up bars exist before `effective_start`
- all expected kline bars exist between `effective_start` and `effective_end`
- all expected funding timestamps exist between `effective_start` and `effective_end`

- [ ] **Step 4: Implement `/api/data/status` and `/api/data/sync`, then rerun the tests**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/data/test_repository.py backend/tests/data/test_sync_service.py backend/tests/api/test_data_api.py -q`  
Expected: PASS

- [ ] **Step 5: Commit and push the market-data layer**

```bash
git add backend/app/models/data_sync.py backend/app/data backend/app/api/data.py backend/app/main.py backend/app/db.py backend/tests/data backend/tests/api/test_data_api.py
git commit -m "feat: add binance market data sync and coverage apis"
git push origin codex/quant-backtesting-platform
```

## Chunk 2: Execution Engine, HTTP Integration, and Frontend Workspace

### Task 4: Implement perpetual execution, funding, liquidation, and analytics

**Files:**
- Create: `backend/app/backtest/contracts.py`
- Create: `backend/app/backtest/indicators.py`
- Create: `backend/app/backtest/liquidation.py`
- Create: `backend/app/backtest/engine.py`
- Create: `backend/app/backtest/analytics.py`
- Create: `backend/tests/backtest/test_engine.py`
- Create: `backend/tests/backtest/test_liquidation.py`
- Create: `backend/tests/backtest/test_analytics.py`

- [ ] **Step 1: Write failing execution tests for fills, fees, funding, flips, liquidation, and summary metrics**

```python
def test_engine_executes_on_next_bar_open_and_applies_costs(sample_dataset, sma_plugin):
    result = run_backtest(dataset=sample_dataset, plugin=sma_plugin, request=backtest_request)
    assert result.trades[0].entry_time.isoformat() == "2024-01-01T01:00:00+00:00"
    assert result.trades[0].fees == pytest.approx(0.80, rel=1e-6)
    assert result.bar_snapshots[0].equity == pytest.approx(10000.0, rel=1e-6)
```

```python
def test_engine_flips_using_post_close_equity(sample_flip_dataset, sma_plugin):
    result = run_backtest(dataset=sample_flip_dataset, plugin=sma_plugin, request=backtest_request)
    assert result.trades[0].exit_reason == "signal_flip"
    assert result.trades[1].allocated_margin_at_entry == pytest.approx(338.10, rel=1e-6)
```

```python
def test_funding_and_bar_open_ordering_follow_spec(sample_funding_dataset, sma_plugin):
    result = run_backtest(dataset=sample_funding_dataset, plugin=sma_plugin, request=backtest_request)
    assert result.funding_events[0].applied_before_open_fill is True
    assert result.trades[0].funding_pnl == pytest.approx(-1.24, rel=1e-6)
```

```python
def test_liquidation_stops_run_and_sets_actual_end(sample_liquidation_dataset, sma_plugin):
    result = run_backtest(dataset=sample_liquidation_dataset, plugin=sma_plugin, request=backtest_request)
    assert result.run.status == "liquidated"
    assert result.run.actual_end.isoformat() == "2024-02-01T04:00:00+00:00"
    assert result.run.final_equity == pytest.approx(0.0, rel=1e-6)
```

```python
def test_engine_forces_close_at_final_bar_and_uses_terminal_close_for_actual_end(sample_final_bar_dataset, sma_plugin):
    result = run_backtest(dataset=sample_final_bar_dataset, plugin=sma_plugin, request=backtest_request)
    assert result.run.status == "completed"
    assert result.run.actual_end.isoformat() == "2024-01-31T01:00:00+00:00"
    assert result.trades[-1].exit_reason == "end_of_range"
```

```python
def test_engine_rejects_malformed_signal_series(sample_dataset, bad_signal_plugin):
    with pytest.raises(StrategyExecutionError):
        run_backtest(dataset=sample_dataset, plugin=bad_signal_plugin, request=backtest_request)
```

```python
def test_engine_allows_empty_trade_set_and_returns_full_result(flat_signal_dataset, flat_signal_plugin):
    result = run_backtest(dataset=flat_signal_dataset, plugin=flat_signal_plugin, request=backtest_request)
    assert result.trades == []
    metrics = build_metrics(result)
    assert metrics.total_trades == 0
```

```python
def test_analytics_computes_sharpe_drawdown_and_average_trade_return(sample_execution_result):
    metrics = build_metrics(sample_execution_result)
    assert metrics.max_drawdown == pytest.approx(-0.0921, rel=1e-4)
    assert metrics.sharpe == pytest.approx(1.44, rel=1e-4)
    assert metrics.average_trade_return == pytest.approx(0.059, rel=1e-6)
```

- [ ] **Step 2: Run the backtest tests to verify the engine is not implemented**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/backtest/test_engine.py backend/tests/backtest/test_liquidation.py backend/tests/backtest/test_analytics.py -q`  
Expected: FAIL with missing contracts and execution engine code

- [ ] **Step 3: Implement the execution contracts, perpetual engine, liquidation rules, and analytics serializer**

```python
def run_backtest(dataset: MarketDataBundle, plugin: BaseStrategyPlugin, request: BacktestRunRequest) -> BacktestExecutionResult:
    ledger = AccountLedger(free_cash=request.initial_capital)
    indicators = plugin.compute_indicators(dataset.klines, request.params)
    signals = plugin.generate_signals(dataset.klines, indicators, request.params)
    validate_signal_series(signals=signals, expected_index=dataset.klines.index)
    for bar in iterate_bars(dataset):
        apply_open_timestamp_funding(ledger, bar)
        execute_scheduled_orders(ledger, bar, request)
        apply_intrabar_funding(ledger, bar)
        evaluate_intrabar_liquidation(ledger, bar, request)
        capture_bar_snapshot(ledger, bar)
    return finalize_run_with_forced_close(ledger, dataset.final_bar)
```

```python
def calculate_liquidation_price(
    side: PositionSide,
    entry_price: float,
    quantity: float,
    isolated_margin_balance: float,
    maintenance_margin_rate: float,
) -> float:
    if side == "long":
        return (entry_price * quantity - isolated_margin_balance) / (quantity * (1 - maintenance_margin_rate))
    return (entry_price * quantity + isolated_margin_balance) / (quantity * (1 + maintenance_margin_rate))
```

- [ ] **Step 3a: Add targeted regressions and matching branches for the remaining event-order rules**

Add one focused regression test and one implementation branch for each of these rules:
- same-side repeated signals leave the existing position open and do not append a new trade
- `0` while flat leaves `free_cash`, `isolated_margin_balance`, and `total_equity` unchanged
- funding events use the latest close at or before the funding timestamp as their reference price
- liquidation settlement applies `free_cash += max(isolated_margin_balance + realized_trade_pnl - exit_fee, 0)` and zeroes isolated balances
- annualized return, average holding time, and the final equity point are computed from `actual_end`
- malformed strategy signals abort the run with `strategy_execution_error`
- an all-flat signal series returns a successful empty trade set and a full result object

- [ ] **Step 4: Rerun the execution tests and add one focused regression for same-side repeat signals**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/backtest/test_engine.py backend/tests/backtest/test_liquidation.py backend/tests/backtest/test_analytics.py -q`  
Expected: PASS

- [ ] **Step 5: Commit and push the execution engine**

```bash
git add backend/app/backtest backend/tests/backtest
git commit -m "feat: add perpetual backtest engine and analytics"
git push origin codex/quant-backtesting-platform
```

### Task 5: Integrate the backtest service and FastAPI endpoints

**Files:**
- Create: `backend/app/models/backtests.py`
- Create: `backend/app/services/backtest_service.py`
- Create: `backend/app/api/backtests.py`
- Create: `backend/tests/api/test_backtests_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing API tests for validation, coverage enforcement, and serialized results**

```python
def test_run_endpoint_rejects_missing_coverage(api_client):
    response = api_client.post("/api/backtests/run", json=MISSING_COVERAGE_REQUEST)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "data_coverage_missing"
```

```python
def test_run_endpoint_rejects_unknown_strategy(api_client):
    response = api_client.post("/api/backtests/run", json={**VALID_REQUEST, "strategy_id": "does_not_exist"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "strategy_not_found"
```

```python
def test_run_endpoint_rejects_invalid_request_shape(api_client):
    response = api_client.post("/api/backtests/run", json={"strategy_id": "sma_cross"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
```

```python
def test_run_endpoint_rejects_invalid_strategy_params(api_client):
    response = api_client.post(
        "/api/backtests/run",
        json={**VALID_REQUEST, "params": {"fast_period": 50, "slow_period": 20}},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "strategy_validation_error"
```

```python
def test_run_endpoint_returns_metrics_series_and_trade_rows(api_client, seeded_market_data):
    payload = api_client.post("/api/backtests/run", json=VALID_REQUEST).json()
    assert payload["metrics"]["total_trades"] >= 0
    assert "market_bars" in payload["series"]
    assert payload["run"]["status"] == "completed"
```

```python
def test_run_endpoint_wraps_unexpected_engine_error(api_client, monkeypatch):
    monkeypatch.setattr("backend.app.services.backtest_service.run_backtest", raise_runtime_error)
    response = api_client.post("/api/backtests/run", json=VALID_REQUEST)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "backtest_failed"
```

- [ ] **Step 2: Run the API tests to verify the backtest service is not wired**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests/api/test_backtests_api.py -q`  
Expected: FAIL with missing request models, routers, or service wiring

- [ ] **Step 3: Implement the request/response models, orchestration service, and run endpoint**

```python
@router.post("/backtests/run", response_model=BacktestRunResponse)
def run_backtest_endpoint(request: BacktestRunRequest) -> BacktestRunResponse:
    return backtest_service.run(request=request)
```

- [ ] **Step 3a: Implement the standard error envelope across validation and runtime failures**

Return a concrete error envelope shaped like `{"error": {"code": "strategy_validation_error", "message": "fast_period must be less than slow_period", "details": {"field": "fast_period"}}}` for:
- `invalid_request`
- `strategy_not_found`
- `strategy_validation_error`
- `strategy_execution_error`
- `data_coverage_missing`
- `backtest_failed`

- [ ] **Step 4: Run the full backend test suite**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests -q`  
Expected: PASS

- [ ] **Step 5: Commit and push the backend integration layer**

```bash
git add backend/app/models/backtests.py backend/app/services/backtest_service.py backend/app/api/backtests.py backend/app/main.py backend/tests/api/test_backtests_api.py
git commit -m "feat: expose backtest execution api"
git push origin codex/quant-backtesting-platform
```

### Task 6: Build the React backtesting workspace and contract-aware UI

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/formatters.ts`
- Create: `frontend/src/types/contracts.ts`
- Create: `frontend/src/hooks/useStrategies.ts`
- Create: `frontend/src/hooks/useCoverage.ts`
- Create: `frontend/src/hooks/useRunBacktest.ts`
- Create: `frontend/src/components/TopBar.tsx`
- Create: `frontend/src/components/StrategyPanel.tsx`
- Create: `frontend/src/components/KlineChart.tsx`
- Create: `frontend/src/components/MetricsGrid.tsx`
- Create: `frontend/src/components/EquityChart.tsx`
- Create: `frontend/src/components/DrawdownChart.tsx`
- Create: `frontend/src/components/TradesTable.tsx`
- Create: `frontend/src/components/MonthlyReturnsTable.tsx`
- Create: `frontend/src/components/DataCoveragePanel.tsx`
- Create: `frontend/src/components/StatusBanner.tsx`
- Create: `frontend/src/components/EmptyState.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/test/msw.ts`
- Create: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing frontend tests for strategy loading, explicit sync, and result rendering**

```tsx
test("blocks run until coverage is complete or sync succeeds", async () => {
  render(<App />);
  expect(await screen.findByText(/data sync required/i)).toBeInTheDocument();
  expect(screen.getByText(/checking local data/i)).toBeInTheDocument();
});
```

```tsx
test("renders schema-driven parameter inputs from the selected strategy", async () => {
  render(<App />);
  expect(await screen.findByLabelText(/fast period/i)).toHaveValue(20);
  expect(screen.getByLabelText(/slow period/i)).toHaveValue(50);
});
```

```tsx
test("renders sync and run error states from backend contracts", async () => {
  server.use(syncFailureHandler, noDataAvailableHandler, coverageMissingHandler);
  render(<App />);
  expect(await screen.findByText(/unable to sync market data/i)).toBeInTheDocument();
  expect(screen.getByText(/requested range has no exchange data/i)).toBeInTheDocument();
  expect(screen.getByText(/data coverage is incomplete/i)).toBeInTheDocument();
});
```

```tsx
test("renders metrics and trades after a successful run", async () => {
  render(<App />);
  expect(await screen.findByText(/max drawdown/i)).toBeInTheDocument();
  expect(screen.getByRole("table", { name: /trade list/i })).toBeInTheDocument();
  expect(screen.getByText(/monthly returns/i)).toBeInTheDocument();
  expect(screen.getByText(/entry_long/i)).toBeInTheDocument();
  expect(screen.getByText(/rendering result/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the frontend tests to confirm the workspace is not implemented**

Run: `npm --prefix frontend test -- --runInBand`  
Expected: FAIL because hooks, components, and API mocks are missing

- [ ] **Step 3: Implement the contract types, data hooks, workspace layout, and charts**

```tsx
function App() {
  return (
    <WorkspaceShell
      topBar={<TopBar />}
      strategyPanel={<StrategyPanel />}
      statusBanner={<StatusBanner />}
      charts={<><KlineChart /><EquityChart /><DrawdownChart /></>}
      details={<><MetricsGrid /><TradesTable /><MonthlyReturnsTable /><DataCoveragePanel /></>}
    />
  );
}
```

```ts
export async function runBacktest(input: BacktestRunRequest): Promise<BacktestRunResponse> {
  return fetchJson("/api/backtests/run", { method: "POST", body: JSON.stringify(input) });
}
```

- [ ] **Step 3a: Implement the spec-required frontend phases and error handling**

The UI must surface these phases exactly:
- `Checking local data`
- `Syncing missing market data`
- `Running backtest`
- `Rendering result`

The UI must also render distinct failure states for:
- `sync_failed`
- `no_data_available`
- `data_coverage_missing`

The strategy form must be generated from `parameter_schema`, not hardcoded to SMA inputs.
If the backend returns `no_data_available`, the UI must stop before calling `POST /api/backtests/run`.

- [ ] **Step 4: Run frontend tests and verify responsive layout manually**

Run: `npm --prefix frontend test -- --runInBand`  
Expected: PASS

Run: `npm --prefix frontend run build`  
Expected: PASS

Run: `npm --prefix frontend run dev`  
Expected: local workspace opens with a single-page dashboard shell

- [ ] **Step 5: Commit and push the frontend workspace**

```bash
git add frontend
git commit -m "feat: add backtesting workspace ui"
git push origin codex/quant-backtesting-platform
```

### Task 7: Add end-to-end coverage, developer docs, and release verification

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/tests/e2e/backtest-workspace.spec.ts`
- Modify: `README.md`
- Modify: `package.json`

- [ ] **Step 1: Write the failing end-to-end spec for the full explicit-sync and run flow**

```ts
test("syncs data explicitly and renders a completed backtest", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /sync data/i }).click();
  await page.getByRole("button", { name: /run backtest/i }).click();
  await expect(page.getByText(/sharpe/i)).toBeVisible();
});
```

- [ ] **Step 2: Run the E2E spec and confirm it fails before Playwright wiring**

Run: `npm --prefix frontend run test:e2e -- --project=chromium`  
Expected: FAIL with missing config, app boot, or selectors

- [ ] **Step 3: Implement Playwright config, stable selectors, root scripts, and README runbook**

```json
{
  "scripts": {
    "dev": "npm --prefix frontend run dev",
    "test": "npm --prefix frontend test -- --runInBand",
    "test:e2e": "npm --prefix frontend run test:e2e"
  }
}
```

- [ ] **Step 4: Run the final verification suite**

Run: `.\.venv\Scripts\python.exe -m pytest backend/tests -q`  
Expected: PASS

Run: `npm --prefix frontend test -- --runInBand`  
Expected: PASS

Run: `npm --prefix frontend run test:e2e -- --project=chromium`  
Expected: PASS

Run: `npm --prefix frontend run build`  
Expected: PASS

- [ ] **Step 5: Commit and push the verified release candidate**

```bash
git add README.md package.json package-lock.json frontend/playwright.config.ts frontend/tests/e2e/backtest-workspace.spec.ts
git commit -m "test: add end-to-end coverage and runbook"
git push origin codex/quant-backtesting-platform
```

## Execution Constraints

- Do not add multi-symbol support, optimization sweeps, auth, or live trading code in V1.
- Do not let strategies bypass fee, slippage, funding, or liquidation accounting.
- Do not auto-sync inside `POST /api/backtests/run`; preserve explicit sync semantics.
- Keep result contracts aligned with the approved spec document at `docs/superpowers/specs/2026-03-22-crypto-quantitative-backtesting-platform-design.md`.
- Favor small focused modules over large utility files.
- Every task must pass its own tests before moving to the next one.
- Every task commit must be pushed to `origin codex/quant-backtesting-platform` before the next task starts.

Plan complete and saved to `docs/superpowers/plans/2026-03-22-crypto-quantitative-backtesting-platform-implementation.md`. Ready to execute via subagent-driven development.
