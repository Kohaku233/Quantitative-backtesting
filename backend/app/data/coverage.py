from datetime import UTC, datetime, timedelta

from backend.app.models.data_sync import CoverageRange


TIMEFRAME_DELTAS = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}
FUNDING_INTERVAL = timedelta(hours=8)


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone offset")
    return parsed.astimezone(UTC)


def coerce_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return coerce_utc_datetime(value).isoformat().replace("+00:00", "Z")


def timeframe_delta(timeframe: str) -> timedelta:
    try:
        return TIMEFRAME_DELTAS[timeframe]
    except KeyError as exc:
        raise ValueError(f"Unsupported timeframe: {timeframe}") from exc


def floor_to_step(value: datetime, step: timedelta) -> datetime:
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    seconds = int((value - epoch).total_seconds())
    step_seconds = int(step.total_seconds())
    floored = seconds - (seconds % step_seconds)
    return epoch + timedelta(seconds=floored)


def normalize_request_range(start: str, end: str, timeframe: str) -> tuple[datetime, datetime]:
    delta = timeframe_delta(timeframe)
    return floor_to_step(parse_timestamp(start), delta), floor_to_step(parse_timestamp(end), delta)


def shift_bars(value: datetime, timeframe: str, bars: int) -> datetime:
    return value - timeframe_delta(timeframe) * bars


def iter_expected_timestamps(start: datetime, end: datetime, step: timedelta) -> list[datetime]:
    current = start
    values: list[datetime] = []
    while current <= end:
        values.append(current)
        current += step
    return values


def iter_expected_funding_timestamps(start: datetime, end: datetime) -> list[datetime]:
    current = floor_to_step(start, FUNDING_INTERVAL)
    while current < start:
        current += FUNDING_INTERVAL
    values: list[datetime] = []
    while current <= end:
        values.append(current)
        current += FUNDING_INTERVAL
    return values


def compress_missing_ranges(values: list[datetime], step: timedelta) -> list[CoverageRange]:
    if not values:
        return []

    ranges: list[CoverageRange] = []
    range_start = values[0]
    previous = values[0]

    for current in values[1:]:
        if current - previous != step:
            ranges.append(
                CoverageRange(
                    start=format_timestamp(range_start),
                    end=format_timestamp(previous),
                )
            )
            range_start = current
        previous = current

    ranges.append(
        CoverageRange(
            start=format_timestamp(range_start),
            end=format_timestamp(previous),
        )
    )
    return ranges
