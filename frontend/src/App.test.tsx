import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import App from "./App";

test("renders workspace shell", () => {
  render(<App />);

  expect(screen.getByText(/quantitative backtesting workspace/i)).toBeInTheDocument();
});
