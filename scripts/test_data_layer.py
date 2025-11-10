#!/usr/bin/env python3
"""
Quick test of the data layer

Tests:
1. Cache service
2. Data normalizer
3. Market data repository
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from datetime import date, timedelta
import structlog

from libs.data import MarketDataRepository

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger(__name__)


def test_repository():
    """Test market data repository"""
    logger.info("Testing MarketDataRepository")
    
    # Initialize
    repo = MarketDataRepository(cache_dir="data/cache_test")
    
    # Test 1: Fetch data (should use yfinance)
    end = date.today()
    start = end - timedelta(days=30)
    
    logger.info("Fetching AAPL data (30 days)")
    bars = repo.get_historical_bars("AAPL", start, end, interval="1d")
    
    if bars:
        logger.info(f"✅ Fetched {len(bars)} bars for AAPL")
        logger.info(f"   First bar: {bars[0].timestamp} | Close: ${bars[0].close}")
        logger.info(f"   Last bar:  {bars[-1].timestamp} | Close: ${bars[-1].close}")
    else:
        logger.error("❌ Failed to fetch data")
        return False
    
    # Test 2: Cache hit (should be instant)
    logger.info("Fetching again (should hit cache)")
    bars2 = repo.get_historical_bars("AAPL", start, end, interval="1d")
    
    if len(bars2) == len(bars):
        logger.info("✅ Cache working")
    else:
        logger.error("❌ Cache miss")
        return False
    
    # Test 3: Latest bar
    logger.info("Fetching latest bar")
    latest = repo.get_latest_bar("AAPL")
    
    if latest:
        logger.info(f"✅ Latest: {latest.timestamp} | Close: ${latest.close}")
    else:
        logger.error("❌ Failed to get latest")
        return False
    
    # Test 4: Pre-cache multiple symbols
    logger.info("Pre-caching SPY and QQQ")
    results = repo.pre_cache_symbols(["SPY", "QQQ"], days_back=7)
    
    if all(results.values()):
        logger.info(f"✅ Pre-cached: {results}")
    else:
        logger.error(f"❌ Pre-cache failed: {results}")
        return False
    
    logger.info("🎉 All tests passed!")
    return True


if __name__ == "__main__":
    success = test_repository()
    sys.exit(0 if success else 1)

