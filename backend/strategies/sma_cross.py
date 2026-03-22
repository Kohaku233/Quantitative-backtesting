from collections.abc import Mapping
from typing import Any

import pandas as pd

from backend.app.strategies.base import BaseStrategyPlugin, StrategyValidationError


class SmaCrossStrategy(BaseStrategyPlugin):
    id = "sma_cross"
    name = "SMA Cross"
    description = "Long/short moving-average crossover strategy."
    supported_timeframes = ("15m", "1h", "4h", "1d")
    required_lookback_bars = 200
    parameter_schema = [
        {
            "key": "fast_period",
            "label": "Fast Period",
            "type": "integer",
            "default": 20,
            "required": True,
            "min": 1,
            "max": 500,
            "step": 1,
            "help": "Short moving average period.",
        },
        {
            "key": "slow_period",
            "label": "Slow Period",
            "type": "integer",
            "default": 50,
            "required": True,
            "min": 2,
            "max": 500,
            "step": 1,
            "help": "Long moving average period.",
        },
    ]

    @classmethod
    def validate_params(cls, params: Mapping[str, Any]) -> dict[str, Any]:
        fast = int(params["fast_period"])
        slow = int(params["slow_period"])
        if fast >= slow:
            raise StrategyValidationError("fast_period must be less than slow_period")

        return {"fast_period": fast, "slow_period": slow}

    @classmethod
    def compute_indicators(
        cls,
        df: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "fast_sma": df["close"].rolling(int(params["fast_period"])).mean(),
                "slow_sma": df["close"].rolling(int(params["slow_period"])).mean(),
            },
            index=df.index,
        )

    @classmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        signals = pd.Series(0, index=df.index, dtype="int8")
        signals.loc[indicators["fast_sma"] > indicators["slow_sma"]] = 1
        signals.loc[indicators["fast_sma"] < indicators["slow_sma"]] = -1
        return signals
