"""Order execution simulator for backtesting"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from libs.strategies.base import TradeSignal
from apps.backtesting.engine.types import SimulatedTrade


@dataclass
class SimulationConfig:
    commission_per_trade: float = 0.0
    slippage_per_share: float = 0.0


def _find_entry_index(df: pd.DataFrame, timestamp: datetime) -> Optional[int]:
    if timestamp in df.index:
        return df.index.get_loc(timestamp)

    # Find first index after timestamp
    idx = df.index.searchsorted(timestamp)
    if idx >= len(df.index):
        return None
    return idx


def simulate_trade(
    signal: TradeSignal,
    df: pd.DataFrame,
    *,
    current_equity: float,
    config: SimulationConfig,
) -> Optional[SimulatedTrade]:
    """Simulate a trade based on a trade signal and price data."""

    entry_idx = _find_entry_index(df, signal.timestamp)
    if entry_idx is None:
        return None

    entry_row = df.iloc[entry_idx]
    entry_price = float(signal.entry_price or entry_row["close"])

    stop_loss = signal.stop_loss
    take_profit = signal.take_profit

    # Provide reasonable defaults if not supplied
    if stop_loss is None:
        stop_loss = entry_price * (0.98 if signal.side == "buy" else 1.02)
    if take_profit is None:
        take_profit = entry_price * (1.03 if signal.side == "buy" else 0.97)

    risk_percent = signal.risk_percent or 0.01
    risk_amount = current_equity * risk_percent
    risk_per_unit = abs(entry_price - stop_loss)
    if risk_per_unit <= 0:
        return None

    qty = risk_amount / risk_per_unit
    if qty <= 0:
        return None

    if signal.side == "sell":
        qty = -qty

    position_value = abs(qty * entry_price)
    if position_value > current_equity and position_value > 0:
        scale = current_equity / position_value
        qty *= scale
        risk_amount *= scale

    if abs(qty) < 1e-6:
        return None

    holding_period_minutes = signal.holding_period_minutes
    max_holding_timedelta = (
        timedelta(minutes=holding_period_minutes) if holding_period_minutes else None
    )

    exit_price = float(df.iloc[-1]["close"])
    exit_time_raw = df.index[-1]
    exit_time = exit_time_raw.to_pydatetime() if hasattr(exit_time_raw, "to_pydatetime") else exit_time_raw
    exit_reason = "end_of_period"

    entry_time_raw = df.index[entry_idx]
    entry_time = entry_time_raw.to_pydatetime() if hasattr(entry_time_raw, "to_pydatetime") else entry_time_raw

    for idx in range(entry_idx + 1, len(df)):
        row = df.iloc[idx]
        timestamp_raw = df.index[idx]
        timestamp = timestamp_raw.to_pydatetime() if hasattr(timestamp_raw, "to_pydatetime") else timestamp_raw

        # Stop-loss check
        if signal.side == "buy":
            if row["low"] <= stop_loss:
                exit_price = float(stop_loss - config.slippage_per_share)
                exit_time = timestamp
                exit_reason = "stop_loss"
                break
            if row["high"] >= take_profit:
                exit_price = float(take_profit - config.slippage_per_share)
                exit_time = timestamp
                exit_reason = "take_profit"
                break
        else:
            if row["high"] >= stop_loss:
                exit_price = float(stop_loss + config.slippage_per_share)
                exit_time = timestamp
                exit_reason = "stop_loss"
                break
            if row["low"] <= take_profit:
                exit_price = float(take_profit + config.slippage_per_share)
                exit_time = timestamp
                exit_reason = "take_profit"
                break

        if max_holding_timedelta and timestamp - entry_time >= max_holding_timedelta:
            exit_price = float(row["close"])
            exit_time = timestamp
            exit_reason = "time_exit"
            break

    pnl = (exit_price - entry_price) * qty if qty >= 0 else (entry_price - exit_price) * abs(qty)
    pnl -= config.commission_per_trade

    duration_seconds = int((exit_time - entry_time).total_seconds()) if exit_time and entry_time else 0

    pnl_percent = (pnl / (abs(qty) * entry_price)) * 100 if qty != 0 else 0.0

    trade = SimulatedTrade(
        symbol=signal.symbol,
        entry_time=entry_time,
        exit_time=exit_time,
        entry_price=entry_price,
        exit_price=exit_price,
        side=signal.side,
        qty=qty,
        pnl=pnl,
        pnl_percent=pnl_percent,
        duration_seconds=duration_seconds,
        exit_reason=exit_reason,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_amount=risk_amount,
        risk_percent=risk_percent,
        commission=config.commission_per_trade,
        slippage=config.slippage_per_share,
        details=signal.metadata,
    )

    return trade
