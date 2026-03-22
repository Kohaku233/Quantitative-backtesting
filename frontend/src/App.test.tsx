import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { http, HttpResponse, server } from "./test/msw";

import App from "./App";


const strategyResponse = {
  strategies: [
    {
      id: "sma_cross",
      name: "SMA Cross",
      description: "Long/short moving-average crossover strategy.",
      supported_timeframes: ["15m", "1h", "4h", "1d"],
      required_lookback_bars: 3,
      parameter_schema: [
        {
          key: "fast_period",
          label: "Fast Period",
          type: "integer",
          default: 20,
          required: true,
          min: 1,
          max: 500,
          step: 1,
          help: "Short moving average period.",
        },
        {
          key: "slow_period",
          label: "Slow Period",
          type: "integer",
          default: 50,
          required: true,
          min: 2,
          max: 500,
          step: 1,
          help: "Long moving average period.",
        },
      ],
    },
  ],
  discovery_warnings: [],
};

const incompleteCoverage = {
  symbol: "BTCUSDT",
  strategy_id: "sma_cross",
  timeframe: "1h",
  requested_start: "2024-01-01T00:00:00Z",
  requested_end: "2024-01-07T23:59:59Z",
  effective_start: "2024-01-01T00:00:00Z",
  effective_end: "2024-01-07T23:00:00Z",
  complete: false,
  kline: {
    cached_start: null,
    cached_end: null,
    missing_ranges: [
      {
        start: "2024-01-01T00:00:00Z",
        end: "2024-01-07T23:00:00Z",
      },
    ],
  },
  funding: {
    cached_start: null,
    cached_end: null,
    missing_ranges: [
      {
        start: "2024-01-01T00:00:00Z",
        end: "2024-01-07T16:00:00Z",
      },
    ],
  },
};

const completeCoverage = {
  ...incompleteCoverage,
  complete: true,
  kline: {
    cached_start: "2024-01-01T00:00:00Z",
    cached_end: "2024-01-07T23:00:00Z",
    missing_ranges: [],
  },
  funding: {
    cached_start: "2024-01-01T00:00:00Z",
    cached_end: "2024-01-07T16:00:00Z",
    missing_ranges: [],
  },
};

const syncCompletedResponse = {
  status: "completed",
  symbol: "BTCUSDT",
  strategy_id: "sma_cross",
  timeframe: "1h",
  requested_start: "2024-01-01T00:00:00Z",
  requested_end: "2024-01-07T23:59:59Z",
  effective_start: "2024-01-01T00:00:00Z",
  effective_end: "2024-01-07T23:00:00Z",
  complete: true,
  downloaded: {
    kline_rows: 168,
    funding_rows: 21,
  },
  coverage: completeCoverage,
};

const syncFailedResponse = {
  status: "sync_failed",
  symbol: "BTCUSDT",
  strategy_id: "sma_cross",
  timeframe: "1h",
  requested_start: "2024-01-01T00:00:00Z",
  requested_end: "2024-01-07T23:59:59Z",
  effective_start: "2024-01-01T00:00:00Z",
  effective_end: "2024-01-07T23:00:00Z",
  complete: false,
  downloaded: {
    kline_rows: 0,
    funding_rows: 0,
  },
  coverage: incompleteCoverage,
  error: {
    code: "sync_failed",
    message: "Market data coverage remained incomplete after sync.",
    details: {},
  },
};

const noDataAvailableResponse = {
  status: "no_data_available",
  symbol: "BTCUSDT",
  strategy_id: "sma_cross",
  timeframe: "1h",
  requested_start: "2024-01-01T00:00:00Z",
  requested_end: "2024-01-07T23:59:59Z",
  effective_start: "2024-01-01T00:00:00Z",
  effective_end: "2024-01-07T23:00:00Z",
  complete: false,
  downloaded: {
    kline_rows: 0,
    funding_rows: 0,
  },
  coverage: incompleteCoverage,
};

const successfulRunResponse = {
  run: {
    symbol: "BTCUSDT",
    strategy_id: "sma_cross",
    timeframe: "1h",
    start: "2024-01-01T00:00:00Z",
    end: "2024-01-07T23:59:59Z",
    effective_start: "2024-01-01T00:00:00Z",
    effective_end: "2024-01-07T23:00:00Z",
    actual_end: "2024-01-07T23:59:59Z",
    status: "completed",
  },
  strategy: {
    id: "sma_cross",
    name: "SMA Cross",
    description: "Long/short moving-average crossover strategy.",
  },
  settings: {
    initial_capital: 10000,
    leverage: 2,
    fee_bps: 4,
    slippage_bps: 2,
    position_size_pct: 0.95,
  },
  metrics: {
    net_pnl: 823.41,
    return_pct: 0.082341,
    annualized_return: 0.201233,
    max_drawdown: -0.0921,
    sharpe: 1.44,
    sortino: 2.01,
    calmar: 2.18,
    total_trades: 18,
    win_rate: 0.5556,
    profit_factor: 1.73,
    average_trade_return: 0.0142,
    average_holding_time_seconds: 172800,
  },
  series: {
    market_bars: [
      {
        time: "2024-01-01T01:00:00Z",
        open: 42200,
        high: 42310,
        low: 42180,
        close: 42290,
        volume: 1023.5,
      },
    ],
    equity_curve: [
      {
        time: "2024-01-01T01:00:00Z",
        equity: 10000,
      },
    ],
    drawdown_curve: [
      {
        time: "2024-01-01T01:00:00Z",
        drawdown: 0,
      },
    ],
  },
  monthly_returns: [
    {
      month: "2024-01",
      return_pct: 0.0312,
    },
  ],
  trades: [
    {
      trade_id: 1,
      side: "long",
      entry_time: "2024-01-03T08:00:00Z",
      exit_time: "2024-01-05T12:00:00Z",
      entry_price: 43210.5,
      exit_price: 44100,
      quantity: 0.023,
      allocated_margin_at_entry: 331.28,
      notional: 993.84,
      gross_pnl: 20.46,
      fees: 0.8,
      funding_pnl: -0.11,
      net_pnl: 19.55,
      return_pct_on_margin: 0.059,
      holding_bars: 52,
      holding_seconds: 187200,
      exit_reason: "signal_flip",
    },
  ],
  markers: [
    {
      time: "2024-01-03T08:00:00Z",
      price: 43210.5,
      action: "entry_long",
      trade_id: 1,
    },
  ],
  coverage: completeCoverage,
};

