import { useEffect, useMemo, useRef } from "react";
import {
  AreaSeries,
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
  type ISeriesApi,
} from "lightweight-charts";

import { toChartTimestamp } from "../lib/chartTime";
import { formatCompactNumber, formatPercent, formatTimestamp } from "../lib/formatters";

export type DrawdownPoint = {
  time: string;
  drawdown: number;
};

type ChartTheme = "light" | "dark";

type DrawdownChartProps = {
  data: DrawdownPoint[];
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
  data: DrawdownPoint[];
  emptyMessage: string;
}) {
  const worst = data.reduce((current, point) => Math.min(current, point.drawdown), 0);
  const latest = data[data.length - 1];

  return (
    <section className="chart-panel chart-panel--fallback">
      <div className="section-heading">
        <p className="eyebrow">Risk</p>
        <h3>{title}</h3>
        {subtitle ? <p className="section-heading__subtle">{subtitle}</p> : null}
      </div>
      {data.length === 0 ? (
        <p className="chart-empty">{emptyMessage}</p>
      ) : (
        <div className="chart-fallback-grid">
          <dl>
            <dt>Worst Drawdown</dt>
            <dd>{formatPercent(worst, 2)}</dd>
          </dl>
          <dl>
            <dt>Latest Drawdown</dt>
            <dd>{formatPercent(latest?.drawdown ?? 0, 2)}</dd>
          </dl>
          <dl>
            <dt>Points</dt>
            <dd>{formatCompactNumber(data.length)}</dd>
          </dl>
          <dl>
            <dt>Last Point</dt>
            <dd>{latest ? formatTimestamp(latest.time) : "-"}</dd>
          </dl>
        </div>
      )}
    </section>
  );
}

export function DrawdownChart({
  data,
  title = "Drawdown Curve",
  subtitle,
  theme,
  height = 220,
  className,
}: DrawdownChartProps) {
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
      lineColor: isDark ? "#fb7185" : "#7f1d1d",
      topColor: isDark ? "rgba(248, 113, 113, 0.22)" : "rgba(127, 29, 29, 0.20)",
      bottomColor: isDark ? "rgba(248, 113, 113, 0.02)" : "rgba(127, 29, 29, 0.04)",
      lineWidth: 2,
      lastValueVisible: true,
      priceLineVisible: false,
    });

    chartRef.current = chart;
    seriesRef.current = series;
    series.setData(
      data.map((point) => ({
        time: toChartTimestamp(point.time),
        value: point.drawdown,
      })),
    );
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
        emptyMessage="Drawdown data will appear after a backtest completes."
      />
    );
  }

  return (
    <section className={className ? `chart-panel ${className}` : "chart-panel"} aria-label={title}>
      <div className="section-heading">
        <p className="eyebrow">Risk</p>
        <h3>{title}</h3>
        {subtitle ? <p className="section-heading__subtle">{subtitle}</p> : null}
      </div>
      <div ref={containerRef} className="chart-panel__canvas" style={{ height }} />
    </section>
  );
}
