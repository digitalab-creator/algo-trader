#!/usr/bin/env python3
"""
Pre-cache market data for backtesting

Usage:
    python scripts/cache_symbols.py --symbols AAPL,MSFT,TSLA --days 365
    python scripts/cache_symbols.py --config configs/symbols/us_stocks.yaml --group default
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

import argparse
import yaml
from datetime import date, timedelta
import structlog

from libs.data.repository import MarketDataRepository

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger(__name__)


def load_symbols_from_config(config_path: str, group: str = "default") -> list[str]:
    """Load symbol list from YAML config"""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    if group not in config:
        available = list(config.keys())
        raise ValueError(f"Group '{group}' not found in {config_path}. Available: {available}")
    
    return config[group]


def main():
    parser = argparse.ArgumentParser(description="Pre-cache market data for backtesting")
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated list of symbols (e.g., AAPL,MSFT,TSLA)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to symbol config YAML file"
    )
    parser.add_argument(
        "--group",
        type=str,
        default="default",
        help="Symbol group from config file (default: 'default')"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days to cache (default: 365)"
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        help="Data interval (default: 1d)"
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["yfinance", "alphavantage", "ibkr"],
        help="Force specific data source"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/cache",
        help="Cache directory (default: data/cache)"
    )
    
    args = parser.parse_args()
    
    # Get symbol list
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    elif args.config:
        symbols = load_symbols_from_config(args.config, args.group)
    else:
        logger.error("Must provide either --symbols or --config")
        sys.exit(1)
    
    logger.info(
        "Starting symbol pre-caching",
        symbols_count=len(symbols),
        days=args.days,
        interval=args.interval,
        source=args.source or "auto"
    )
    
    # Initialize repository
    repo = MarketDataRepository(cache_dir=args.cache_dir)
    
    # Pre-cache symbols
    results = repo.pre_cache_symbols(
        symbols=symbols,
        days_back=args.days,
        interval=args.interval,
        source=args.source
    )
    
    # Print summary
    total_bars = sum(results.values())
    successful = sum(1 for count in results.values() if count > 0)
    failed = len(symbols) - successful
    
    logger.info(
        "Pre-caching complete",
        total_symbols=len(symbols),
        successful=successful,
        failed=failed,
        total_bars=total_bars
    )
    
    if failed > 0:
        logger.warning("Failed symbols:", symbols=[s for s, c in results.items() if c == 0])
    
    # Print detailed results
    print("\n📊 Cache Results:")
    print("=" * 60)
    for symbol, count in sorted(results.items()):
        status = "✅" if count > 0 else "❌"
        print(f"{status} {symbol:10s} {count:6d} bars")
    print("=" * 60)
    print(f"Total: {total_bars} bars across {successful}/{len(symbols)} symbols")


if __name__ == "__main__":
    main()

