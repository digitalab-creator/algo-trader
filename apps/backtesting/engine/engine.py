"""Backtesting engine orchestrator"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date
from typing import Callable, Dict, List, Optional

import structlog
from sqlmodel import Session

from libs.data import MarketDataRepository
from libs.strategies.base import strategy_registry
from libs.strategies.base import BaseBacktestStrategy
from libs.strategies.base import TradeSignal

from apps.backtesting.engine.executor import SimulationConfig, simulate_trade
from apps.backtesting.engine.metrics import calculate_metrics
from apps.backtesting.engine.portfolio import Portfolio
from apps.backtesting.engine.types import SimulatedTrade, BacktestSummary
from apps.backtesting.models import BacktestRun, BacktestTrade
from apps.backtesting.strategies.utils import bars_to_dataframe


logger = structlog.get_logger(__name__)


class BacktestEngine:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        data_repository: Optional[MarketDataRepository] = None,
        initial_capital: float = 100_000.0,
        simulation_config: Optional[SimulationConfig] = None,
    ) -> None:
        self.session_factory = session_factory
        self.repo = data_repository or MarketDataRepository()
        self.initial_capital = initial_capital
        self.simulation_config = simulation_config or SimulationConfig()

    def _fetch_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: str,
    ) -> Dict[str, list]:
        data: Dict[str, list] = {}
        for symbol in symbols:
            bars = self.repo.get_historical_bars(symbol, start_date, end_date, interval)
            if not bars:
                logger.warning("No data fetched for symbol", symbol=symbol)
                continue
            data[symbol] = bars
        return data

    def _instantiate_strategy(self, strategy_name: str) -> BaseBacktestStrategy:
        return strategy_registry.get(strategy_name)

    def _generate_signals(
        self,
        strategy: BaseBacktestStrategy,
        data: Dict[str, list],
        params: dict,
    ) -> List[TradeSignal]:
        signals: List[TradeSignal] = []
        for symbol, bars in data.items():
            symbol_signals = strategy.generate_signals(symbol, bars, params=params)
            signals.extend(symbol_signals)
        signals.sort(key=lambda s: (s.timestamp, s.symbol))
        return signals

    def run_backtest(
        self,
        *,
        strategy_name: str,
        params: Dict,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: str = "1d",
        data_source: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> tuple[BacktestRun, BacktestSummary, List[SimulatedTrade]]:
        t_start = time.perf_counter()
        strategy = self._instantiate_strategy(strategy_name)

        logger.info(
            "Starting backtest",
            strategy=strategy.version,
            symbols=symbols,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )

        raw_data = self._fetch_data(symbols, start_date, end_date, interval)
        if not raw_data:
            raise ValueError("No market data available for requested symbols")

        dataframes = {symbol: bars_to_dataframe(bars) for symbol, bars in raw_data.items()}
        signals = self._generate_signals(strategy, raw_data, params)

        if not signals:
            logger.warning("No signals generated", strategy=strategy.version)

        portfolio = Portfolio(self.initial_capital)
        simulated_trades: List[SimulatedTrade] = []

        for signal in signals:
            df = dataframes.get(signal.symbol)
            if df is None or df.empty:
                logger.warning("No price data for signal", symbol=signal.symbol)
                continue

            trade = simulate_trade(
                signal,
                df,
                current_equity=portfolio.current_equity,
                config=self.simulation_config,
            )

            if trade is None:
                logger.debug("Signal skipped", symbol=signal.symbol, timestamp=signal.timestamp)
                continue

            portfolio.apply_pnl(trade.exit_time, trade.pnl)
            simulated_trades.append(trade)

        t_end = time.perf_counter()
        summary = calculate_metrics(
            simulated_trades,
            initial_capital=self.initial_capital,
            final_capital=portfolio.current_equity,
            equity_curve=portfolio.equity_curve,
            execution_time_seconds=t_end - t_start,
        )

        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()

        run_record = BacktestRun(
            strategy_name=strategy_name,
            strategy_version=strategy.version,
            params_hash=params_hash,
            params_json=params,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            total_trades=summary.total_trades,
            winning_trades=summary.winning_trades,
            losing_trades=summary.losing_trades,
            initial_capital=self.initial_capital,
            final_capital=summary.final_capital,
            total_pnl=summary.total_pnl,
            roi=summary.roi,
            sharpe_ratio=summary.sharpe_ratio,
            max_drawdown=summary.max_drawdown,
            max_drawdown_duration=summary.max_drawdown_duration,
            win_rate=summary.win_rate,
            avg_win=summary.avg_win,
            avg_loss=summary.avg_loss,
            profit_factor=summary.profit_factor,
            execution_time_seconds=summary.execution_time_seconds,
            data_source=data_source or (self.repo.preferred_source or "auto"),
            notes=notes,
        )

        with self.session_factory() as session:
            session.add(run_record)
            session.flush()

            trade_records = [
                BacktestTrade(
                    backtest_run_id=run_record.id,
                    symbol=trade.symbol,
                    entry_time=trade.entry_time,
                    exit_time=trade.exit_time,
                    entry_price=trade.entry_price,
                    exit_price=trade.exit_price,
                    exit_reason=trade.exit_reason,
                    side=trade.side,
                    qty=trade.qty,
                    pnl=trade.pnl,
                    pnl_percent=trade.pnl_percent,
                    duration_seconds=trade.duration_seconds,
                    stop_loss=trade.stop_loss,
                    take_profit=trade.take_profit,
                    risk_amount=trade.risk_amount,
                    risk_percent=trade.risk_percent,
                    commission=trade.commission,
                    slippage=trade.slippage,
                    details=trade.details,
                )
                for trade in simulated_trades
            ]

            session.add_all(trade_records)
            session.commit()
            session.refresh(run_record)
            session.expunge(run_record)

        logger.info(
            "Backtest complete",
            strategy=strategy.version,
            trades=summary.total_trades,
            roi=summary.roi,
            total_pnl=summary.total_pnl,
        )

        return run_record, summary, simulated_trades
