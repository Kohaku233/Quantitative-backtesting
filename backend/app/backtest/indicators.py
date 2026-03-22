import math

import pandas as pd

from backend.app.strategies.base import StrategyExecutionError


def validate_signal_series(signals: pd.Series, expected_index: pd.Index) -> pd.Series:
    if not isinstance(signals, pd.Series):
        raise StrategyExecutionError("Strategy must return a pandas Series of signals.")
    if not signals.index.equals(expected_index):
        raise StrategyExecutionError("Strategy signal index must match market data index.")
    if signals.isna().any():
        raise StrategyExecutionError("Strategy signals must not contain null values.")

    invalid_values = {
        value
        for value in signals.tolist()
        if not isinstance(value, (int, float)) or not float(value).is_integer() or int(value) not in (-1, 0, 1)
    }
    if invalid_values:
        raise StrategyExecutionError(f"Strategy signals contain invalid values: {sorted(invalid_values)}")
    normalized = signals.astype("int8")
    if not normalized.apply(math.isfinite).all():
        raise StrategyExecutionError("Strategy signals must be finite values.")
    return normalized
