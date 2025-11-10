"""
Market Data Management Library

Provides unified access to market data from multiple sources:
- IBKR (Interactive Brokers)
- Alpha Vantage
- yfinance

Features:
- Automatic source selection (cache → yfinance → alphavantage → IBKR)
- Data normalization (all sources → NormalizedBar)
- File-based cache with expiration
- DuckDB for analytical queries
- Parquet for long-term storage
"""

from libs.data.models import NormalizedBar, DataSource
from libs.data.cache_service import MarketDataCache
from libs.data.normalizer import DataNormalizer
from libs.data.repository import MarketDataRepository

__all__ = [
    "NormalizedBar",
    "DataSource",
    "MarketDataCache",
    "DataNormalizer",
    "MarketDataRepository",
]

