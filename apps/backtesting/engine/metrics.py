"""Metrics calculation for backtesting"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from apps.backtesting.engine.types import SimulatedTrade, BacktestSummary


def calculate_metrics(
    trades: List[SimulatedTrade],
    *,
    initial_capital: float,
    final_capital: float,
    equity_curve: list[tuple],
    execution_time_seconds: float,
) -> BacktestSummary:
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.pnl > 0)
    losing_trades = sum(1 for t in trades if t.pnl < 0)
    total_pnl = sum(t.pnl for t in trades)

    roi = ((final_capital - initial_capital) / initial_capital) * 100 if initial_capital else 0.0

    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [abs(t.pnl) for t in trades if t.pnl < 0]

    avg_win = float(np.mean(wins)) if wins else None
    avg_loss = float(np.mean(losses)) if losses else None
    profit_factor = (sum(wins) / sum(losses)) if wins and losses and sum(losses) != 0 else None

    win_rate = (winning_trades / total_trades) * 100 if total_trades else 0.0

    # Sharpe ratio approximation using trade returns
    returns = [t.pnl_percent / 100 for t in trades if t.pnl_percent]
    sharpe_ratio: Optional[float] = None
    if returns:
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        if std_return != 0:
            sharpe_ratio = (mean_return / std_return) * np.sqrt(252)  # Annualized

    # Max drawdown
    max_drawdown = 0.0
    max_duration = 0
    peak = equity_curve[0][1] if equity_curve else initial_capital
    peak_time = equity_curve[0][0] if equity_curve else None

    for timestamp, equity in equity_curve:
        if equity > peak:
            peak = equity
            peak_time = timestamp
        drawdown = (peak - equity) / peak if peak else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            if peak_time:
                max_duration = int((timestamp - peak_time).total_seconds() // 86400)

    return BacktestSummary(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_pnl=total_pnl,
        final_capital=final_capital,
        roi=roi,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown * 100,
        max_drawdown_duration=max_duration,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        execution_time_seconds=execution_time_seconds,
    )
