import { Activity, BadgeDollarSign, ChartNoAxesCombined, ShieldAlert, TrendingUp } from "lucide-react";

import type { MetricItem } from "./MetricsGrid";
import type { ReactNode } from "react";

type SummaryRailProps = {
  metrics: MetricItem[];
  runSummary: ReactNode;
  tradeInspector: ReactNode;
};

const metricIcons = {
  "Net PnL": BadgeDollarSign,
  "Return %": TrendingUp,
  "Max Drawdown": ShieldAlert,
  Sharpe: Activity,
  "Profit Factor": ChartNoAxesCombined,
} as const;

export function SummaryRail({
  metrics,
  runSummary,
  tradeInspector,
}: SummaryRailProps) {
  return (
    <section className="summary-rail" aria-label="Run summary">
      <div className="summary-card">
        <div className="section-heading">
          <p className="eyebrow">Run Context</p>
          <h2>Summary</h2>
        </div>
        <div className="summary-card__content">{runSummary}</div>
      </div>

      <section className="summary-card summary-card--metrics" aria-label="Key metrics">
        <div className="section-heading">
          <p className="eyebrow">Key Metrics</p>
          <h3>Research readout</h3>
        </div>

        <div className="summary-metrics">
          {metrics.map((item) => {
            const Icon = metricIcons[item.label as keyof typeof metricIcons] ?? Activity;

            return (
              <article
                key={item.label}
                className="summary-metric"
                data-tone={item.tone ?? "neutral"}
              >
                <div className="summary-metric__meta">
                  <Icon size={16} strokeWidth={2} aria-hidden="true" />
                  <span>{item.label}</span>
                </div>
                <strong className="summary-metric__value">{item.value}</strong>
                {item.detail ? <p className="summary-metric__detail">{item.detail}</p> : null}
              </article>
            );
          })}
        </div>
      </section>

      {tradeInspector}
    </section>
  );
}
