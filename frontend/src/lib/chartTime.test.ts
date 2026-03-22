import { describe, expect, test } from "vitest";

import { toChartTimestamp } from "./chartTime";


describe("toChartTimestamp", () => {
  test("normalizes ISO timestamps with fractional seconds into unix seconds", () => {
    expect(toChartTimestamp("2024-01-09T15:59:59.999000Z")).toBe(1704815999);
  });

  test("throws for invalid timestamps", () => {
    expect(() => toChartTimestamp("not-a-timestamp")).toThrow(/invalid date/i);
  });
});
