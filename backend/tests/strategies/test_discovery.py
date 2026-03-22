from pathlib import Path
from textwrap import dedent

from backend.app.strategies.discovery import discover_strategies


VALID_PLUGIN = """
from typing import Any, Mapping

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
            "help": "Short moving average period."
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
            "help": "Long moving average period."
        }
    ]

    @classmethod
    def validate_params(cls, params: Mapping[str, Any]) -> dict[str, Any]:
        fast = int(params["fast_period"])
        slow = int(params["slow_period"])
        if fast >= slow:
            raise StrategyValidationError("fast_period must be less than slow_period")
        return {"fast_period": fast, "slow_period": slow}

    @classmethod
    def compute_indicators(cls, df: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
        return pd.DataFrame(index=df.index)

    @classmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        return pd.Series(0, index=df.index, dtype="int8")
"""


BROKEN_PLUGIN = """
raise ImportError("missing dependency")
"""


DUPLICATE_PLUGIN = """
from typing import Any, Mapping

import pandas as pd

from backend.app.strategies.base import BaseStrategyPlugin


class DuplicateSmaCrossStrategy(BaseStrategyPlugin):
    id = "sma_cross"
    name = "Duplicate SMA Cross"
    description = "Duplicate id plugin."
    supported_timeframes = ("1h",)
    required_lookback_bars = 10
    parameter_schema = []

    @classmethod
    def validate_params(cls, params: Mapping[str, Any]) -> dict[str, Any]:
        return {}

    @classmethod
    def compute_indicators(cls, df: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
        return pd.DataFrame(index=df.index)

    @classmethod
    def generate_signals(
        cls,
        df: pd.DataFrame,
        indicators: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        return pd.Series(0, index=df.index, dtype="int8")
"""


INVALID_CONTRACT_PLUGIN = """
from typing import Any, Mapping

import pandas as pd

from backend.app.strategies.base import BaseStrategyPlugin


class InvalidContractStrategy(BaseStrategyPlugin):
    id = "invalid_contract"
    name = "Invalid Contract"
    description = "Plugin with the wrong method contract."
    supported_timeframes = ("1h",)
    required_lookback_bars = 10
    parameter_schema = []

    def validate_params(self, params: Mapping[str, Any]) -> dict[str, Any]:
        return {}

    def compute_indicators(self, df: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
        return pd.DataFrame(index=df.index)

    def generate_signals(self, df: pd.DataFrame, indicators: pd.DataFrame, params: Mapping[str, Any]) -> pd.Series:
        return pd.Series(0, index=df.index, dtype="int8")
"""


ABSTRACT_PLUGIN = """
from backend.app.strategies.base import BaseStrategyPlugin


class AbstractMetadataOnlyStrategy(BaseStrategyPlugin):
    id = "abstract_strategy"
    name = "Abstract Strategy"
    description = "Metadata only; abstract methods not implemented."
    supported_timeframes = ("1h",)
    required_lookback_bars = 20
    parameter_schema = []
"""


def _write_plugin(path: Path, content: str) -> None:
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def test_discovery_skips_invalid_plugins_and_returns_warnings(tmp_path: Path) -> None:
    _write_plugin(tmp_path / "sma_cross.py", VALID_PLUGIN)
    _write_plugin(tmp_path / "broken_plugin.py", BROKEN_PLUGIN)
    _write_plugin(tmp_path / "duplicate_sma_cross.py", DUPLICATE_PLUGIN)
    _write_plugin(tmp_path / "invalid_contract.py", INVALID_CONTRACT_PLUGIN)
    _write_plugin(tmp_path / "abstract_plugin.py", ABSTRACT_PLUGIN)

    strategies, warnings = discover_strategies(tmp_path)

    assert strategies == []
    warning_dicts = [warning.model_dump() for warning in warnings]
    assert {
        "file": "broken_plugin.py",
        "reason": "ImportError: missing dependency",
    } in warning_dicts
    assert {
        "file": "sma_cross.py",
        "reason": "duplicate id 'sma_cross'",
    } in warning_dicts
    assert {
        "file": "duplicate_sma_cross.py",
        "reason": "duplicate id 'sma_cross'",
    } in warning_dicts
    assert {
        "file": "invalid_contract.py",
        "reason": "TypeError: validate_params must be declared as a @classmethod",
    } in warning_dicts
    assert {
        "file": "abstract_plugin.py",
        "reason": "TypeError: plugin class must implement all abstract strategy methods",
    } in warning_dicts


def test_discovery_finds_real_shipped_strategy() -> None:
    strategies, warnings = discover_strategies(Path("backend/strategies"))

    assert [strategy.id for strategy in strategies] == ["sma_cross"]
    assert warnings == []
