"""Risk management helpers for strategies"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PositionSizing:
    qty: float
    risk_amount: float


def calculate_position_size(
    equity: float,
    risk_percent: float,
    entry_price: float,
    stop_price: float,
) -> PositionSizing:
    """Calculate position size based on risk percentage."""

    risk_amount = equity * risk_percent
    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share <= 0:
        raise ValueError("Risk per share must be positive")

    qty = max(risk_amount / risk_per_share, 0)
    return PositionSizing(qty=qty, risk_amount=risk_amount)
