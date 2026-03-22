import type { StrategyMetadata, StrategyParameterField } from "../types/contracts";

type Timeframe = "15m" | "1h" | "4h" | "1d";
type ParameterValue = string | number | boolean;

type DiscoveryWarning = {
  file: string;
  reason: string;
};

type StrategyPanelProps = {
  strategies: StrategyMetadata[];
  selectedStrategy: StrategyMetadata | null;
  selectedStrategyId: string;
  onSelectStrategy: (strategyId: string) => void;
  timeframe: Timeframe;
  onTimeframeChange: (timeframe: Timeframe) => void;
  startValue: string;
  endValue: string;
  onStartChange: (value: string) => void;
  onEndChange: (value: string) => void;
  initialCapital: number;
  onInitialCapitalChange: (value: number) => void;
  leverage: number;
  onLeverageChange: (value: number) => void;
  feeBps: number;
  onFeeBpsChange: (value: number) => void;
  slippageBps: number;
  onSlippageBpsChange: (value: number) => void;
  positionSizePct: number;
  onPositionSizePctChange: (value: number) => void;
  parameterValues: Record<string, ParameterValue>;
  onParameterChange: (field: StrategyParameterField, value: ParameterValue) => void;
  onSync: () => void;
  onRun: () => void;
  canRun: boolean;
  isSyncing: boolean;
  showRunButton: boolean;
  showSyncButton: boolean;
  discoveryWarnings: DiscoveryWarning[];
};

function parseNumber(value: string) {
  return Number.parseFloat(value);
}

function getFallbackValue(field: StrategyParameterField): ParameterValue {
  if (
    typeof field.default === "boolean" ||
    typeof field.default === "number" ||
    typeof field.default === "string"
  ) {
    return field.default;
  }

  if (field.type === "boolean") {
    return false;
  }

  if (field.type === "integer" || field.type === "number" || field.type === "float") {
    return typeof field.min === "number" ? field.min : 0;
  }

  return "";
}

function renderParameterField(
  field: StrategyParameterField,
  value: ParameterValue,
  onParameterChange: StrategyPanelProps["onParameterChange"],
) {
  const inputId = `strategy-parameter-${field.key}`;
  const sharedProps = {
    id: inputId,
    name: field.key,
  };

  if (field.type === "boolean") {
    return (
      <label className="field field--checkbox" htmlFor={inputId}>
        <input
          {...sharedProps}
          type="checkbox"
          checked={Boolean(value)}
          onChange={(event) => onParameterChange(field, event.currentTarget.checked)}
        />
        <span>{field.label}</span>
      </label>
    );
  }

  if (Array.isArray(field.options) && field.options.length > 0) {
    return (
      <>
        <label className="field__label" htmlFor={inputId}>
          {field.label}
        </label>
        <select
          {...sharedProps}
          value={String(value)}
          onChange={(event) => onParameterChange(field, event.currentTarget.value)}
        >
          {field.options.map((option) => (
            <option key={String(option)} value={String(option)}>
              {String(option)}
            </option>
          ))}
        </select>
      </>
    );
  }

  if (field.type === "integer" || field.type === "number" || field.type === "float") {
    return (
      <>
        <label className="field__label" htmlFor={inputId}>
          {field.label}
        </label>
        <input
          {...sharedProps}
          type="number"
          value={Number(value)}
          min={field.min}
          max={field.max}
          step={field.step ?? (field.type === "integer" ? 1 : 0.01)}
          onChange={(event) => onParameterChange(field, event.currentTarget.value)}
        />
      </>
    );
  }

  return (
    <>
      <label className="field__label" htmlFor={inputId}>
        {field.label}
      </label>
      <input
        {...sharedProps}
        type="text"
        value={String(value)}
        onChange={(event) => onParameterChange(field, event.currentTarget.value)}
      />
    </>
  );
}

