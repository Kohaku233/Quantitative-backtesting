type Theme = "light" | "dark";

type TopBarProps = {
  theme: Theme;
  onToggleTheme: () => void;
  strategyName: string;
  symbol: string;
  coverageComplete: boolean;
};

export function TopBar({
  theme,
  onToggleTheme,
  strategyName,
  symbol,
  coverageComplete,
}: TopBarProps) {
  return (
    <header className="app-header">
      <div className="app-header__copy">
        <p className="eyebrow">Local Crypto Research</p>
        <div className="app-header__headline">
          <div>
            <h1>Quantitative Backtesting Workspace</h1>
            <p>
              Evaluate Binance perpetual strategies with explicit data coverage,
              professional risk metrics, and visible execution evidence.
            </p>
          </div>

          <div className="app-header__chips" aria-label="Workspace context">
            <span className="meta-chip">{symbol} perpetual</span>
            <span className="meta-chip">{strategyName}</span>
            <span className={coverageComplete ? "meta-chip meta-chip--success" : "meta-chip meta-chip--warning"}>
              {coverageComplete ? "Coverage ready" : "Coverage incomplete"}
            </span>
          </div>
        </div>
      </div>

      <button type="button" className="theme-toggle" onClick={onToggleTheme}>
        <span>{theme === "dark" ? "Switch to light" : "Switch to dark"}</span>
      </button>
    </header>
  );
}
