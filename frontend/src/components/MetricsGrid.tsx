import type { ReactNode } from "react";

type MetricTone = "neutral" | "positive" | "negative" | "warning";

export type MetricItem = {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  tone?: MetricTone;
};

type MetricsGridProps = {
  items: MetricItem[];
  className?: string;
};

export function MetricsGrid({ items, className }: MetricsGridProps) {
  return (
    <section
      className={className ? `metrics-grid ${className}` : "metrics-grid"}
      aria-label="Backtest metrics"
    >
      {items.map((item) => (
        <article
          key={item.label}
          className={item.tone ? `metric-card metric-card--${item.tone}` : "metric-card"}
          data-tone={item.tone ?? "neutral"}
        >
          <p className="metric-card__label">{item.label}</p>
          <div className="metric-card__value">{item.value}</div>
          {item.detail ? <p className="metric-card__detail">{item.detail}</p> : null}
        </article>
      ))}
    </section>
  );
}
