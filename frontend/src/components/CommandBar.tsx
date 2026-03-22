import type { CSSProperties } from "react";
import { Clock3, Database, MoonStar, Play, ShieldAlert, ShieldCheck, SunMedium } from "lucide-react";

type Theme = "light" | "dark";

type CommandBarProps = {
  brandLabel?: string;
  strategyName: string;
  symbol: string;
  timeframeLabel: string;
  rangeLabel: string;
  statusText?: string;
  coverageReady: boolean;
  theme: Theme;
  onToggleTheme: () => void;
  onSync?: () => void;
  onRun?: () => void;
  syncDisabled?: boolean;
  runDisabled?: boolean;
  syncLabel?: string;
  runLabel?: string;
  className?: string;
};

const shellStyle: CSSProperties = {
  display: "grid",
  gap: "14px",
  padding: "14px 16px",
  border: "1px solid var(--panel-border, rgba(120, 132, 160, 0.28))",
  borderRadius: "20px",
  background:
    "linear-gradient(180deg, color-mix(in oklch, var(--panel, white) 94%, transparent) 0%, color-mix(in oklch, var(--panel-strong, white) 88%, transparent) 100%)",
  boxShadow: "var(--shadow, 0 18px 44px rgba(49, 63, 84, 0.08))",
  backdropFilter: "blur(12px)",
};

const topRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "16px",
  flexWrap: "wrap",
};

const brandStyle: CSSProperties = {
  display: "grid",
  gap: "6px",
  minWidth: 0,
};

const brandLabelStyle: CSSProperties = {
  margin: 0,
  color: "var(--text-subtle, #667085)",
  fontSize: "0.72rem",
  fontWeight: 800,
  letterSpacing: "0.18em",
  textTransform: "uppercase",
};

const titleStyle: CSSProperties = {
  margin: 0,
  color: "var(--text, #1f2937)",
  fontSize: "clamp(1.1rem, 1.8vw, 1.35rem)",
  lineHeight: 1.1,
  letterSpacing: "-0.03em",
};

const subtitleStyle: CSSProperties = {
  margin: 0,
  color: "var(--text-subtle, #667085)",
  fontSize: "0.92rem",
  lineHeight: 1.45,
};

const actionRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
  flexWrap: "wrap",
  justifyContent: "flex-end",
};

const actionButtonStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
  minHeight: "38px",
  padding: "0.68rem 0.95rem",
  borderRadius: "999px",
  border: "1px solid var(--panel-border, rgba(120, 132, 160, 0.28))",
  background: "var(--input-bg, rgba(255, 255, 255, 0.72))",
  color: "var(--text, #1f2937)",
  font: "inherit",
};

const primaryActionStyle: CSSProperties = {
  ...actionButtonStyle,
  background: "color-mix(in oklch, var(--accent, #3f4f63) 14%, var(--panel-strong, white) 86%)",
  borderColor: "color-mix(in oklch, var(--accent, #3f4f63) 24%, var(--panel-border, rgba(120, 132, 160, 0.28)) 76%)",
};

const gridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
  gap: "10px",
};

const fieldStyle: CSSProperties = {
  display: "grid",
  gap: "4px",
  minWidth: 0,
  padding: "10px 12px",
  borderRadius: "14px",
  background: "color-mix(in oklch, var(--bg-muted, #eef2f7) 56%, transparent)",
};

const fieldLabelStyle: CSSProperties = {
  margin: 0,
  color: "var(--text-subtle, #667085)",
  fontSize: "0.7rem",
  fontWeight: 800,
  letterSpacing: "0.16em",
  textTransform: "uppercase",
};

const fieldValueStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
  margin: 0,
  color: "var(--text, #1f2937)",
  fontSize: "0.98rem",
  fontWeight: 700,
  lineHeight: 1.25,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const fieldNoteStyle: CSSProperties = {
  margin: 0,
  color: "var(--text-subtle, #667085)",
  fontSize: "0.82rem",
  lineHeight: 1.3,
};

export function CommandBar({
  brandLabel = "Local Crypto Research",
  strategyName,
  symbol,
  timeframeLabel,
  rangeLabel,
  statusText,
  coverageReady,
  theme,
  onToggleTheme,
  onSync,
  onRun,
  syncDisabled = false,
  runDisabled = false,
  syncLabel = "Sync",
  runLabel = "Run Backtest",
  className,
}: CommandBarProps) {
  const themeLabel = theme === "dark" ? "Switch to light" : "Switch to dark";
  const ThemeIcon = theme === "dark" ? SunMedium : MoonStar;
  const CoverageIcon = coverageReady ? ShieldCheck : ShieldAlert;

  return (
    <header className={className} style={shellStyle}>
      <div style={topRowStyle}>
        <div style={brandStyle}>
          <p style={brandLabelStyle}>{brandLabel}</p>
          <h1 style={titleStyle}>Quantitative Backtesting Workspace</h1>
          <p style={subtitleStyle}>
            {statusText ??
              "Chart-first terminal for strategy validation, coverage inspection, and execution review."}
          </p>
        </div>

        <div style={actionRowStyle} aria-label="Workspace actions">
          {onSync ? (
            <button type="button" style={actionButtonStyle} onClick={onSync} disabled={syncDisabled}>
              <Database size={15} aria-hidden="true" />
              {syncLabel}
            </button>
          ) : null}
          {onRun ? (
            <button type="button" style={primaryActionStyle} onClick={onRun} disabled={runDisabled}>
              <Play size={15} aria-hidden="true" />
              {runLabel}
            </button>
          ) : null}
          <button type="button" style={actionButtonStyle} onClick={onToggleTheme}>
            <ThemeIcon size={15} aria-hidden="true" />
            {themeLabel}
          </button>
        </div>
      </div>

      <div style={gridStyle} aria-label="Workspace context">
        <section style={fieldStyle}>
          <p style={fieldLabelStyle}>Symbol</p>
          <p style={fieldValueStyle}>{symbol} perpetual</p>
          <p style={fieldNoteStyle}>Primary market</p>
        </section>

        <section style={fieldStyle}>
          <p style={fieldLabelStyle}>Strategy</p>
          <p style={fieldValueStyle}>{strategyName}</p>
          <p style={fieldNoteStyle}>Active research target</p>
        </section>

        <section style={fieldStyle}>
          <p style={fieldLabelStyle}>Timeframe</p>
          <p style={fieldValueStyle}>
            <Clock3 size={14} aria-hidden="true" />
            {timeframeLabel}
          </p>
          <p style={fieldNoteStyle}>Bar resolution</p>
        </section>

        <section style={fieldStyle}>
          <p style={fieldLabelStyle}>Range</p>
          <p style={fieldValueStyle}>{rangeLabel}</p>
          <p style={fieldNoteStyle}>Historical window</p>
        </section>

        <section style={fieldStyle}>
          <p style={fieldLabelStyle}>Coverage</p>
          <p style={fieldValueStyle}>
            <CoverageIcon size={14} aria-hidden="true" />
            {coverageReady ? "Ready" : "Incomplete"}
          </p>
          <p style={fieldNoteStyle}>{coverageReady ? "Local cache is complete" : "Sync required before run"}</p>
        </section>
      </div>
    </header>
  );
}

export type { CommandBarProps, Theme };