export function StrategyPanel({
  strategies,
  selectedStrategy,
  selectedStrategyId,
  onSelectStrategy,
  timeframe,
  onTimeframeChange,
  startValue,
  endValue,
  onStartChange,
  onEndChange,
  initialCapital,
  onInitialCapitalChange,
  leverage,
  onLeverageChange,
  feeBps,
  onFeeBpsChange,
  slippageBps,
  onSlippageBpsChange,
  positionSizePct,
  onPositionSizePctChange,
  parameterValues,
  onParameterChange,
  onSync,
  onRun,
  canRun,
  isSyncing,
  showRunButton,
  showSyncButton,
  discoveryWarnings,
}: StrategyPanelProps) {
  return (
    <section className="strategy-panel panel-surface">
      <div className="section-heading">
        <p className="eyebrow">Strategy Setup</p>
        <h2>Research controls</h2>
        <p className="section-heading__subtle">
          Configure the plugin, historical window, and execution assumptions
          before a run.
        </p>
      </div>

      <div className="field">
        <label className="field__label" htmlFor="strategy-select">
          Strategy
        </label>
        <select
          id="strategy-select"
          value={selectedStrategyId}
          onChange={(event) => onSelectStrategy(event.currentTarget.value)}
        >
          {strategies.map((strategy) => (
            <option key={strategy.id} value={strategy.id}>
              {strategy.name}
            </option>
          ))}
        </select>
      </div>

      {selectedStrategy ? (
        <div className="strategy-panel__description">
          <h3>{selectedStrategy.name}</h3>
          <p>{selectedStrategy.description}</p>
        </div>
      ) : null}

      <div className="config-grid">
        <div className="field">
          <label className="field__label" htmlFor="timeframe-select">
            Timeframe
          </label>
          <select
            id="timeframe-select"
            value={timeframe}
            onChange={(event) => onTimeframeChange(event.currentTarget.value as Timeframe)}
          >
            {(selectedStrategy?.supported_timeframes ?? ["15m", "1h", "4h", "1d"]).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="start-input">
            Start
          </label>
          <input
            id="start-input"
            type="datetime-local"
            value={startValue}
            onChange={(event) => onStartChange(event.currentTarget.value)}
          />
        </div>

        <div className="field">
          <label className="field__label" htmlFor="end-input">
            End
          </label>
          <input
            id="end-input"
            type="datetime-local"
            value={endValue}
            onChange={(event) => onEndChange(event.currentTarget.value)}
          />
        </div>

        <div className="field">
          <label className="field__label" htmlFor="initial-capital-input">
            Initial Capital
          </label>
          <input
            id="initial-capital-input"
            type="number"
            min={100}
            step={100}
            value={initialCapital}
            onChange={(event) => onInitialCapitalChange(parseNumber(event.currentTarget.value))}
          />
        </div>

        <div className="field">
          <label className="field__label" htmlFor="leverage-input">
            Leverage
          </label>
          <input
            id="leverage-input"
            type="number"
            min={1}
            max={20}
            step={0.5}
            value={leverage}
            onChange={(event) => onLeverageChange(parseNumber(event.currentTarget.value))}
          />
        </div>

        <div className="field">
          <label className="field__label" htmlFor="fee-bps-input">
            Fee (bps)
          </label>
          <input
            id="fee-bps-input"
            type="number"
            min={0}
            step={0.1}
            value={feeBps}
            onChange={(event) => onFeeBpsChange(parseNumber(event.currentTarget.value))}
          />
        </div>

        <div className="field">
          <label className="field__label" htmlFor="slippage-bps-input">
            Slippage (bps)
          </label>
          <input
            id="slippage-bps-input"
            type="number"
            min={0}
            step={0.1}
            value={slippageBps}
            onChange={(event) => onSlippageBpsChange(parseNumber(event.currentTarget.value))}
          />
        </div>

        <div className="field">
          <label className="field__label" htmlFor="position-size-input">
            Position Size
          </label>
          <input
            id="position-size-input"
            type="number"
            min={0.05}
            max={1}
            step={0.01}
            value={positionSizePct}
            onChange={(event) => onPositionSizePctChange(parseNumber(event.currentTarget.value))}
          />
          <p className="field__hint">Fraction of equity allocated to each isolated trade.</p>
        </div>
      </div>

      {selectedStrategy ? (
        <div className="parameter-group">
          <div className="section-heading">
            <p className="eyebrow">Plugin Parameters</p>
            <h3>Schema-driven inputs</h3>
          </div>

          <div className="config-grid">
            {selectedStrategy.parameter_schema.map((field) => (
              <div className="field" key={field.key}>
                {renderParameterField(
                  field,
                  parameterValues[field.key] ?? getFallbackValue(field),
                  onParameterChange,
                )}
                {field.help ? <p className="field__hint">{field.help}</p> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {discoveryWarnings.length > 0 ? (
        <div className="warning-stack" aria-label="Discovery warnings">
          <p className="eyebrow">Plugin Notes</p>
          {discoveryWarnings.map((warning) => (
            <p key={`${warning.file}-${warning.reason}`} className="warning-stack__item">
              <strong>{warning.file}</strong>: {warning.reason}
            </p>
          ))}
        </div>
      ) : null}

      <div className="panel-actions">
        {showSyncButton ? (
          <button type="button" className="button button--secondary" onClick={onSync} disabled={isSyncing}>
            Sync missing market data
          </button>
        ) : null}
        {showRunButton ? (
          <button type="button" className="button button--primary" onClick={onRun} disabled={!canRun}>
            Run backtest
          </button>
        ) : null}
      </div>
    </section>
  );
}
