import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";

import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

import { CommandBar } from "./components/CommandBar";
import { ConfigRail } from "./components/ConfigRail";
import { DataCoveragePanel } from "./components/DataCoveragePanel";
import { DrawdownChart } from "./components/DrawdownChart";
import { EmptyState } from "./components/EmptyState";
import { EquityChart } from "./components/EquityChart";
import { KlineChart } from "./components/KlineChart";
import { MonthlyReturnsTable } from "./components/MonthlyReturnsTable";
import { ResultDock } from "./components/ResultDock";
import { SummaryRail } from "./components/SummaryRail";
import { StrategyPanel } from "./components/StrategyPanel";
import { TradeInspector } from "./components/TradeInspector";
import { TradesTable, type TradeRow } from "./components/TradesTable";
import { WorkspaceShell } from "./components/WorkspaceShell";
import { formatNumber, formatPercent, formatTimestamp } from "./lib/formatters";
import { useCoverage } from "./hooks/useCoverage";
import { useRunBacktest } from "./hooks/useRunBacktest";
import { useStrategies } from "./hooks/useStrategies";
import type {
  BacktestRunResponse,
  CoverageStatusResponse,
  JsonRecord,
  StrategyParameterField,
} from "./types/contracts";
import type { MetricItem } from "./components/MetricsGrid";
import "./styles.css";

type Theme = "light" | "dark";
type Timeframe = "15m" | "1h" | "4h" | "1d";
type ParameterValue = string | number | boolean;
type BacktestSignature = {
  strategyId: string;
  timeframe: Timeframe;
  start: string;
  end: string;
  initialCapital: number;
  leverage: number;
  feeBps: number;
  slippageBps: number;
  positionSizePct: number;
  paramsKey: string;
};

const FIXED_SYMBOL = "BTCUSDT";
const DEFAULT_TIMEFRAME: Timeframe = "1h";
const DEFAULT_FORM = {
  initialCapital: 10_000,
  leverage: 2,
  feeBps: 4,
  slippageBps: 2,
  positionSizePct: 0.95,
};

function toLocalDateTimeInput(date: Date): string {
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return offsetDate.toISOString().slice(0, 16);
}

function getDefaultRange() {
  const end = new Date();
  const start = new Date(end.getTime() - 21 * 24 * 60 * 60 * 1000);

  return {
    start: toLocalDateTimeInput(start),
    end: toLocalDateTimeInput(end),
  };
}

function toIsoString(value: string): string {
  return new Date(value).toISOString();
}

function buildDefaultParameters(fields: StrategyParameterField[]): Record<string, ParameterValue> {
  const defaults: Record<string, ParameterValue> = {};

  for (const field of fields) {
    if (
      typeof field.default === "boolean" ||
      typeof field.default === "number" ||
      typeof field.default === "string"
    ) {
      defaults[field.key] = field.default;
      continue;
    }

    if (field.type === "boolean") {
      defaults[field.key] = false;
      continue;
    }

    if (field.type === "integer" || field.type === "number" || field.type === "float") {
      defaults[field.key] = typeof field.min === "number" ? field.min : 0;
      continue;
    }

    defaults[field.key] = "";
  }

  return defaults;
}

function normalizeParameterValue(field: StrategyParameterField, value: ParameterValue): ParameterValue {
  if (field.type === "boolean") {
    return Boolean(value);
  }

  if (field.type === "integer") {
    return Number.parseInt(String(value), 10);
  }

  if (field.type === "number" || field.type === "float") {
    return Number.parseFloat(String(value));
  }

  return String(value);
}

function serializeParameterValues(values: Record<string, ParameterValue>): string {
  return JSON.stringify(
    Object.entries(values).sort(([leftKey], [rightKey]) => leftKey.localeCompare(rightKey)),
  );
}

function formatNullableMetric(
  value: number | null,
  formatter: (metric: number) => string,
  fallback = "Not enough data",
): string {
  return value === null ? fallback : formatter(value);
}

