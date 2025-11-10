"""Types used by the backtesting engine"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class SimulatedTrade:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    side: str
    qty: float
    pnl: float
    pnl_percent: float
    duration_seconds: int
    exit_reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_amount: Optional[float] = None
    risk_percent: Optional[float] = None
    commission: float = 0.0
    slippage: float = 0.0
    details: Dict[str, float] | Dict[str, str] | Dict[str, object] = field(default_factory=dict)


@dataclass
class BacktestSummary:
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    final_capital: float
    roi: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    max_drawdown_duration: Optional[int]
    win_rate: float
    avg_win: Optional[float]
    avg_loss: Optional[float]
    profit_factor: Optional[float]
    execution_time_seconds: float
