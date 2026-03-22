from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from backend.app.data.coverage import (
    coerce_utc_datetime,
    compress_missing_ranges,
    format_timestamp,
    iter_expected_funding_timestamps,
    iter_expected_timestamps,
    normalize_request_range,
    shift_bars,
    timeframe_delta,
)
from backend.app.models.data_sync import CoverageSection, CoverageStatusResponse, DataSyncRequest


class DuckDbRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self):
        return duckdb.connect(str(self.database_path))

    def initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS klines (
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open_time TIMESTAMP NOT NULL,
                    close_time TIMESTAMP NOT NULL,
                    open DOUBLE NOT NULL,
                    high DOUBLE NOT NULL,
                    low DOUBLE NOT NULL,
                    close DOUBLE NOT NULL,
                    volume DOUBLE NOT NULL,
                    PRIMARY KEY(symbol, timeframe, open_time)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS funding_rates (
                    symbol TEXT NOT NULL,
                    funding_time TIMESTAMP NOT NULL,
                    funding_rate DOUBLE NOT NULL,
                    PRIMARY KEY(symbol, funding_time)
                )
                """
            )

    def upsert_klines(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return

        payload = [
            (
                row["symbol"],
                row["timeframe"],
                row["open_time"],
                row["close_time"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
            )
            for row in rows
        ]

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO klines (
                    symbol, timeframe, open_time, close_time, open, high, low, close, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )

    def upsert_funding_rates(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return

        payload = [
            (row["symbol"], row["funding_time"], row["funding_rate"])
            for row in rows
        ]

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO funding_rates (
                    symbol, funding_time, funding_rate
                ) VALUES (?, ?, ?)
                """,
                payload,
            )

    def count_rows(self, table: str) -> int:
        with self._connect() as connection:
            return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def _existing_timestamps(
        self,
        table: str,
        column: str,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str | None = None,
    ) -> set[datetime]:
        normalized_start = coerce_utc_datetime(start).replace(tzinfo=None)
        normalized_end = coerce_utc_datetime(end).replace(tzinfo=None)
        query = f"""
            SELECT {column}
            FROM {table}
            WHERE symbol = ?
              AND {column} BETWEEN ? AND ?
        """
        params: list[Any] = [symbol, normalized_start, normalized_end]
        if timeframe is not None:
            query += " AND timeframe = ?"
            params.append(timeframe)

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return {coerce_utc_datetime(row[0]) for row in rows}

    def _cached_bounds(
        self,
        table: str,
        column: str,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str | None = None,
    ) -> tuple[str | None, str | None]:
        normalized_start = coerce_utc_datetime(start).replace(tzinfo=None)
        normalized_end = coerce_utc_datetime(end).replace(tzinfo=None)
        query = f"""
            SELECT MIN({column}), MAX({column})
            FROM {table}
            WHERE symbol = ?
              AND {column} BETWEEN ? AND ?
        """
        params: list[Any] = [symbol, normalized_start, normalized_end]
        if timeframe is not None:
            query += " AND timeframe = ?"
            params.append(timeframe)

        with self._connect() as connection:
            min_value, max_value = connection.execute(query, params).fetchone()
        return format_timestamp(min_value), format_timestamp(max_value)

    def get_coverage(
        self,
        request: DataSyncRequest,
        required_lookback_bars: int,
    ) -> CoverageStatusResponse:
        effective_start, effective_end = normalize_request_range(
            request.start,
            request.end,
            request.timeframe,
        )
        kline_start = shift_bars(effective_start, request.timeframe, required_lookback_bars)
        kline_step = timeframe_delta(request.timeframe)

        expected_klines = iter_expected_timestamps(kline_start, effective_end, kline_step)
        existing_klines = self._existing_timestamps(
            table="klines",
            column="open_time",
            symbol=request.symbol,
            start=kline_start,
            end=effective_end,
            timeframe=request.timeframe,
        )
        missing_klines = compress_missing_ranges(
            [value for value in expected_klines if value not in existing_klines],
            kline_step,
        )
        kline_cached_start, kline_cached_end = self._cached_bounds(
            table="klines",
            column="open_time",
            symbol=request.symbol,
            start=kline_start,
            end=effective_end,
            timeframe=request.timeframe,
        )

        expected_funding = iter_expected_funding_timestamps(effective_start, effective_end)
        existing_funding = self._existing_timestamps(
            table="funding_rates",
            column="funding_time",
            symbol=request.symbol,
            start=effective_start,
            end=effective_end,
        )
        missing_funding = compress_missing_ranges(
            [value for value in expected_funding if value not in existing_funding],
            timeframe_delta("1h") * 8,
        )
        funding_cached_start, funding_cached_end = self._cached_bounds(
            table="funding_rates",
            column="funding_time",
            symbol=request.symbol,
            start=effective_start,
            end=effective_end,
        )

        return CoverageStatusResponse(
            symbol=request.symbol,
            strategy_id=request.strategy_id,
            timeframe=request.timeframe,
            requested_start=request.start,
            requested_end=request.end,
            effective_start=format_timestamp(effective_start),
            effective_end=format_timestamp(effective_end),
            complete=not missing_klines and not missing_funding,
            kline=CoverageSection(
                cached_start=kline_cached_start,
                cached_end=kline_cached_end,
                missing_ranges=missing_klines,
            ),
            funding=CoverageSection(
                cached_start=funding_cached_start,
                cached_end=funding_cached_end,
                missing_ranges=missing_funding,
            ),
        )

    def load_klines(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        normalized_start = coerce_utc_datetime(start).replace(tzinfo=None)
        normalized_end = coerce_utc_datetime(end).replace(tzinfo=None)
        with self._connect() as connection:
            frame = connection.execute(
                """
                SELECT open_time, close_time, open, high, low, close, volume
                FROM klines
                WHERE symbol = ?
                  AND timeframe = ?
                  AND open_time BETWEEN ? AND ?
                ORDER BY open_time
                """,
                [symbol, timeframe, normalized_start, normalized_end],
            ).fetchdf()

        if frame.empty:
            empty = pd.DataFrame(
                columns=["close_time", "open", "high", "low", "close", "volume"],
                index=pd.DatetimeIndex([], tz=UTC, name="open_time"),
            )
            empty["close_time"] = pd.to_datetime(empty["close_time"], utc=True)
            return empty

        frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
        frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
        frame = frame.set_index("open_time")
        frame.index.name = "open_time"
        return frame

    def load_funding_rates(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        normalized_start = coerce_utc_datetime(start).replace(tzinfo=None)
        normalized_end = coerce_utc_datetime(end).replace(tzinfo=None)
        with self._connect() as connection:
            frame = connection.execute(
                """
                SELECT funding_time, funding_rate
                FROM funding_rates
                WHERE symbol = ?
                  AND funding_time BETWEEN ? AND ?
                ORDER BY funding_time
                """,
                [symbol, normalized_start, normalized_end],
            ).fetchdf()

        if frame.empty:
            return pd.DataFrame(
                columns=["funding_rate"],
                index=pd.DatetimeIndex([], tz=UTC, name="funding_time"),
            )

        frame["funding_time"] = pd.to_datetime(frame["funding_time"], utc=True)
        frame = frame.set_index("funding_time")
        frame.index.name = "funding_time"
        return frame
