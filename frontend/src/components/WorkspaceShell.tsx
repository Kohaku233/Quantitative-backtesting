import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import type { ReactNode } from "react";

type WorkspaceShellProps = {
  config: ReactNode;
  chart: ReactNode;
  dock: ReactNode;
  summary: ReactNode;
};

export function WorkspaceShell({
  config,
  chart,
  dock,
  summary,
}: WorkspaceShellProps) {
  return (
    <section className="workspace-shell" aria-label="Backtest workspace">
      <PanelGroup direction="horizontal" className="workspace-shell__group">
        <Panel defaultSize={24} minSize={18} maxSize={30} className="workspace-shell__panel">
          <aside className="workspace-shell__column workspace-shell__column--config">{config}</aside>
        </Panel>

        <PanelResizeHandle className="workspace-shell__handle" />

        <Panel defaultSize={56} minSize={38} className="workspace-shell__panel">
          <PanelGroup direction="vertical" className="workspace-shell__center">
            <Panel defaultSize={58} minSize={36} className="workspace-shell__panel">
              <div className="workspace-shell__column workspace-shell__column--chart">{chart}</div>
            </Panel>

            <PanelResizeHandle className="workspace-shell__handle workspace-shell__handle--horizontal" />

            <Panel defaultSize={42} minSize={24} className="workspace-shell__panel">
              <div className="workspace-shell__column workspace-shell__column--dock">{dock}</div>
            </Panel>
          </PanelGroup>
        </Panel>

        <PanelResizeHandle className="workspace-shell__handle" />

        <Panel defaultSize={20} minSize={16} maxSize={28} className="workspace-shell__panel">
          <aside className="workspace-shell__column workspace-shell__column--summary">{summary}</aside>
        </Panel>
      </PanelGroup>
    </section>
  );
}
