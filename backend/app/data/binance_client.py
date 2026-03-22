from datetime import UTC, datetime
from typing import Any

import httpx

from backend.app.data.coverage import (
    FUNDING_INTERVAL,
    floor_to_step,
    format_timestamp,
    parse_timestamp,
    timeframe_delta,
)


class BinancePublicClient:
    def __init__(
        self,
        *,
        base_url: str = "https://fapi.binance.com",
        timeout: float = 30.0,
        kline_limit: int = 1500,
        funding_limit: int = 1000,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.kline_limit = kline_limit
        self.funding_limit = funding_limit

    async def _request_json(self, path: str, params: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    async def fetch_klines(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
    ) -> list[dict[str, Any]]:
        start_at = parse_timestamp(start)
        end_at = parse_timestamp(end)
        candle_delta = timeframe_delta(timeframe)
        rows: list[dict[str, Any]] = []
        cursor = start_at

        while cursor <= end_at:
            payload = await self._request_json(
                "/fapi/v1/klines",
                {
                    "symbol": symbol,
                    "interval": timeframe,
                    "startTime": int(cursor.timestamp() * 1000),
                    "endTime": int((end_at + candle_delta).timestamp() * 1000) - 1,
                    "limit": self.kline_limit,
                },
            )
            if not payload:
                break

            for row in payload:
                open_time = parse_timestamp_from_ms(int(row[0]))
                if open_time < start_at or open_time > end_at:
                    continue

                rows.append(
                    {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "open_time": format_timestamp(open_time),
                        "close_time": format_timestamp(parse_timestamp_from_ms(int(row[6]))),
                        "open": float(row[1]),
                        "high": float(row[2]),
                        "low": float(row[3]),
                        "close": float(row[4]),
                        "volume": float(row[5]),
                    }
                )

            if len(payload) < self.kline_limit:
                break

            next_cursor = parse_timestamp_from_ms(int(payload[-1][0])) + candle_delta
            if next_cursor <= cursor:
                break
            cursor = next_cursor

        return rows

    async def fetch_funding_rates(
        self,
        *,
        symbol: str,
        start: str,
        end: str,
    ) -> list[dict[str, Any]]:
        start_at = parse_timestamp(start)
        end_at = parse_timestamp(end)
        rows: list[dict[str, Any]] = []
        cursor = start_at

        while cursor <= end_at:
            payload = await self._request_json(
                "/fapi/v1/fundingRate",
                {
                    "symbol": symbol,
                    "startTime": int(cursor.timestamp() * 1000),
                    "endTime": int((end_at + FUNDING_INTERVAL).timestamp() * 1000) - 1,
                    "limit": self.funding_limit,
                },
            )
            if not payload:
                break

            for row in payload:
                funding_time = floor_to_step(
                    parse_timestamp_from_ms(int(row["fundingTime"])),
                    FUNDING_INTERVAL,
                )
                if funding_time < start_at or funding_time > end_at:
                    continue
                rows.append(
                    {
                        "symbol": symbol,
                        "funding_time": format_timestamp(funding_time),
                        "funding_rate": float(row["fundingRate"]),
                    }
                )

            if len(payload) < self.funding_limit:
                break

            next_cursor = floor_to_step(
                parse_timestamp_from_ms(int(payload[-1]["fundingTime"])),
                FUNDING_INTERVAL,
            ) + FUNDING_INTERVAL
            if next_cursor <= cursor:
                break
            cursor = next_cursor
        return rows


def parse_timestamp_from_ms(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=UTC)
