from pydantic import BaseModel

from backend.app.models.common import JsonDict


class DiscoveryWarning(BaseModel):
    file: str
    reason: str


class StrategyMetadata(BaseModel):
    id: str
    name: str
    description: str
    supported_timeframes: list[str]
    required_lookback_bars: int
    parameter_schema: list[JsonDict]


class StrategiesResponse(BaseModel):
    strategies: list[StrategyMetadata]
    discovery_warnings: list[DiscoveryWarning]
