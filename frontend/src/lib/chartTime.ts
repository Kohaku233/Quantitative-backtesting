import type { UTCTimestamp } from "lightweight-charts";


export function toChartTimestamp(value: string): UTCTimestamp {
  const timestamp = Date.parse(value);

  if (Number.isNaN(timestamp)) {
    throw new RangeError(`Invalid date string=${value}`);
  }

  return Math.floor(timestamp / 1000) as UTCTimestamp;
}
