"""CLI to run a single backtest"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

import structlog

from apps.backtesting.config import get_settings
from apps.backtesting.db import get_session
from apps.backtesting.engine import BacktestEngine, SimulationConfig

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a backtest")
    parser.add_argument("--strategy", required=True, help="Strategy version to run")
    parser.add_argument("--symbols", required=True, help="Comma-separated list of symbols")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--params", help="JSON string of strategy parameters", default="{}")
    parser.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
    parser.add_argument("--initial-capital", type=float, help="Initial capital override")
    parser.add_argument(
        "--show-trades",
        action="store_true",
        help="Print trade-by-trade details after summary",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    params = json.loads(args.params)

    session_factory = get_session
    simulation_config = SimulationConfig(
        commission_per_trade=settings.simulation_commission,
        slippage_per_share=settings.simulation_slippage,
    )

    engine = BacktestEngine(
        session_factory,
        initial_capital=args.initial_capital or settings.initial_capital,
        simulation_config=simulation_config,
    )

    run_record, summary, trades = engine.run_backtest(
        strategy_name=args.strategy,
        params=params,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=args.interval,
    )

    initial_capital = args.initial_capital or settings.initial_capital
    logger.info(
        "Backtest finished",
        run_id=run_record.id,
        trades=summary.total_trades,
        roi=summary.roi,
        pnl=summary.total_pnl,
    )

    print("\n=== Backtest Summary ===")
    print(f"Run ID:       {run_record.id}")
    print(f"Strategy:     {run_record.strategy_name} ({run_record.strategy_version})")
    print(f"Symbols:      {', '.join(run_record.symbols)}")
    print(f"Period:       {run_record.start_date} → {run_record.end_date}")
    print(f"Initial Cap:  ${initial_capital:,.2f}")
    print(f"Final Cap:    ${summary.final_capital:,.2f}")
    print(f"Trades:       {summary.total_trades}")
    print(f"Win Rate:     {summary.win_rate:.2f}%")
    print(f"ROI:          {summary.roi:.2f}%")
    print(f"Total PnL:    {summary.total_pnl:.2f}")
    print(f"Sharpe Ratio: {summary.sharpe_ratio:.2f}" if summary.sharpe_ratio else "Sharpe Ratio: n/a")
    print(f"Max Drawdown: {summary.max_drawdown:.2f}%")
    print("========================\n")

    if args.show_trades and trades:
        print("Top Trades (chronological):")
        for trade in sorted(trades, key=lambda t: (t.entry_time, t.symbol)):
            print(
                f"{trade.entry_time.date()} {trade.symbol:<6} qty={trade.qty:.2f} "
                f"entry=${trade.entry_price:.2f} exit=${trade.exit_price:.2f} "
                f"pnl=${trade.pnl:.2f} ({trade.pnl_percent:.2f}%) reason={trade.exit_reason}"
            )
        print("================================\n")


if __name__ == "__main__":
    main()