function getMetricItems(result: BacktestRunResponse): MetricItem[] {
  return [
    {
      label: "Net PnL",
      value: `${result.metrics.net_pnl >= 0 ? "+" : ""}${formatNumber(result.metrics.net_pnl, 2)}`,
      detail: `${formatNumber(result.settings.initial_capital, 2)} initial capital`,
      tone: result.metrics.net_pnl >= 0 ? "positive" : "negative",
    },
    {
      label: "Return %",
      value: formatPercent(result.metrics.return_pct, 2),
      detail: `Leverage ${formatNumber(result.settings.leverage, 1)}x`,
      tone: result.metrics.return_pct >= 0 ? "positive" : "negative",
    },
    {
      label: "Max Drawdown",
      value: formatNullableMetric(result.metrics.max_drawdown, (metric) => formatPercent(metric, 2)),
      tone:
        result.metrics.max_drawdown !== null && result.metrics.max_drawdown < -0.15
          ? "warning"
          : "neutral",
    },
    {
      label: "Sharpe",
      value: formatNullableMetric(result.metrics.sharpe, (metric) => formatNumber(metric, 2)),
    },
    {
      label: "Sortino",
      value: formatNullableMetric(result.metrics.sortino, (metric) => formatNumber(metric, 2)),
    },
    {
      label: "Calmar",
      value: formatNullableMetric(result.metrics.calmar, (metric) => formatNumber(metric, 2)),
    },
    {
      label: "Win Rate",
      value: formatNullableMetric(result.metrics.win_rate, (metric) => formatPercent(metric, 2)),
      detail: `${result.metrics.total_trades} trades`,
    },
    {
      label: "Profit Factor",
      value: formatNullableMetric(result.metrics.profit_factor, (metric) => formatNumber(metric, 2)),
    },
  ];
}

function isCoverageStatusResponse(value: unknown): value is CoverageStatusResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Partial<CoverageStatusResponse>;
  return (
    typeof candidate.symbol === "string" &&
    typeof candidate.strategy_id === "string" &&
    typeof candidate.timeframe === "string" &&
    typeof candidate.complete === "boolean" &&
    typeof candidate.kline === "object" &&
    candidate.kline !== null &&
    typeof candidate.funding === "object" &&
    candidate.funding !== null
  );
}

function getCoverageFromDetails(details: JsonRecord | undefined): CoverageStatusResponse | null {
  if (!details || !("coverage" in details)) {
    return null;
  }

  return isCoverageStatusResponse(details.coverage) ? details.coverage : null;
}

function buildRunSummary(result: BacktestRunResponse | null, phaseTitle: string, phaseDescription: string) {
  if (!result) {
    return (
      <p className="summary-copy">
        <strong>{phaseTitle}</strong>
        <span>{phaseDescription}</span>
      </p>
    );
  }

  return (
    <div className="run-summary">
      <div className="run-summary__headline">
        <strong>{result.strategy.name}</strong>
        <span className={`run-pill run-pill--${result.run.status}`}>{result.run.status}</span>
      </div>

      <dl className="run-summary__grid">
        <div>
          <dt>Range</dt>
          <dd>{formatTimestamp(result.run.effective_start)} to {formatTimestamp(result.run.actual_end)}</dd>
        </div>
        <div>
          <dt>Trades</dt>
          <dd>{result.metrics.total_trades}</dd>
        </div>
        <div>
          <dt>Leverage</dt>
          <dd>{formatNumber(result.settings.leverage, 1)}x</dd>
        </div>
        <div>
          <dt>Costs</dt>
          <dd>
            {formatNumber(result.settings.fee_bps, 1)} bps fee / {formatNumber(result.settings.slippage_bps, 1)} bps slip
          </dd>
        </div>
      </dl>
    </div>
  );
}

