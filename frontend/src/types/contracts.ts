export type JsonRecord = Record<string, unknown>;

export type ApiErrorEnvelope = {
  error: {
    code: string;
    message: string;
    details: JsonRecord;
  };
};

export class AppApiError extends Error {
  code: string;
  status: number;
  details: JsonRecord;

  constructor({
    code,
    message,
    status,
    details,
  }: {
    code: string;
    message: string;
    status: number;
    details?: JsonRecord;
  }) {
    super(message);
    this.name = "AppApiError";
    this.code = code;
    this.status = status;
    this.details = details ?? {};
  }
}

export type StrategyParameterField = {
  key: string;
  label: string;
  type: string;
  default?: unknown;
  required?: boolean;
  min?: number;
  max?: number;
  step?: number;
  help?: string;
  options?: Array<string | number>;
  [key: string]: unknown;
};

export type DiscoveryWarning = {
  file: string;
  reason: string;
};

export type StrategyMetadata = {
  id: string;
  name: string;
  description: string;
  supported_timeframes: string[];
  required_lookback_bars: number;
  parameter_schema: StrategyParameterField[];
};

export type StrategiesResponse = {
  strategies: StrategyMetadata[];
  discovery_warnings: DiscoveryWarning[];
};

export type CoverageRange = {
  start: string;
  end: string;
};

export type CoverageSection = {
  cached_start: string | null;
  cached_end: string | null;
  missing_ranges: CoverageRange[];
};

export type CoverageStatusResponse = {
  symbol: string;
  strategy_id: string;
  timeframe: string;
  requested_start: string;
  requested_end: string;
  effective_start: string;
  effective_end: string;
  complete: boolean;
  kline: CoverageSection;
  funding: CoverageSection;
};

export type DataSyncRequest = {
  strategy_id: string;
  symbol: string;
  timeframe: "15m" | "1h" | "4h" | "1d";
  start: string;
  end: string;
};

export type DataSyncError = {
  code: string;
  message: string;
  details: JsonRecord;
};

export type DataSyncResponse = {
  status: string;
  symbol: string;
  strategy_id: string;
  timeframe: string;
  requested_start: string;
  requested_end: string;
  effective_start: string;
  effective_end: string;
  complete: boolean;
  downloaded: {
    kline_rows: number;
    funding_rows: number;
  };
  coverage: CoverageStatusResponse;
  error?: DataSyncError | null;
};

export type BacktestRunRequest = {
  strategy_id: string;
  symbol: "BTCUSDT";
  timeframe: "15m" | "1h" | "4h" | "1d";
  start: string;
  end: string;
  initial_capital: number;
  leverage: number;
  fee_bps: number;
  slippage_bps: number;
  position_size_pct: number;
  params: JsonRecord;
};

export type BacktestRunResponse = {
  run: {
    symbol: string;
    strategy_id: string;
    timeframe: string;
    start: string;
    end: string;
    effective_start: string;
    effective_end: string;
    actual_end: string;
    status: "completed" | "liquidated";
  };
  strategy: {
    id: string;
    name: string;
    description: string;
  };
  settings: {
    initial_capital: number;
    leverage: number;
    fee_bps: number;
    slippage_bps: number;
    position_size_pct: number;
  };
  metrics: {
    net_pnl: number;
    return_pct: number;
    annualized_return: number | null;
    max_drawdown: number | null;
    sharpe: number | null;
    sortino: number | null;
    calmar: number | null;
    total_trades: number;
    win_rate: number | null;
    profit_factor: number | null;
    average_trade_return: number | null;
    average_holding_time_seconds: number | null;
  };
  series: {
    market_bars: Array<{
      time: string;
      open: number;
      high: number;
      low: number;
      close: number;
      volume: number;
    }>;
    equity_curve: Array<{
      time: string;
      equity: number;
    }>;
    drawdown_curve: Array<{
      time: string;
      drawdown: number;
    }>;
  };
  monthly_returns: Array<{
    month: string;
    return_pct: number;
  }>;
  trades: Array<{
    trade_id: number;
    side: string;
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    quantity: number;
    allocated_margin_at_entry: number;
    notional: number;
    gross_pnl: number;
    fees: number;
    funding_pnl: number;
    net_pnl: number;
    return_pct_on_margin: number;
    holding_bars: number;
    holding_seconds: number;
    exit_reason: string;
  }>;
  markers: Array<{
    time: string;
    price: number;
    action: string;
    trade_id: number;
  }>;
  coverage: CoverageStatusResponse;
};
