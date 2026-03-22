import { useEffect, useMemo, useRef } from "react";
import {
  AreaSeries,
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
  type ISeriesApi,
} from "lightweight-charts";

import { formatCompactNumber, formatNumber, formatTimestamp } from "../lib/formatters";

export type EquityPoint = {
  time: string;
  equity: number;
};

type ChartTheme = "light" | "dark";

type EquityChartProps = {
  data: EquityPoint[];
  title?: string;
  subtitle?: string;
  theme?: ChartTheme;
  height?: number;
  className?: string;
};

function resolveTheme(theme?: ChartTheme): ChartTheme {
  if (theme) {
    return theme;
  }

  if (typeof document !== "undefined") {
    const explicit = document.documentElement.dataset.theme;
    if (explicit === "light" || explicit === "dark") {
      return explicit;
    }
  }

  if (typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }

  return "light";
}

function supportsChartRendering() {
  return typeof window !== "undefined" && typeof document !== "undefined" && typeof ResizeObserver !== "undefined";
}

function ChartFallback({
  title,
  subtitle,
  data,
  emptyMessage,
}: {
  title: string;
  subtitle?: string;
  data: EquityPoint[];
  emptyMessage: string;
}) {
  const last = data[data.length - 1];
  const first = data[0];
  const change = first && last ? last.equity - first.equity : 0;

  return (
    <section className="chart-panel chart-panel--fallback">
      <div className="section-heading">
        <p className="eyebrow">Performance</p>
        <h3>{title}</h3>
        {subtitle ? <p className="section-heading__subtle">{subtitle}</p> : null}
      </div>
      {data.length === 0 ? (
        <p className="chart-empty">{emptyMessage}</p>
      ) : (
        <div className="chart-fallback-grid">
          <dl>
            <dt>Ending Equity</dt>
            <dd>{formatNumber(last?.equity ?? 0, 2)}</dd>
          </dl>
          <dl>
            <dt>Change</dt>
            <dd>{formatNumber(change, 2)}</dd>
          </dl>
          <dl>
            <dt>Points</dt>
            <dd>{formatCompactNumber(data.length)}</dd>
          </dl>
          <dl>
            <dt>Last Point</dt>
            <dd>{last ? formatTimestamp(last.time) : "-"}</dd>
          </dl>
        </div>
      )}
    </section>
  );
}

export function EquityChart({
  data,
  title = "Equity Curve",
  subtitle,
  theme,
  height = 280,
  className,
}: EquityChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const resolvedTheme = resolveTheme(theme);
  const shouldRenderChart = useMemo(
    () => supportsChartRendering() && data.length > 0,
    [data.length],
  );

  useEffect(() => {
    const container = containerRef.current;

    if (!container || !shouldRenderChart) {
      return undefined;
    }

    container.innerHTML = "";

    const isDark = resolvedTheme === "dark";
    const chart = createChart(container, {
      autoSize: false,
      width: container.clientWidth || 720,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: isDark ? "#d6d9e0" : "#2c3340",
      },
      grid: {
        vertLines: { color: isDark ? "rgba(148, 163, 184, 0.12)" : "rgba(100, 116, 139, 0.14)" },
        horzLines: { color: isDark ? "rgba(148, 163, 184, 0.12)" : "rgba(100, 116, 139, 0.14)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: false,
      handleScale: false,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: isDark ? "#7dd3fc" : "#0f172a",
      topColor: isDark ? "rgba(125, 211, 252, 0.28)" : "rgba(15, 23, 42, 0.22)",
      bottomColor: isDark ? "rgba(125, 211, 252, 0.02)" : "rgba(15, 23, 42, 0.04)",
      lineWidth: 2,
      lastValueVisible: true,
      priceLineVisible: false,
    });

    chartRef.current = chart;
    seriesRef.current = series;
    series.setData(data);
    chart.timeScale().fitContent();

    const resize = () => {
      chart.applyOptions({
        width: container.clientWidth || 720,
        height,
      });
    };

    resize();

    const observer = new ResizeObserver(() => resize());
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [data, height, resolvedTheme, shouldRenderChart]);

  if (!shouldRenderChart) {
    return (
      <ChartFallback
        title={title}
        subtitle={subtitle}
        data={data}
        emptyMessage="Equity data will appear after a backtest completes."
      />
    );
  }

  return (
    <section className={className ? `chart-panel ${className}` : "chart-panel"} aria-label={title}>
      <div className="section-heading">
        <p className="eyebrow">Performance</p>
        <h3>{title}</h3>
        {subtitle ? <p className="section-heading__subtle">{subtitle}</p> : null}
      </div>
      <div ref={containerRef} className="chart-panel__canvas" style={{ height }} />
    </section>
  );
}