function buildFundingTable(trades: TradeRow[]) {
  return (
    <div className="table-scroll">
      <table className="returns-table" aria-label="Funding summary">
        <thead>
          <tr>
            <th scope="col">Trade</th>
            <th scope="col">Side</th>
            <th scope="col">Funding</th>
            <th scope="col">Fees</th>
            <th scope="col">Net PnL</th>
          </tr>
        </thead>
        <tbody>
          {trades.length === 0 ? (
            <tr>
              <td colSpan={5} className="table-empty">No funding activity is available for this run.</td>
            </tr>
          ) : (
            trades.map((trade) => (
              <tr key={`funding-${trade.trade_id}`}>
                <th scope="row">#{trade.trade_id}</th>
                <td>{trade.side}</td>
                <td>{formatNumber(trade.funding_pnl, 2)}</td>
                <td>{formatNumber(trade.fees, 2)}</td>
                <td className={trade.net_pnl >= 0 ? "table-value--positive" : "table-value--negative"}>
                  {formatNumber(trade.net_pnl, 2)}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function buildPositionsTable(trades: TradeRow[]) {
  return (
    <div className="table-scroll">
      <table className="returns-table" aria-label="Position summary">
        <thead>
          <tr>
            <th scope="col">Trade</th>
            <th scope="col">Side</th>
            <th scope="col">Qty</th>
            <th scope="col">Margin</th>
            <th scope="col">Notional</th>
            <th scope="col">Return</th>
          </tr>
        </thead>
        <tbody>
          {trades.length === 0 ? (
            <tr>
              <td colSpan={6} className="table-empty">No position history is available for this run.</td>
            </tr>
          ) : (
            trades.map((trade) => (
              <tr key={`position-${trade.trade_id}`}>
                <th scope="row">#{trade.trade_id}</th>
                <td>{trade.side}</td>
                <td>{formatNumber(trade.quantity, 6)}</td>
                <td>{formatNumber(trade.allocated_margin_at_entry, 2)}</td>
                <td>{formatNumber(trade.notional, 2)}</td>
                <td className={trade.return_pct_on_margin >= 0 ? "table-value--positive" : "table-value--negative"}>
                  {formatPercent(trade.return_pct_on_margin, 2)}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
  const defaultRange = useMemo(() => getDefaultRange(), []);
  const [theme, setTheme] = useState<Theme>("dark");
  const [selectedStrategyId, setSelectedStrategyId] = useState("");
  const [timeframe, setTimeframe] = useState<Timeframe>(DEFAULT_TIMEFRAME);
  const [startValue, setStartValue] = useState(defaultRange.start);
  const [endValue, setEndValue] = useState(defaultRange.end);
  const [initialCapital, setInitialCapital] = useState(DEFAULT_FORM.initialCapital);
  const [leverage, setLeverage] = useState(DEFAULT_FORM.leverage);
  const [feeBps, setFeeBps] = useState(DEFAULT_FORM.feeBps);
  const [slippageBps, setSlippageBps] = useState(DEFAULT_FORM.slippageBps);
  const [positionSizePct, setPositionSizePct] = useState(DEFAULT_FORM.positionSizePct);
  const [parameterValues, setParameterValues] = useState<Record<string, ParameterValue>>({});
  const [lastRunSignature, setLastRunSignature] = useState<BacktestSignature | null>(null);
  const [selectedTradeId, setSelectedTradeId] = useState<number | null>(null);

  const {
    strategies,
    discoveryWarnings,
    isLoading: isStrategiesLoading,
    error: strategiesError,
  } = useStrategies();
  const selectedStrategy = useMemo(
    () => strategies.find((strategy) => strategy.id === selectedStrategyId) ?? null,
    [selectedStrategyId, strategies],
  );

  useEffect(() => {
    if (selectedStrategyId || strategies.length === 0) {
      return;
    }

    startTransition(() => {
      setSelectedStrategyId(strategies[0].id);
    });
  }, [selectedStrategyId, strategies]);

  useEffect(() => {
    if (!selectedStrategy) {
      return;
    }

    startTransition(() => {
      setTimeframe((current) =>
        selectedStrategy.supported_timeframes.includes(current)
          ? current
          : (selectedStrategy.supported_timeframes[0] as Timeframe | undefined) ?? DEFAULT_TIMEFRAME,
      );
      setParameterValues(buildDefaultParameters(selectedStrategy.parameter_schema));
    });
  }, [selectedStrategy?.id]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  const coverageRequest = useMemo(() => {
    if (!selectedStrategy || !startValue || !endValue) {
      return null;
    }

    return {
      strategy_id: selectedStrategy.id,
      symbol: FIXED_SYMBOL,
      timeframe,
      start: toIsoString(startValue),
      end: toIsoString(endValue),
    };
  }, [endValue, selectedStrategy, startValue, timeframe]);

  const {
    coverage,
    syncResult,
    isLoading: isCoverageLoading,
    isSyncing,
    error: coverageError,
    syncCoverage,
  } = useCoverage(coverageRequest);
  const {
    result,
    isRunning,
    error: runError,
    runBacktest,
  } = useRunBacktest();
  const currentParamsKey = useMemo(
    () => serializeParameterValues(parameterValues),
    [parameterValues],
  );
  const activeResult = useMemo(() => {
    if (!result || !coverageRequest || !selectedStrategy || !lastRunSignature) {
      return null;
    }

    if (
      lastRunSignature.strategyId !== selectedStrategy.id ||
      lastRunSignature.strategyId !== result.strategy.id ||
      lastRunSignature.timeframe !== timeframe ||
      lastRunSignature.start !== startValue ||
      lastRunSignature.end !== endValue ||
      lastRunSignature.initialCapital !== initialCapital ||
      lastRunSignature.leverage !== leverage ||
      lastRunSignature.feeBps !== feeBps ||
      lastRunSignature.slippageBps !== slippageBps ||
      lastRunSignature.positionSizePct !== positionSizePct ||
      lastRunSignature.paramsKey !== currentParamsKey
    ) {
      return null;
    }

    return result;
  }, [
    coverageRequest,
    currentParamsKey,
    endValue,
    feeBps,
    initialCapital,
    leverage,
    positionSizePct,
    result,
    selectedStrategy,
    slippageBps,
    startValue,
    timeframe,
    lastRunSignature,
  ]);
  const deferredResult = useDeferredValue(activeResult);
  const visibleResult = activeResult === null ? null : deferredResult;

  useEffect(() => {
    if (!visibleResult || visibleResult.trades.length === 0) {
      setSelectedTradeId(null);
      return;
    }

    setSelectedTradeId((current) =>
      current && visibleResult.trades.some((trade) => trade.trade_id === current)
        ? current
        : visibleResult.trades[0].trade_id,
    );
  }, [visibleResult]);

  const effectiveCoverage =
    getCoverageFromDetails(runError?.details) ?? visibleResult?.coverage ?? coverage;
  const canRun = Boolean(coverage?.complete && !isSyncing && !isRunning && selectedStrategy);
  const showSyncButton = Boolean(selectedStrategy) && !isCoverageLoading;

  const phaseBanner = useMemo(() => {
    if (strategiesError) {
      return {
        tone: "error" as const,
        title: "Strategy catalogue unavailable",
        description: strategiesError.message,
      };
    }

    if (!selectedStrategy || isStrategiesLoading || isCoverageLoading) {
      return {
        tone: "info" as const,
        title: "Checking local data",
        description: "Loading strategy metadata and validating the cached BTCUSDT coverage window.",
      };
    }

    if (coverageError) {
      return {
        tone: "error" as const,
        title: "Coverage lookup failed",
        description: coverageError.message,
      };
    }

    if (isSyncing) {
      return {
        tone: "warning" as const,
        title: "Syncing missing market data",
        description: "Pulling missing Binance klines and funding rates into the local DuckDB cache.",
      };
    }

    if (syncResult?.status === "sync_failed") {
      return {
        tone: "error" as const,
        title: "Unable to sync market data",
        description: syncResult.error?.message ?? "Market data coverage remained incomplete after sync.",
      };
    }

    if (syncResult?.status === "no_data_available") {
      return {
        tone: "warning" as const,
        title: "Requested range has no exchange data",
        description: "Binance does not expose tradable history for the selected window. Choose a later range and retry.",
      };
    }

    if (isRunning) {
      return {
        tone: "info" as const,
        title: "Running backtest",
        description: "Evaluating the strategy with leverage, funding, fees, and slippage applied.",
      };
    }

    if (runError?.code === "data_coverage_missing") {
      return {
        tone: "error" as const,
        title: "Data coverage is incomplete",
        description: "The run was blocked because the required market data window is still missing.",
      };
    }

    if (runError) {
      return {
        tone: "error" as const,
        title: "Backtest execution failed",
        description: runError.message,
      };
    }

    if (visibleResult) {
      return {
        tone: "success" as const,
        title: "Result ready",
        description: `${visibleResult.strategy.name} finished ${visibleResult.metrics.total_trades} trades over the selected research range.`,
      };
    }

    if (coverage && !coverage.complete) {
      return {
        tone: "warning" as const,
        title: "Data sync required",
        description: "Local coverage is incomplete for this request. Sync the missing Binance data before running the strategy.",
      };
    }

    if (coverage?.complete) {
      return {
        tone: "success" as const,
        title: "Local data ready",
        description: "Cached coverage is complete for the selected strategy, timeframe, and date range.",
      };
    }

    return {
      tone: "neutral" as const,
      title: "Waiting for configuration",
      description: "Select a strategy and a valid historical range to begin.",
    };
  }, [
    coverage,
    coverageError,
    isCoverageLoading,
    isRunning,
    isStrategiesLoading,
    isSyncing,
    runError,
    selectedStrategy,
    strategiesError,
    syncResult,
    visibleResult,
  ]);

  const metrics = useMemo(() => (visibleResult ? getMetricItems(visibleResult) : []), [visibleResult]);
  const selectedTrade = useMemo(
    () => visibleResult?.trades.find((trade) => trade.trade_id === selectedTradeId) ?? null,
    [selectedTradeId, visibleResult],
  );

  const handleThemeToggle = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };

  const handleStrategyChange = (strategyId: string) => {
    setSelectedStrategyId(strategyId);
  };

  const handleParameterChange = (field: StrategyParameterField, value: ParameterValue) => {
    setParameterValues((current) => ({
      ...current,
      [field.key]: normalizeParameterValue(field, value),
    }));
  };

  const handleSync = async () => {
    if (!coverageRequest || isSyncing) {
      return;
    }

    try {
      await syncCoverage();
    } catch {
      return;
    }
  };

  const handleRun = async () => {
    if (!selectedStrategy || !coverageRequest || !coverage?.complete || isRunning) {
      return;
    }

    const signature: BacktestSignature = {
      strategyId: selectedStrategy.id,
      timeframe,
      start: startValue,
      end: endValue,
      initialCapital,
      leverage,
      feeBps,
      slippageBps,
      positionSizePct,
      paramsKey: currentParamsKey,
    };

    setLastRunSignature(signature);

    try {
      await runBacktest({
        ...coverageRequest,
        symbol: FIXED_SYMBOL,
        initial_capital: initialCapital,
        leverage,
        fee_bps: feeBps,
        slippage_bps: slippageBps,
        position_size_pct: positionSizePct,
        params: parameterValues,
      });
    } catch {
      return;
    }
  };

  const rangeLabel =
    startValue && endValue
      ? `${formatTimestamp(toIsoString(startValue))} -> ${formatTimestamp(toIsoString(endValue))}`
      : "Waiting for range";

  return (
    <main className="app-shell app-shell--terminal">
      <div className="app-frame app-frame--terminal">
        <CommandBar
          theme={theme}
          onToggleTheme={handleThemeToggle}
          strategyName={selectedStrategy?.name ?? "Strategy pending"}
          symbol={FIXED_SYMBOL}
          timeframeLabel={timeframe}
          rangeLabel={rangeLabel}
          coverageReady={Boolean(effectiveCoverage?.complete)}
          statusText={`${phaseBanner.title}: ${phaseBanner.description}`}
          onSync={showSyncButton ? handleSync : undefined}
          onRun={handleRun}
          syncDisabled={isSyncing}
          runDisabled={!canRun}
          syncLabel={isSyncing ? "Syncing missing market data" : "Sync missing market data"}
          runLabel={isRunning ? "Running..." : "Run Backtest"}
        />

        <WorkspaceShell
          config={
            <ConfigRail>
              <StrategyPanel
                strategies={strategies}
                selectedStrategy={selectedStrategy}
                selectedStrategyId={selectedStrategyId}
                onSelectStrategy={handleStrategyChange}
                timeframe={timeframe}
                onTimeframeChange={(value) => setTimeframe(value)}
                startValue={startValue}
                endValue={endValue}
                onStartChange={setStartValue}
                onEndChange={setEndValue}
                initialCapital={initialCapital}
                onInitialCapitalChange={setInitialCapital}
                leverage={leverage}
                onLeverageChange={setLeverage}
                feeBps={feeBps}
                onFeeBpsChange={setFeeBps}
                slippageBps={slippageBps}
                onSlippageBpsChange={setSlippageBps}
                positionSizePct={positionSizePct}
                onPositionSizePctChange={setPositionSizePct}
                parameterValues={parameterValues}
                onParameterChange={handleParameterChange}
                onSync={handleSync}
                onRun={handleRun}
                canRun={canRun}
                isSyncing={isSyncing}
                showRunButton={false}
                showSyncButton={false}
                discoveryWarnings={discoveryWarnings}
                showHeader={false}
                showActions={false}
              />
            </ConfigRail>
          }
          chart={
            visibleResult ? (
              <KlineChart
                data={visibleResult.series.market_bars}
                markers={visibleResult.markers}
                activeTradeId={selectedTradeId}
                title="BTCUSDT perpetual"
                subtitle={`${visibleResult.run.timeframe} candles with execution markers`}
                theme={theme}
                height={520}
                className="chart-panel chart-panel--main"
              />
            ) : (
              <EmptyState
                className="empty-state empty-state--chart"
                eyebrow="Chart Workspace"
                title="No market context yet"
                description="Sync the selected window and run a strategy to project entries, exits, and holding behavior onto the price chart."
              />
            )
          }
          dock={
            visibleResult ? (
              <ResultDock
                className="result-dock"
                trades={(
                  <TradesTable
                    trades={visibleResult.trades}
                    selectedTradeId={selectedTradeId}
                    onSelectTrade={setSelectedTradeId}
                  />
                )}
                positions={buildPositionsTable(visibleResult.trades)}
                funding={buildFundingTable(visibleResult.trades)}
                equity={(
                  <EquityChart
                    data={visibleResult.series.equity_curve}
                    subtitle={`${visibleResult.run.status} run with ${visibleResult.metrics.total_trades} closed trades`}
                    theme={theme}
                    className="chart-panel chart-panel--dock"
                  />
                )}
                drawdown={(
                  <DrawdownChart
                    data={visibleResult.series.drawdown_curve}
                    subtitle="Peak-to-trough equity stress across the selected range"
                    theme={theme}
                    className="chart-panel chart-panel--dock"
                  />
                )}
                monthlyReturns={<MonthlyReturnsTable monthlyReturns={visibleResult.monthly_returns} />}
                coverage={(
                  <DataCoveragePanel
                    coverage={effectiveCoverage}
                    isLoading={!selectedStrategy || isCoverageLoading}
                    syncStatus={syncResult?.status ?? null}
                  />
                )}
              />
            ) : (
              <section className="dock-placeholder panel-surface" aria-label="Result dock placeholder">
                <div className="section-heading">
                  <p className="eyebrow">Result Dock</p>
                  <h3>Trades, funding, and curve analysis will appear here</h3>
                  <p className="section-heading__subtle">
                    The redesigned workspace keeps trade history below the chart, not in a separate evidence panel.
                  </p>
                </div>
              </section>
            )
          }
          summary={
            <SummaryRail
              metrics={metrics}
              runSummary={buildRunSummary(visibleResult, phaseBanner.title, phaseBanner.description)}
              tradeInspector={<TradeInspector trade={selectedTrade} />}
            />
          }
        />
      </div>
    </main>
  );
}
