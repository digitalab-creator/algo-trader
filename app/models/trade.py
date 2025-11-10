from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.strategy_run import StrategyRun


class Trade(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    layer: str
    strategy: str
    side: str
    qty: int
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    budget_allocated: Optional[float] = None
    entry_signal: Optional[str] = None
    exit_signal: Optional[str] = None
    order_status: Optional[str] = None
    signal_snapshot: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    exit_snapshot: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    notes: Optional[str] = None
    strategy_run_id: int | None = Field(
        default=None, foreign_key="strategyrun.id"
    )
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: datetime | None = None

