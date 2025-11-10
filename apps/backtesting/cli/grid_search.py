"""CLI to run grid search for backtesting strategies"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Dict, List

import structlog
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

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


def load_grid_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_param_grid(param_grid: Dict[str, List]) -> List[Dict]:
    keys = list(param_grid.keys())
    values = [param_grid[key] for key in keys]
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run grid search backtests")
    parser.add_argument("config", type=Path, help="Path to grid search YAML config")
    parser.add_argument("--max-workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--initial-capital", type=float, help="Initial capital override")
    return parser.parse_args()


def run_single_backtest(engine_factory, strategy: str, params: Dict, symbols: List[str], start: date, end: date, interval: str):
    engine = engine_factory()
    run_record, summary, _ = engine.run_backtest(
        strategy_name=strategy,
        params=params,
        symbols=symbols,
        start_date=start,
        end_date=end,
        interval=interval,
    )
    return run_record, summary


def main() -> None:
    args = parse_args()
    settings = get_settings()
    config = load_grid_config(args.config)

    strategy = config["strategy"]
    symbols = config.get("symbols", [])
    if not symbols:
        raise ValueError("Grid config must include 'symbols' list")

    date_range = config.get("date_range")
    if not date_range:
        raise ValueError("Grid config must include 'date_range' with start/end")

    start_date = date.fromisoformat(date_range["start"])
    end_date = date.fromisoformat(date_range["end"])
    interval = config.get("interval", "1d")

    param_grid = config.get("param_grid")
    if not param_grid:
        raise ValueError("Grid config must include 'param_grid'")

    param_combinations = generate_param_grid(param_grid)
    logger.info(
        "Starting grid search",
        strategy=strategy,
        combos=len(param_combinations),
        symbols=symbols,
    )

    simulation_config = SimulationConfig(
        commission_per_trade=settings.simulation_commission,
        slippage_per_share=settings.simulation_slippage,
    )

    def engine_factory() -> BacktestEngine:
        return BacktestEngine(
            get_session,
            initial_capital=args.initial_capital or settings.initial_capital,
            simulation_config=simulation_config,
        )

    results = []

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_params = {
            executor.submit(
                run_single_backtest,
                engine_factory,
                strategy,
                params,
                symbols,
                start_date,
                end_date,
                interval,
            ): params
            for params in param_combinations
        }

        for future in as_completed(future_to_params):
            params = future_to_params[future]
            try:
                run_record, summary = future.result()
                logger.info(
                    "Backtest completed",
                    params=params,
                    roi=summary.roi,
                    pnl=summary.total_pnl,
                    win_rate=summary.win_rate,
                )
                results.append(
                    {
                        "run_id": run_record.id,
                        "params": params,
                        "roi": summary.roi,
                        "total_pnl": summary.total_pnl,
                        "win_rate": summary.win_rate,
                        "strategy": strategy,
                        "symbols": symbols,
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    }
                )
            except Exception as exc:
                logger.error("Backtest failed", params=params, error=str(exc))

    results.sort(key=lambda r: r["roi"], reverse=True)

    output_path = args.config.with_suffix(".results.json")
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    if results:
        best = results[0]
        print("\n=== Grid Search Complete ===")
        print(f"Best ROI:   {best['roi']:.2f}%")
        print(f"Total PnL:  {best['total_pnl']:.2f}")
        print(f"Win Rate:   {best['win_rate']:.2f}%")
        print(f"Params:     {best['params']}")
        print(f"Run ID:     {best['run_id']}")
        print(f"Results saved to {output_path}")
    else:
        print("No successful backtests were completed.")


if __name__ == "__main__":
    main()
