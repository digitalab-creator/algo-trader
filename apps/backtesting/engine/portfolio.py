"""Portfolio tracking for backtesting"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple


@dataclass
class Portfolio:
    initial_capital: float
    cash: float = field(init=False)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cash = self.initial_capital
        self.equity_curve.append((datetime.utcnow(), self.initial_capital))

    def apply_pnl(self, timestamp: datetime, pnl: float) -> None:
        self.cash += pnl
        self.equity_curve.append((timestamp, self.cash))

    @property
    def current_equity(self) -> float:
        return self.cash

    def max_drawdown(self) -> tuple[float, int]:
        max_equity = self.initial_capital
        max_drawdown = 0.0
        max_duration = 0
        peak_time = self.equity_curve[0][0]

        for timestamp, equity in self.equity_curve:
            if equity > max_equity:
                max_equity = equity
                peak_time = timestamp
            drawdown = (max_equity - equity) / max_equity if max_equity > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_duration = int((timestamp - peak_time).total_seconds() // 86400)

        return max_drawdown * 100, max_duration
