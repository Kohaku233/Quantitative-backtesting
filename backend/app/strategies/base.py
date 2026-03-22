from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

import pandas as pd

from backend.app.models.strategies import StrategyMetadata


class StrategyValidationError(ValueError):
    """Raised when strategy parameters are invalid."""


class StrategyExecutionError(RuntimeError):
    """Raised when a strategy produces malformed outputs."""


class BaseStrategyPlugin(ABC):
    id: str
    name: str
    description: str
    supported_timeframes: tuple[str, ...]
    required_lookback_bars: int
    parameter_schema: list[dict[str, Any]]

    @classmethod
    @abstractmethod
    def validate_params(cls, params: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def compute_indicators(
        cls,
        df: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.DataFrame:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        raise NotImplementedError

    @classmethod
    def to_metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            id=cls.id,
            name=cls.name,
            description=cls.description,
            supported_timeframes=list(cls.supported_timeframes),
            required_lookback_bars=cls.required_lookback_bars,
            parameter_schema=list(cls.parameter_schema),
        )
