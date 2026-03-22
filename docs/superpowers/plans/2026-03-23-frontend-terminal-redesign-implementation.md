# Frontend Terminal Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the current dashboard-like frontend into a chart-first quantitative terminal with a compact command bar, dominant interactive chart, docked result tabs, and denser trade analysis workflow.

**Architecture:** Keep the existing React + Vite app and backtest data flow, but replace the current page shell with a terminal layout. Reuse the working data hooks and chart/table logic where possible, then reorganize them into a new command bar, workspace shell, summary rail, and docked result system.

**Tech Stack:** React 19, TypeScript, Vite, lightweight-charts, Radix Tabs, react-resizable-panels, lucide-react, fontsource IBM Plex, Vitest, Testing Library

---

## File Structure

**Create:**

- `frontend/src/components/CommandBar.tsx`
- `frontend/src/components/ConfigRail.tsx`
- `frontend/src/components/ResultDock.tsx`
- `frontend/src/components/SummaryRail.tsx`
- `frontend/src/components/TradeInspector.tsx`
- `frontend/src/components/WorkspaceShell.tsx`
- `frontend/src/components/ResultDock.test.tsx`

**Modify:**

- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/components/DataCoveragePanel.tsx`
- `frontend/src/components/DrawdownChart.tsx`
- `frontend/src/components/EquityChart.tsx`
- `frontend/src/components/KlineChart.tsx`
- `frontend/src/components/MonthlyReturnsTable.tsx`
- `frontend/src/components/StatusBanner.tsx`
- `frontend/src/components/StrategyPanel.tsx`
- `frontend/src/components/TopBar.tsx`
- `frontend/src/components/TradesTable.tsx`
- `frontend/src/styles.css`

**Keep but de-emphasize / wrap:**

- `frontend/src/hooks/*`
- `frontend/src/lib/*`
- `frontend/src/types/contracts.ts`

---

## Chunk 1: Design Foundation And Terminal Shell

### Task 1: Add the UI foundation dependencies

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Add the required UI dependencies**

Add:

- `@fontsource/ibm-plex-sans`
- `@fontsource/ibm-plex-mono`
- `@radix-ui/react-tabs`
- `lucide-react`
- `react-resizable-panels`

- [ ] **Step 2: Install dependencies**

Run: `npm.cmd --prefix frontend install`
Expected: install completes without dependency conflicts

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add terminal ui foundation"
```

### Task 2: Replace the current hero/dashboard shell with the terminal shell

**Files:**
- Create: `frontend/src/components/WorkspaceShell.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write the failing layout test**

Add a test asserting that, after a completed run, the UI renders:

- a compact command bar
- a chart workspace region
- a docked result tablist
- no `Evidence Trail` section

- [ ] **Step 2: Run the layout test to confirm failure**

Run: `npm.cmd --prefix frontend test -- --run -t "renders the terminal workspace shell after a completed run"`
Expected: FAIL because the current page still renders the old dashboard layout

- [ ] **Step 3: Implement `WorkspaceShell` and move `App` to the new high-level structure**

Wire `App` so it renders:

- `CommandBar`
- `WorkspaceShell`
- left config rail
- center chart stack
- right summary rail
- bottom result dock

Remove the hero framing and the standalone evidence panel.

- [ ] **Step 4: Rework the top-level CSS tokens and shell layout**

Update `frontend/src/styles.css` to:

- drop the landing-page hero treatment
- flatten the background treatment
- reduce ornamental cards
- define terminal spacing and region sizes

- [ ] **Step 5: Run the updated test**

Run: `npm.cmd --prefix frontend test -- --run -t "renders the terminal workspace shell after a completed run"`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/components/WorkspaceShell.tsx frontend/src/styles.css
git commit -m "refactor: replace dashboard shell with terminal layout"
```

---

## Chunk 2: Controls, Summary, And Information Hierarchy

### Task 3: Build the compact command bar and summary rail

**Files:**
- Create: `frontend/src/components/CommandBar.tsx`
- Create: `frontend/src/components/SummaryRail.tsx`
- Modify: `frontend/src/components/TopBar.tsx`
- Modify: `frontend/src/components/StatusBanner.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write a failing test for compact control placement**

Add a test asserting that the primary actions and current run context are rendered in the command bar rather than in a hero region.

- [ ] **Step 2: Run the test to confirm failure**

Run: `npm.cmd --prefix frontend test -- --run -t "renders primary controls inside the command bar"`
Expected: FAIL

- [ ] **Step 3: Implement the command bar**

The bar must contain:

- strategy selector
- timeframe selector
- date range controls
- sync action
- run action
- theme toggle
- compact sync/result status

- [ ] **Step 4: Implement the summary rail**

Move KPI presentation into a tighter vertical summary:

- Net PnL
- Return
- Max Drawdown
- Sharpe
- Win Rate
- Profit Factor
- run settings summary

- [ ] **Step 5: Run the targeted test**

Run: `npm.cmd --prefix frontend test -- --run -t "renders primary controls inside the command bar"`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/components/CommandBar.tsx frontend/src/components/SummaryRail.tsx frontend/src/components/StatusBanner.tsx frontend/src/components/TopBar.tsx frontend/src/styles.css
git commit -m "feat: add command bar and summary rail"
```

### Task 4: Collapse the setup UI into a true configuration rail

**Files:**
- Create: `frontend/src/components/ConfigRail.tsx`
- Modify: `frontend/src/components/StrategyPanel.tsx`
- Modify: `frontend/src/components/DataCoveragePanel.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write a failing test asserting the old `Evidence Trail` and oversized setup structure are gone**

- [ ] **Step 2: Run the test to confirm failure**

Run: `npm.cmd --prefix frontend test -- --run -t "removes the evidence trail and uses a compact configuration rail"`
Expected: FAIL

- [ ] **Step 3: Implement `ConfigRail`**

Group controls into:

- Strategy
- Range
- Execution
- Costs
- Parameters

Coverage should become a secondary detail area, not a dominant permanent card.

- [ ] **Step 4: Adapt existing setup components into the rail**

Keep the current data model but shrink visual weight and allow the rail to collapse cleanly on smaller screens.

- [ ] **Step 5: Run the targeted test**

Run: `npm.cmd --prefix frontend test -- --run -t "removes the evidence trail and uses a compact configuration rail"`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/components/ConfigRail.tsx frontend/src/components/DataCoveragePanel.tsx frontend/src/components/StrategyPanel.tsx frontend/src/styles.css
git commit -m "refactor: convert setup panels into configuration rail"
```

---

## Chunk 3: Chart Workspace And Docked Result System

### Task 5: Rebuild the center workspace around the chart and dock

**Files:**
- Create: `frontend/src/components/ResultDock.tsx`
- Create: `frontend/src/components/ResultDock.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/KlineChart.tsx`
- Modify: `frontend/src/components/EquityChart.tsx`
- Modify: `frontend/src/components/DrawdownChart.tsx`
- Modify: `frontend/src/components/MonthlyReturnsTable.tsx`
- Modify: `frontend/src/components/TradesTable.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing tests for dock tabs**

Add tests covering:

- dock tablist renders after a completed run
- default tab is `Trades`
- `Evidence Trail` is absent
- switching to `Equity` and `Drawdown` tabs renders the respective content

- [ ] **Step 2: Run the dock tests to confirm failure**

Run: `npm.cmd --prefix frontend test -- --run src/components/ResultDock.test.tsx`
Expected: FAIL because the dock does not exist yet

- [ ] **Step 3: Implement `ResultDock` with Radix Tabs**

Tabs:

- Trades
- Positions
- Funding
- Equity
- Drawdown
- Monthly Returns
- Coverage

For the first iteration, `Positions` and `Funding` can render concise placeholders or derived data blocks if dedicated backend feeds are not yet present.

- [ ] **Step 4: Move result content into the dock**

Reorganize the existing result components so:

- chart stays above
- trades live below the chart
- equity/drawdown/monthly returns are dock tabs, not equal peer cards

- [ ] **Step 5: Make the chart more terminal-like**

Enable meaningful chart interaction:

- scrolling and scaling
- crosshair
- preserved visible range behavior

Do not attempt full drawing-tool parity in this pass.

- [ ] **Step 6: Run the dock tests**

Run: `npm.cmd --prefix frontend test -- --run src/components/ResultDock.test.tsx`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/ResultDock.tsx frontend/src/components/ResultDock.test.tsx frontend/src/components/KlineChart.tsx frontend/src/components/EquityChart.tsx frontend/src/components/DrawdownChart.tsx frontend/src/components/MonthlyReturnsTable.tsx frontend/src/components/TradesTable.tsx frontend/src/styles.css
git commit -m "feat: add docked result workspace"
```

### Task 6: Tie the trade list to chart context

**Files:**
- Create: `frontend/src/components/TradeInspector.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/KlineChart.tsx`
- Modify: `frontend/src/components/TradesTable.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write a failing test for selected trade behavior**

Assert that selecting a trade row:

- marks that row as active
- updates the inspector region
- passes selected trade context to the chart component

- [ ] **Step 2: Run the test to confirm failure**

Run: `npm.cmd --prefix frontend test -- --run -t "syncs selected trade rows with the inspector and chart context"`
Expected: FAIL

- [ ] **Step 3: Add selected-trade state to `App`**

Store the active trade id and pass it to:

- `TradesTable`
- `TradeInspector`
- `KlineChart`

- [ ] **Step 4: Update the chart and table components**

Make the selected trade more visible by:

- emphasizing its markers
- highlighting the active table row
- surfacing its details in the right rail

- [ ] **Step 5: Run the targeted test**

Run: `npm.cmd --prefix frontend test -- --run -t "syncs selected trade rows with the inspector and chart context"`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/components/TradeInspector.tsx frontend/src/components/KlineChart.tsx frontend/src/components/TradesTable.tsx frontend/src/styles.css
git commit -m "feat: connect trades to chart context"
```

---

## Chunk 4: Visual System And Final Verification

### Task 7: Apply the terminal typography, iconography, and density pass

**Files:**
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/*.tsx` as needed

- [ ] **Step 1: Load IBM Plex fonts and use lucide-react icons in command and summary surfaces**

- [ ] **Step 2: Tighten spacing, borders, density, and numeric alignment**

- [ ] **Step 3: Remove remaining dashboard/card anti-patterns**

- [ ] **Step 4: Run frontend tests**

Run: `npm.cmd --prefix frontend test`
Expected: all tests pass

- [ ] **Step 5: Run production build**

Run: `npm.cmd --prefix frontend run build`
Expected: build succeeds

- [ ] **Step 6: Commit**

```bash
git add frontend/src
git commit -m "style: polish terminal workspace"
```

### Task 8: Live verification

**Files:**
- No code changes required unless issues are found

- [ ] **Step 1: Run backend tests**

Run: `F:\\code\\Quantitative-backtesting\\.worktrees\\quant-platform\\.venv\\Scripts\\python.exe -m pytest backend\\tests -q`
Expected: all tests pass

- [ ] **Step 2: Start backend and frontend locally**

Run backend:

```powershell
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Run frontend:

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

- [ ] **Step 3: Verify the redesigned workflow in a real browser**

Check:

- chart dominates the page
- dock tabs work
- `Evidence Trail` is gone
- trades live below the chart
- selecting a trade updates the inspector and chart emphasis
- run/sync flow still works

- [ ] **Step 4: Push the completed branch**

```bash
git push origin codex/quant-backtesting-platform
```
