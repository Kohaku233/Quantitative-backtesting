import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { ResultDock } from "./ResultDock";

test("renders the trades tab by default", () => {
  render(
    <ResultDock
      trades={<div>Trades panel</div>}
      positions={<div>Positions panel</div>}
      funding={<div>Funding panel</div>}
      equity={<div>Equity panel</div>}
      drawdown={<div>Drawdown panel</div>}
      monthlyReturns={<div>Monthly returns panel</div>}
      coverage={<div>Coverage panel</div>}
    />,
  );

  expect(screen.getByRole("tab", { name: /trades/i })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByText("Trades panel")).toBeVisible();
  expect(screen.queryByText("Positions panel")).not.toBeInTheDocument();
});

test("switches visible content when a different tab is selected", () => {
  render(
    <ResultDock
      trades={<div>Trades panel</div>}
      positions={<div>Positions panel</div>}
      funding={<div>Funding panel</div>}
      equity={<div>Equity panel</div>}
      drawdown={<div>Drawdown panel</div>}
      monthlyReturns={<div>Monthly returns panel</div>}
      coverage={<div>Coverage panel</div>}
    />,
  );

  fireEvent.click(screen.getByRole("tab", { name: /equity/i }));

  expect(screen.getByRole("tab", { name: /equity/i })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByText("Equity panel")).toBeVisible();
  expect(screen.queryByText("Trades panel")).not.toBeInTheDocument();
});
