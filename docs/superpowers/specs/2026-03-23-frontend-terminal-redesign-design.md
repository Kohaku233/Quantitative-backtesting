# Frontend Terminal Redesign Design

**Date:** 2026-03-23

**Goal:** Replace the current dashboard-like workspace with a chart-first quantitative terminal that matches how serious backtesting tools organize controls, market context, and execution results.

## Problem Statement

The current frontend is functionally usable but structurally wrong for a backtesting product.

It over-prioritizes marketing-style framing, persistent card containers, and duplicated panels instead of the core analytical workflow. The result is a page that feels like a generic dashboard with charts rather than a research terminal.

The most damaging issues are:

- the oversized hero header consumes prime screen space without helping analysis
- the main price chart is visually subordinate to surrounding cards
- `Evidence Trail` duplicates trade information and fractures the user's attention
- metrics, coverage, and charts are all treated as same-weight cards
- the left setup column is too tall and too visually dominant
- the chart area does not behave like a serious trading terminal

## Design Direction

The redesign will follow a restrained terminal layout:

- chart-first
- data-dense but calm
- professional rather than promotional
- precise typography instead of decorative display type
- clear hierarchy driven by layout and contrast, not visual effects

The target experience is closer to a research workstation than a landing page. Users should feel that the platform is built for inspecting strategy behavior, not selling the idea of quant trading.

## Reference Product Patterns

This redesign intentionally follows the common structure seen across established backtesting and trading tools:

- TradingView-style chart dominance with bottom results/testing panels
- QuantConnect-style separation of summary statistics, charts, trades, and logs
- FMZ-style grouping of strategy configuration away from the core result surface

The redesign does **not** aim to clone any product visually. It borrows their layout logic: chart first, configuration secondary, results docked, tables tied directly to chart context.

## Layout Architecture

The page will be rebuilt around four zones.

### 1. Command Bar

A compact top command bar replaces the hero header.

It contains:

- symbol badge
- strategy selector
- timeframe selector
- date range controls
- sync status / coverage state
- primary run action
- secondary sync action
- theme toggle

This bar acts as the operating surface for the workspace. It should be fixed in purpose and visually compact.

### 2. Main Workspace

The central workspace becomes a three-region terminal shell:

- a collapsible left configuration rail
- a dominant center analysis surface
- a compact right summary/inspector rail

The center analysis surface gets the most width. On desktop it should visibly dominate the page. On narrower screens, the side rails collapse into drawers or stacked sections.

### 3. Chart Stack

The center surface is led by a large interactive K-line chart.

Below the chart, a synchronized dock hosts result tabs. The chart and dock together become the main analytical area.

The chart must support:

- drag/pan
- zoom
- visible-range movement
- crosshair inspection
- clear entry/exit markers
- trade-focused highlighting when a table row is selected

The chart is no longer paired with a dedicated `Evidence Trail` panel. That panel is removed entirely.

### 4. Bottom Dock

The result dock sits directly below the chart and uses tabs rather than separate equal-weight cards.

Tabs for the first iteration:

- `Trades`
- `Positions`
- `Funding`
- `Equity`
- `Drawdown`
- `Monthly Returns`
- `Coverage`

The default tab after a completed run should be `Trades`.

## Information Hierarchy

The redesigned hierarchy is:

1. main chart and active run context
2. run action and sync status
3. selected-trade details and key metrics
4. tabbed historical result views
5. configuration controls and coverage detail

Anything that is not directly helping the user run or inspect a backtest should move down the hierarchy or disappear.

## Component-Level Changes

### Remove

- hero-style top header
- large descriptive intro copy
- standalone `Evidence Trail` panel
- permanent large `Data Coverage` card in the primary flow
- equal-sized KPI card wall

### Add / Rebuild

- `CommandBar`
- `WorkspaceShell`
- `ConfigRail`
- `SummaryRail`
- `ResultTabs`
- `TradeInspector`
- `TradeList` with row selection and higher-density presentation

### Adapt Existing Components

- `KlineChart` becomes the dominant workspace surface
- `TradesTable` becomes the primary execution detail view
- `EquityChart` and `DrawdownChart` move into dock tabs
- `DataCoveragePanel` becomes a dock tab or collapsible utility panel
- `TopBar` is replaced rather than iterated
- `MetricsGrid` is replaced by a tighter summary strip / grouped stat blocks

## Trade Presentation Rules

Trade information will be reorganized to behave more like exchange and terminal tooling.

The trade table must:

- sit below the main chart inside the result dock
- show direction, entry, exit, quantity, allocated margin, notional, fees, funding, net PnL, return on margin, holding time, and exit reason
- support selecting a row to focus the related markers on the chart
- visually separate positive, negative, and neutral values without turning the table into a color wall

Trade markers should remain on the chart, but the descriptive breakdown belongs in the table, not in a separate signal feed.

## Visual System

The redesign will use a restrained terminal design system:

- sans serif body and UI font
- monospaced numeric support for tabular data
- icon system for structural cues, not decoration
- flatter surfaces and less ornamental background treatment
- reduced border radius and reduced card nesting
- calmer light/dark themes with tighter contrast control

Typography should feel technical and readable, not editorial.

## Component/Library Strategy

This redesign should stop hand-rolling every structural primitive.

Recommended foundation:

- headless UI primitives for tabs, select, tooltip, drawer, scroll areas, and resizable panels
- a consistent icon system
- a stronger table foundation for dense trade/result grids

This is not about making the interface look like a component library demo. The goal is to use reliable primitives while keeping the visual layer custom and product-specific.

## Interaction Model

The product should behave like a workstation:

- changing configuration clears stale result surfaces
- selecting a trade updates the chart focus
- switching dock tabs preserves chart context
- sync and run phases remain visible in a compact status strip
- utility information such as coverage detail is available without occupying prime visual space all the time

## Responsive Behavior

Desktop is the primary target for this product, but mobile and small laptop support still needs to be coherent.

- desktop: three-region terminal shell
- tablet: compact left controls, stacked right summary, dock retained
- mobile: command bar + collapsible config sections + chart + tabbed result stack

The mobile experience should preserve the workflow, not simply hide core features.

## Testing and Verification

The refactor must preserve the existing run/sync/result behaviors while changing layout and component boundaries.

Required verification:

- existing frontend tests still pass
- updated tests cover dock tabs and stale-result clearing after config changes
- production build passes
- live browser verification confirms:
  - chart remains interactive
  - result tabs render
  - `Evidence Trail` is gone
  - trade list is directly associated with the chart area

## Recommended Execution Order

1. establish the new layout shell and design tokens
2. replace the hero/header with the command bar
3. rebuild the workspace around chart + dock + summary rail
4. move trades, equity, drawdown, monthly returns, and coverage into dock tabs
5. wire trade-row selection to chart focus/highlighting
6. polish spacing, typography, iconography, and responsive behavior

## Success Criteria

The redesign is successful when:

- the chart is clearly the primary visual focus
- the page no longer reads like a dashboard or landing page
- trade detail lives below the chart, not in a duplicated side panel
- the workflow feels closer to a serious backtesting terminal
- the interface looks credible even before visual polish iterations
