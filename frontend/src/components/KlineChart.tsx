import { useEffect, useMemo, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarker,
  type UTCTimestamp,
} from "lightweight-charts";

import { toChartTimestamp } from "../lib/chartTime";
import { formatCompactNumber, formatNumber, formatTimestamp } from "../lib/formatters";

export type KlinePoint = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type KlineMarker = {
  time: string;
  price: number;
  action: string;
  trade_id: number;
};

type ChartTheme = "light" | "dark";

type KlineChartProps = {
  data: KlinePoint[];
  markers?: KlineMarker[];
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

function mapMarker(marker: KlineMarker): SeriesMarker<UTCTimestamp> {
  const action = marker.action.toLowerCase();
  const isEntry = action.includes("entry");
  const isExit = action.includes("exit");

  return {
    time: toChartTimestamp(marker.time),
    position: isEntry ? "belowBar" : "aboveBar",
    shape: isEntry ? "arrowUp" : isExit ? "arrowDown" : "circle",
    color: isEntry ? "#2f855a" : isExit ? "#c53030" : "#4a5568",
    text: `#${marker.trade_id} ${marker.action.replaceAll("_", " ")}`,
    price: marker.price,
    id: String(marker.trade_id),
  };
}

function supportsChartRendering() {
  return typeof window !== "undefined" && typeof document !== "undefined" && typeof ResizeObserver !== "undefined";
}

function ChartFallback({
  title,
  subtitle,
  data,
  markers,
  emptyMessage,
}: {
  title: string;
  subtitle?: string;
  data: KlinePoint[];
  markers: KlineMarker[];
  emptyMessage: string;
}) {
  const last = data[data.length - 1];
  const high = data.reduce((current, point) => Math.max(current, point.high), Number.NEGATIVE_INFINITY);
  const low = data.reduce((current, point) => Math.min(current, point.low), Number.POSITIVE_INFINITY);

  return (
    <section className="chart-panel chart-panel--fallback">
      <div className="section-heading">
        <p className="eyebrow">Market Structure</p>
        <h3>{title}</h3>
        {subtitle ? <p className="section-heading__subtle">{subtitle}</p> : null}
      </div>
      {data.length === 0 ? (
        <p className="chart-empty">{emptyMessage}</p>
      ) : (
        <div className="chart-fallback-grid">
          <dl>
            <dt>Last Close</dt>
            <dd>{formatNumber(last?.close ?? 0, 2)}</dd>
          </dl>
          <dl>
            <dt>Range High</dt>
            <dd>{formatNumber(high, 2)}</dd>
          </dl>
          <dl>
            <dt>Range Low</dt>
            <dd>{formatNumber(low, 2)}</dd>
          </dl>
          <dl>
            <dt>Bars</dt>
            <dd>{formatCompactNumber(data.length)}</dd>
          </dl>
        </div>
      )}
      {markers.length > 0 ? (
        <div className="chart-marker-list" aria-label="Trade markers">
          {markers.slice(0, 4).map((marker) => (
            <p key={`${marker.trade_id}-${marker.time}`}>
              {marker.action.replaceAll("_", " ")} at {formatTimestamp(marker.time)} for {formatNumber(marker.price, 2)}
            </p>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export function KlineChart({
  data,
  markers = [],
  title = "BTC / USDT",
  subtitle,
  theme,
  height = 420,
  className,
}: KlineChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = useRef<{ detach: () => void } | null>(null);
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
      localization: {
        dateFormat: "MMM dd",
      },
      handleScroll: false,
      handleScale: false,
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#2f855a",
      downColor: "#c53030",
      borderVisible: false,
      wickUpColor: "#2f855a",
      wickDownColor: "#c53030",
    });

    chartRef.current = chart;
    seriesRef.current = series;
    series.setData(
      data.map((point) => ({
        time: toChartTimestamp(point.time),
        open: point.open,
        high: point.high,
        low: point.low,
        close: point.close,
      })),
    );
    markersRef.current?.detach();
    markersRef.current = createSeriesMarkers(series, markers.map(mapMarker), {
      autoScale: true,
      zOrder: "top",
    });
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
      markersRef.current?.detach();
      markersRef.current = null;
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [data, height, markers, resolvedTheme, shouldRenderChart]);

  if (!shouldRenderChart) {
    return (
      <ChartFallback
        title={title}
        subtitle={subtitle}
        data={data}
        markers={markers}
        emptyMessage="Market data is not available for this range yet."
      />
    );
  }

  return (
    <section className={className ? `chart-panel ${className}` : "chart-panel"} aria-label={`${title} price chart`}>
      <div className="section-heading">
        <p className="eyebrow">Market Structure</p>
        <h3>{title}</h3>
        {subtitle ? <p className="section-heading__subtle">{subtitle}</p> : null}
      </div>
      <div ref={containerRef} className="chart-panel__canvas" style={{ height }} />
    </section>
  );
}
