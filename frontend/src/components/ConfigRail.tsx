import type { ReactNode } from "react";

type ConfigRailProps = {
  children: ReactNode;
};

export function ConfigRail({ children }: ConfigRailProps) {
  return (
    <section className="config-rail" aria-label="Backtest configuration">
      <div className="config-rail__header">
        <p className="eyebrow">Backtest Setup</p>
        <h2>Configuration</h2>
        <p className="section-heading__subtle">
          Keep the operating controls compact and move deeper parameter editing into the rail.
        </p>
      </div>

      <div className="config-rail__body">{children}</div>
    </section>
  );
}
