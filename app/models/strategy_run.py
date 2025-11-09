from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.trade import Trade


class StrategyRun(SQLModel, table=True):
    __tablename__ = "strategyrun"
    
    id: int | None = Field(default=None, primary_key=True)
    strategy: str
    layer: str
    status: str = Field(default="pending")
    budget: float | None = None
    signals_triggered: int = Field(default=0)
    trades_executed: int = Field(default=0)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    notes: str | None = None

