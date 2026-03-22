import { useState, type CSSProperties, type ReactNode } from "react";

type DockTabId = "trades" | "positions" | "funding" | "equity" | "drawdown" | "monthlyReturns" | "coverage";

type ResultDockProps = {
  trades: ReactNode;
  positions: ReactNode;
  funding: ReactNode;
  equity: ReactNode;
  drawdown: ReactNode;
  monthlyReturns: ReactNode;
  coverage: ReactNode;
  defaultTabId?: DockTabId;
  className?: string;
};

const tabs: Array<{ id: DockTabId; label: string }> = [
  { id: "trades", label: "Trades" },
  { id: "positions", label: "Positions" },
  { id: "funding", label: "Funding" },
  { id: "equity", label: "Equity" },
  { id: "drawdown", label: "Drawdown" },
  { id: "monthlyReturns", label: "Monthly Returns" },
  { id: "coverage", label: "Coverage" },
];

const shellStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  padding: 16,
  border: "1px solid color-mix(in oklch, var(--panel-border, #cfd6df) 100%, transparent)",
  borderRadius: 20,
  background: "linear-gradient(180deg, color-mix(in oklch, var(--panel, white) 96%, transparent) 0%, color-mix(in oklch, var(--panel, white) 100%, transparent) 100%)",
  boxShadow: "var(--shadow, 0 18px 44px rgba(49, 63, 84, 0.08))",
};

const tabListStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  padding: 4,
  borderRadius: 999,
  background: "color-mix(in oklch, var(--bg-muted, #eef2f7) 62%, transparent)",
};

const tabButtonStyle: CSSProperties = {
  appearance: "none",
  borderWidth: 1,
  borderStyle: "solid",
  borderColor: "transparent",
  borderRadius: 999,
  padding: "0.7rem 0.95rem",
  background: "transparent",
  color: "var(--text-muted, #445)",
  font: "inherit",
  fontSize: 13,
  fontWeight: 700,
  letterSpacing: "0.04em",
  textTransform: "uppercase",
};

const activeTabButtonStyle: CSSProperties = {
  background: "color-mix(in oklch, var(--panel, white) 92%, transparent)",
  borderColor: "color-mix(in oklch, var(--panel-border, #cfd6df) 100%, transparent)",
  color: "var(--text, #121826)",
  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.04)",
};

const panelStyle: CSSProperties = {
  borderRadius: 18,
  padding: 16,
  background: "color-mix(in oklch, var(--bg-muted, #eef2f7) 42%, transparent)",
  minHeight: 160,
};

function getTabContent(props: ResultDockProps, tabId: DockTabId): ReactNode {
  switch (tabId) {
    case "trades":
      return props.trades;
    case "positions":
      return props.positions;
    case "funding":
      return props.funding;
    case "equity":
      return props.equity;
    case "drawdown":
      return props.drawdown;
    case "monthlyReturns":
      return props.monthlyReturns;
    case "coverage":
      return props.coverage;
  }
}

export function ResultDock({
  trades,
  positions,
  funding,
  equity,
  drawdown,
  monthlyReturns,
  coverage,
  defaultTabId = "trades",
  className,
}: ResultDockProps) {
  const [activeTabId, setActiveTabId] = useState<DockTabId>(defaultTabId);
  const contentMap = { trades, positions, funding, equity, drawdown, monthlyReturns, coverage };

  return (
    <section className={className} aria-label="Backtest results" style={shellStyle}>
      <div role="tablist" aria-label="Result tabs" style={tabListStyle}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTabId === tab.id}
            aria-controls={`result-dock-panel-${tab.id}`}
            id={`result-dock-tab-${tab.id}`}
            onClick={() => setActiveTabId(tab.id)}
            style={{ ...tabButtonStyle, ...(activeTabId === tab.id ? activeTabButtonStyle : null) }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        id={`result-dock-panel-${activeTabId}`}
        aria-labelledby={`result-dock-tab-${activeTabId}`}
        style={panelStyle}
      >
        {getTabContent(contentMap, activeTabId)}
      </div>
    </section>
  );
}
