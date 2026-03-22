from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from pydantic import field_validator, model_validator


class CoverageRange(BaseModel):
    start: str
    end: str


class CoverageSection(BaseModel):
    cached_start: str | None
    cached_end: str | None
    missing_ranges: list[CoverageRange]


class CoverageStatusResponse(BaseModel):
    symbol: str
    strategy_id: str
    timeframe: str
    requested_start: str
    requested_end: str
    effective_start: str
    effective_end: str
    complete: bool
    kline: CoverageSection
    funding: CoverageSection


class DataSyncRequest(BaseModel):
    strategy_id: str
    symbol: str
    timeframe: Literal["15m", "1h", "4h", "1d"]
    start: str
    end: str

    @field_validator("strategy_id", "symbol")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized

    @field_validator("start", "end")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timestamp must include a timezone offset")
        return value

    @model_validator(mode="after")
    def validate_range(self):
        start = datetime.fromisoformat(self.start.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.end.replace("Z", "+00:00"))
        if end < start:
            raise ValueError("end must be greater than or equal to start")
        return self


class DownloadedRows(BaseModel):
    kline_rows: int
    funding_rows: int


class SyncError(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class DataSyncResponse(BaseModel):
    status: str
    symbol: str
    strategy_id: str
    timeframe: str
    requested_start: str
    requested_end: str
    effective_start: str
    effective_end: str
    complete: bool
    downloaded: DownloadedRows
    coverage: CoverageStatusResponse
    error: SyncError | None = None
