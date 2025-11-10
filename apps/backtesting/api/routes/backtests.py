"""Backtesting API routes"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, func

from apps.backtesting.api.dependencies import get_db_session
from apps.backtesting.api.schemas import (
    APIResponse,
    AnalyticsSummary,
    BacktestRunDetail,
    BacktestRunRequest,
    BacktestRunSummary,
    BacktestTradeRead,
    GridSearchRequest,
    format_response,
)
from apps.backtesting.config import get_settings
from apps.backtesting.db import get_session
from apps.backtesting.engine import BacktestEngine, SimulationConfig
from apps.backtesting.models import BacktestRun, BacktestTrade
import structlog


router = APIRouter(prefix="/backtests", tags=["backtests"])


def _create_engine(initial_capital: float | None = None) -> BacktestEngine:
    settings = get_settings()
    simulation_config = SimulationConfig(
        commission_per_trade=settings.simulation_commission,
        slippage_per_share=settings.simulation_slippage,
    )
    return BacktestEngine(
        get_session,
        initial_capital=initial_capital or settings.initial_capital,
        simulation_config=simulation_config,
    )


@router.get("/", response_model=APIResponse)
def list_backtests(
    strategy: str | None = None,
    min_roi: float | None = None,
    limit: int = 50,
    session: Session = Depends(get_db_session),
) -> APIResponse:
    query = select(BacktestRun).order_by(BacktestRun.created_at.desc()).limit(limit)
    if strategy:
        query = query.where(BacktestRun.strategy_name == strategy)
    if min_roi is not None:
        query = query.where(BacktestRun.roi >= min_roi)

    runs = session.exec(query).all()
    summaries = [
        BacktestRunSummary(
            id=run.id,
            strategy_name=run.strategy_name,
            strategy_version=run.strategy_version,
            symbols=run.symbols,
            start_date=run.start_date,
            end_date=run.end_date,
            interval=run.interval,
            total_trades=run.total_trades,
            win_rate=run.win_rate,
            roi=run.roi,
            total_pnl=run.total_pnl,
            sharpe_ratio=run.sharpe_ratio,
            max_drawdown=run.max_drawdown,
            created_at=run.created_at,
        )
        for run in runs
    ]

    return format_response({"runs": summaries})


@router.get("/{run_id}", response_model=APIResponse)
def get_backtest(run_id: int, session: Session = Depends(get_db_session)) -> APIResponse:
    run = session.get(BacktestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    detail = BacktestRunDetail(**run.model_dump())
    return format_response({"run": detail})


@router.get("/{run_id}/trades", response_model=APIResponse)
def get_backtest_trades(run_id: int, session: Session = Depends(get_db_session)) -> APIResponse:
    run = session.get(BacktestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    trades = session.exec(
        select(BacktestTrade).where(BacktestTrade.backtest_run_id == run_id).order_by(BacktestTrade.entry_time)
    ).all()

    trade_reads = [BacktestTradeRead(**trade.model_dump()) for trade in trades]
    return format_response({"trades": trade_reads, "count": len(trade_reads)})


@router.post("/run", response_model=APIResponse)
def run_backtest(request: BacktestRunRequest) -> APIResponse:
    engine = _create_engine(initial_capital=request.initial_capital)
    run_record, summary, _ = engine.run_backtest(
        strategy_name=request.strategy_name,
        params=request.params,
        symbols=request.symbols,
        start_date=request.start_date,
        end_date=request.end_date,
        interval=request.interval,
        notes=request.notes,
    )

    return format_response(
        {
            "run_id": run_record.id,
            "strategy": run_record.strategy_name,
            "roi": summary.roi,
            "total_pnl": summary.total_pnl,
            "win_rate": summary.win_rate,
        },
        message="Backtest executed successfully",
    )


@router.post("/grid-search", response_model=APIResponse)
def grid_search(
    request: GridSearchRequest,
    background_tasks: BackgroundTasks,
) -> APIResponse:
    for key, values in request.param_grid.items():
        if not isinstance(values, list) or not values:
            raise HTTPException(status_code=400, detail=f"Param '{key}' must be a non-empty list")

    # We run grid search asynchronously to return immediately
    def run_grid() -> None:
        logger = structlog.get_logger("grid_search")
        settings = get_settings()
        param_keys = list(request.param_grid.keys())
        param_values = [request.param_grid[key] for key in param_keys]

        simulation_config = SimulationConfig(
            commission_per_trade=settings.simulation_commission,
            slippage_per_share=settings.simulation_slippage,
        )

        engine = BacktestEngine(
            get_session,
            initial_capital=settings.initial_capital,
            simulation_config=simulation_config,
        )

        for combo in product(*param_values):
            params = dict(zip(param_keys, combo))
            try:
                engine.run_backtest(
                    strategy_name=request.strategy_name,
                    params=params,
                    symbols=request.symbols,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    interval=request.interval,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Grid search run failed", params=params, error=str(exc))

    background_tasks.add_task(run_grid)

    combination_count = 1
    for values in request.param_grid.values():
        combination_count *= len(values)

    return format_response(
        {
            "status": "scheduled",
            "strategy": request.strategy_name,
            "combinations": combination_count,
        },
        message="Grid search scheduled",
    )


@router.get("/analytics/summary", response_model=APIResponse)
def analytics_summary(session: Session = Depends(get_db_session)) -> APIResponse:
    total_runs_row = session.exec(select(func.count(BacktestRun.id))).one()
    total_runs = int(total_runs_row) if isinstance(total_runs_row, (int, float)) else int(total_runs_row[0])
    if total_runs == 0:
        return format_response(
            {
                "summary": AnalyticsSummary(
                    total_runs=0,
                    total_trades=0,
                    avg_roi=0.0,
                    best_roi=0.0,
                    worst_roi=0.0,
                    best_strategy=None,
                    best_symbols=None,
                    cumulative_pnl=0.0,
                )
            }
        )

    totals_row = session.exec(
        select(
            func.sum(BacktestRun.total_trades),
            func.avg(BacktestRun.roi),
            func.max(BacktestRun.roi),
            func.min(BacktestRun.roi),
            func.sum(BacktestRun.total_pnl),
        )
    ).one()

    totals = (
        float(totals_row[0] or 0),
        float(totals_row[1] or 0),
        float(totals_row[2] or 0),
        float(totals_row[3] or 0),
        float(totals_row[4] or 0),
    )

    best_run = session.exec(
        select(BacktestRun).order_by(BacktestRun.roi.desc()).limit(1)
    ).one()

    summary = AnalyticsSummary(
        total_runs=total_runs,
        total_trades=int(totals[0]),
        avg_roi=totals[1],
        best_roi=totals[2],
        worst_roi=totals[3],
        best_strategy=best_run.strategy_name,
        best_symbols=best_run.symbols,
        cumulative_pnl=totals[4],
    )

    return format_response({"summary": summary})
