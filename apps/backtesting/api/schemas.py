"""Pydantic schemas for backtesting API"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestRunSummary(BaseModel):
    id: int
    strategy_name: str
    strategy_version: str
    symbols: List[str]
    start_date: date
    end_date: date
    interval: str
    total_trades: int
    win_rate: float
    roi: float
    total_pnl: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    created_at: datetime


class BacktestTradeRead(BaseModel):
    id: int
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    side: str
    qty: float
    pnl: float
    pnl_percent: float
    exit_reason: str
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_amount: Optional[float]
    risk_percent: Optional[float]
    duration_seconds: int
    details: Optional[Dict[str, Any]]


class BacktestRunDetail(BaseModel):
    id: int
    strategy_name: str
    strategy_version: str
    params_json: Dict[str, Any]
    symbols: List[str]
    start_date: date
    end_date: date
    interval: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    initial_capital: float
    final_capital: float
    total_pnl: float
    roi: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: float
    avg_win: Optional[float]
    avg_loss: Optional[float]
    profit_factor: Optional[float]
    execution_time_seconds: Optional[float]
    data_source: str
    created_at: datetime
    notes: Optional[str]


class BacktestRunRequest(BaseModel):
    strategy_name: str = Field(..., description="Strategy version to run")
    symbols: List[str]
    start_date: date
    end_date: date
    interval: str = "1d"
    params: Dict[str, Any] = Field(default_factory=dict)
    initial_capital: Optional[float] = None
    notes: Optional[str] = None


class GridSearchRequest(BaseModel):
    strategy_name: str
    symbols: List[str]
    start_date: date
    end_date: date
    interval: str = "1d"
    param_grid: Dict[str, List[Any]]
    max_workers: int = 4


class AnalyticsSummary(BaseModel):
    total_runs: int
    total_trades: int
    avg_roi: float
    best_roi: float
    worst_roi: float
    best_strategy: Optional[str]
    best_symbols: Optional[List[str]]
    cumulative_pnl: float


class APIResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None
    timestamp: datetime


def format_response(data: Dict[str, Any], message: Optional[str] = None) -> APIResponse:
    return APIResponse(success=True, data=data, message=message, timestamp=datetime.utcnow())