const coverageMissingError = {
  error: {
    code: "data_coverage_missing",
    message: "Required market data coverage is incomplete for this run.",
    details: {},
  },
};


function deferredResponse<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve;
  });
  return { promise, resolve };
}


function createDefaultHandlers() {
  return [
    http.get("/api/strategies", () => HttpResponse.json(strategyResponse)),
    http.get("/api/data/status", () => HttpResponse.json(incompleteCoverage)),
  ];
}


beforeEach(() => {
  server.use(...createDefaultHandlers());
});

afterEach(() => {
  vi.restoreAllMocks();
});


test("blocks run until coverage is complete or sync succeeds", async () => {
  const coverageGate = deferredResponse<typeof incompleteCoverage>();

  server.use(
    http.get("/api/data/status", () => coverageGate.promise.then((body) => HttpResponse.json(body))),
  );

  render(<App />);

  expect(await screen.findByText(/checking local data/i)).toBeInTheDocument();

  coverageGate.resolve(incompleteCoverage);

  expect(await screen.findByText(/data sync required/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /run backtest/i })).toBeDisabled();
});


test("renders schema-driven parameter inputs from the selected strategy", async () => {
  render(<App />);

  expect(await screen.findByLabelText(/fast period/i)).toHaveValue(20);
  expect(screen.getByLabelText(/slow period/i)).toHaveValue(50);
});


test("renders sync and run error states from backend contracts", async () => {
  server.use(
    http.post("/api/data/sync", () => HttpResponse.json(syncFailedResponse)),
    http.post("/api/backtests/run", () => HttpResponse.json(coverageMissingError, { status: 409 })),
  );

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: /sync missing market data/i }));

  expect(await screen.findByText(/syncing missing market data/i)).toBeInTheDocument();
  expect(await screen.findByText(/unable to sync market data/i)).toBeInTheDocument();

  server.use(
    http.post("/api/data/sync", () => HttpResponse.json(syncCompletedResponse)),
  );

  fireEvent.click(screen.getByRole("button", { name: /sync missing market data/i }));
  fireEvent.click(await screen.findByRole("button", { name: /run backtest/i }));

  expect(await screen.findByText(/data coverage is incomplete/i)).toBeInTheDocument();
});


test("stops after no_data_available without calling the run endpoint", async () => {
  const runSpy = vi.fn();

  server.use(
    http.post("/api/data/sync", () => HttpResponse.json(noDataAvailableResponse)),
    http.post("/api/backtests/run", async () => {
      runSpy();
      return HttpResponse.json(successfulRunResponse);
    }),
  );

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: /sync missing market data/i }));

  expect(await screen.findByText(/requested range has no exchange data/i)).toBeInTheDocument();
  await waitFor(() => expect(runSpy).not.toHaveBeenCalled());
});


test("renders metrics and trades after a successful run", async () => {
  server.use(
    http.post("/api/data/sync", () => HttpResponse.json(syncCompletedResponse)),
    http.post("/api/backtests/run", () => HttpResponse.json(successfulRunResponse)),
  );

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: /sync missing market data/i }));
  fireEvent.click(await screen.findByRole("button", { name: /run backtest/i }));

  expect(await screen.findByText(/max drawdown/i)).toBeInTheDocument();
  expect(screen.getByRole("table", { name: /trade list/i })).toBeInTheDocument();
  expect(screen.getByText(/monthly returns/i)).toBeInTheDocument();
  expect(screen.getByText(/entry_long/i)).toBeInTheDocument();
  expect(screen.getByText(/rendering result/i)).toBeInTheDocument();
});


test("clears stale results when the active research configuration changes", async () => {
  server.use(
    http.post("/api/data/sync", () => HttpResponse.json(syncCompletedResponse)),
    http.post("/api/backtests/run", () => HttpResponse.json(successfulRunResponse)),
  );

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: /sync missing market data/i }));
  fireEvent.click(await screen.findByRole("button", { name: /run backtest/i }));

  expect(await screen.findByText(/entry_long/i)).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText(/timeframe/i), { target: { value: "4h" } });

  expect(await screen.findByText(/checking local data/i)).toBeInTheDocument();
  await waitFor(() => expect(screen.queryByText(/entry_long/i)).not.toBeInTheDocument());
});
