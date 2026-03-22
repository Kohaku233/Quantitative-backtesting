from __future__ import annotations


def _normalize_side(side: str) -> str:
    value = side.strip().lower()
    if value not in {"long", "short"}:
        raise ValueError(f"Unsupported position side: {side!r}")
    return value


def calculate_liquidation_price(
    side: str,
    entry_price: float,
    quantity: float,
    isolated_margin_balance: float,
    maintenance_margin_rate: float,
) -> float:
    side_value = _normalize_side(side)
    if side_value == "long":
        return (quantity * entry_price - isolated_margin_balance) / (quantity * (1 - maintenance_margin_rate))
    return (isolated_margin_balance + quantity * entry_price) / (quantity * (1 + maintenance_margin_rate))
