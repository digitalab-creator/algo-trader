"""
Trading routes - trades and strategy runs.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.config import Settings, get_settings
from app.models.strategy_run import StrategyRun
from app.models.trade import Trade
from lib.infrastructure import AppContext

router = APIRouter(tags=["trades"])


def get_context() -> AppContext:
    """Get application context (injected from main)."""
    from app.main import context
    return context


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Algo-Fleet API ready"}


@router.get("/health", tags=["system"])
async def health_detailed(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """
    Detailed health check with mode information.
    
    Note: Basic /health is auto-included by lib/infrastructure.
    """
    return {
        "status": "ok",
        "mode": settings.mode,
        "service": "algo-fleet",
    }


@router.get("/trades")
async def list_trades(
    strategy: str | None = None,
    layer: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    context: AppContext = Depends(get_context),
) -> list[Trade]:
    """
    List trades with optional filters.
    
    Args:
        strategy: Filter by strategy name
        layer: Filter by risk layer (high/medium/low)
        limit: Maximum number of trades to return
        context: Application context (auto-injected)
    
    Returns:
        List of Trade objects
    """
    async with context.db.session() as session:
        statement = select(Trade).order_by(Trade.opened_at.desc()).limit(limit)
        
        if strategy:
            statement = statement.where(Trade.strategy == strategy)
        if layer:
            statement = statement.where(Trade.layer == layer)
        
        result = await session.execute(statement)
        return result.scalars().all()


@router.get("/strategy-runs")
async def list_strategy_runs(
    strategy: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    context: AppContext = Depends(get_context),
) -> list[StrategyRun]:
    """
    List strategy execution runs.
    
    Args:
        strategy: Filter by strategy name
        status: Filter by status (pending/running/completed/failed)
        limit: Maximum number of runs to return
        context: Application context (auto-injected)
    
    Returns:
        List of StrategyRun objects
    """
    async with context.db.session() as session:
        statement = select(StrategyRun).order_by(StrategyRun.started_at.desc()).limit(limit)
        
        if strategy:
            statement = statement.where(StrategyRun.strategy == strategy)
        if status:
            statement = statement.where(StrategyRun.status == status)
        
        result = await session.execute(statement)
        return result.scalars().all()

