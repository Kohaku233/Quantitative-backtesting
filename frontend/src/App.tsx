import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

import { DataCoveragePanel } from "./components/DataCoveragePanel";
import { DrawdownChart } from "./components/DrawdownChart";
import { EmptyState } from "./components/EmptyState";
import { EquityChart } from "./components/EquityChart";
import { KlineChart } from "./components/KlineChart";
import { MetricsGrid, type MetricItem } from "./components/MetricsGrid";
import { MonthlyReturnsTable } from "./components/MonthlyReturnsTable";
import { StatusBanner } from "./components/StatusBanner";
import { StrategyPanel } from "./components/StrategyPanel";
import { TopBar } from "./components/TopBar";
import { TradesTable } from "./components/TradesTable";
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
    feeBps,
    initialCapital,
    leverage,
    positionSizePct,
    currentParamsKey,
    result,
    selectedStrategy,
    startValue,
    slippageBps,
    timeframe,
    endValue,
    lastRunSignature,
  ]);
  const deferredResult = useDeferredValue(activeResult);
  const visibleResult = activeResult === null ? null : deferredResult;

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
        title: "Rendering result",
        description: `${visibleResult.strategy.name} completed ${visibleResult.metrics.total_trades} trades between ${formatTimestamp(visibleResult.run.effective_start)} and ${formatTimestamp(visibleResult.run.actual_end)}.`,
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
    deferredResult,
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

  return (
    <main className="app-shell">
      <div className="app-frame">
        <TopBar
          theme={theme}
          onToggleTheme={handleThemeToggle}
          strategyName={selectedStrategy?.name ?? "Strategy pending"}
          symbol={FIXED_SYMBOL}
          coverageComplete={Boolean(effectiveCoverage?.complete)}
        />

        <div className="workspace-grid">
          <aside className="sidebar-stack">
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
              showRunButton={!isSyncing}
              showSyncButton={showSyncButton}
              discoveryWarnings={discoveryWarnings}
            />

            <DataCoveragePanel
              coverage={effectiveCoverage}
              isLoading={!selectedStrategy || isCoverageLoading}
              syncStatus={syncResult?.status ?? null}
            />
          </aside>

          <section className="results-stack">
            <StatusBanner
              tone={phaseBanner.tone}
              title={phaseBanner.title}
              description={phaseBanner.description}
            />

            {!visibleResult ? (
              <EmptyState
                eyebrow="Research Terminal"
                title="No backtest result yet"
                description="Sync the requested data window, then run the selected strategy to inspect risk, returns, execution, and market context in one place."
              />
            ) : (
              <>
                <MetricsGrid items={metrics} />

                <div className="results-grid">
                  <KlineChart
                    data={visibleResult.series.market_bars}
                    markers={visibleResult.markers}
                    title="BTCUSDT perpetual"
                    subtitle={`${visibleResult.run.timeframe} candles with execution markers`}
                    theme={theme}
                  />

                  <section className="signal-feed panel-surface" aria-label="Signal markers">
                    <div className="section-heading">
                      <p className="eyebrow">Evidence Trail</p>
                      <h3>Execution markers</h3>
                      <p className="section-heading__subtle">
                        Raw signal actions emitted by the strategy.
                      </p>
                    </div>

                    <div className="signal-feed__list">
                      {visibleResult.markers.length === 0 ? (
                        <p className="signal-feed__empty">No marker annotations were produced for this run.</p>
                      ) : (
                        visibleResult.markers.map((marker) => (
                          <article key={`${marker.trade_id}-${marker.time}`} className="signal-chip">
                            <strong>{marker.action}</strong>
                            <span>Trade #{marker.trade_id}</span>
                            <span>{formatTimestamp(marker.time)}</span>
                            <span>{formatNumber(marker.price, 2)}</span>
                          </article>
                        ))
                      )}
                    </div>
                  </section>
                </div>

                <div className="secondary-grid">
                  <EquityChart
                    data={visibleResult.series.equity_curve}
                    subtitle={`${visibleResult.run.status} run with ${visibleResult.metrics.total_trades} closed trades`}
                    theme={theme}
                  />
                  <DrawdownChart
                    data={visibleResult.series.drawdown_curve}
                    subtitle="Peak-to-trough equity stress across the selected range"
                    theme={theme}
                  />
                </div>

                <div className="secondary-grid secondary-grid--tables">
                  <TradesTable trades={visibleResult.trades} />
                  <MonthlyReturnsTable monthlyReturns={visibleResult.monthly_returns} />
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
