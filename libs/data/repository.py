"""
Market Data Repository - unified interface for historical data

Intelligent source selection:
1. Check cache first
2. Try yfinance (free, no rate limit for daily data)
3. Try Alpha Vantage (25 req/day limit)
4. Try IBKR (if connected)

Stores data in:
- File cache (JSON) for fast retrieval
- DuckDB for analytical queries (optional)
- Parquet for long-term storage (optional)
"""

import os
from datetime import date, datetime, timedelta
from typing import Optional
import structlog

from libs.data.models import NormalizedBar, DataSource
from libs.data.cache_service import MarketDataCache
from libs.data.normalizer import DataNormalizer
from libs.data.ingestors import YFinanceIngestor, AlphaVantageIngestor, IBKRIngestor

logger = structlog.get_logger(__name__)


class MarketDataRepository:
    """
    Central repository for market data with intelligent source fallback.
    
    Pattern from lotto-predictor: cache-first, then try sources in priority order
    """
    
    def __init__(
        self,
        cache_dir: str = "data/cache",
        cache_expiration_days: int = 2,
        preferred_source: Optional[DataSource] = None
    ):
        """
        Initialize repository.
        
        Args:
            cache_dir: Directory for cache files
            cache_expiration_days: Days before cache expires
            preferred_source: Preferred data source (if None, auto-select)
        """
        self.cache = MarketDataCache(cache_dir, cache_expiration_days)
        self.normalizer = DataNormalizer()
        self.preferred_source = preferred_source
        
        # Initialize ingestors
        self.yfinance = YFinanceIngestor()
        self.alphavantage = AlphaVantageIngestor(
            api_key=os.getenv("ALPHA_VANTAGE_API_KEY", "")
        )
        self.ibkr = IBKRIngestor()
        
        logger.info(
            "MarketDataRepository initialized",
            cache_dir=cache_dir,
            preferred_source=preferred_source
        )
    
    def get_historical_bars(
        self,
        symbol: str,
        start: date | str,
        end: date | str,
        interval: str = "1d",
        source: Optional[DataSource] = None,
        force_refresh: bool = False
    ) -> list[NormalizedBar]:
        """
        Get historical price bars with intelligent source fallback.
        
        Args:
            symbol: Ticker symbol
            start: Start date (date object or ISO string)
            end: End date (date object or ISO string)
            interval: Time interval (1d, 1h, 5m, etc.)
            source: Force specific source (bypasses auto-selection)
            force_refresh: Skip cache, fetch fresh data
            
        Returns:
            List of NormalizedBar objects
        """
        # Normalize dates to ISO strings
        start_str = start.isoformat() if isinstance(start, date) else start
        end_str = end.isoformat() if isinstance(end, date) else end
        
        # 1. Check cache first (unless force_refresh)
        if not force_refresh:
            cached = self.cache.get(symbol, start_str, end_str, interval)
            if cached:
                logger.info(
                    "Serving from cache",
                    symbol=symbol,
                    bars_count=len(cached),
                    source="cache"
                )
                filtered = self.normalizer.normalize_dict(cached, symbol, interval, source="cache")
                return self._filter_date_range(filtered, start_str, end_str)
        
        # 2. Fetch from source
        bars = self._fetch_from_source(symbol, start_str, end_str, interval, source)
        
        # 3. Cache the results
        if bars:
            filtered_bars = self._filter_date_range(bars, start_str, end_str)
            self.cache.set(
                symbol,
                start_str,
                end_str,
                interval,
                [bar.to_dict() for bar in filtered_bars]
            )
        
        return self._filter_date_range(bars, start_str, end_str)
    
    def _fetch_from_source(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str,
        source: Optional[DataSource] = None
    ) -> list[NormalizedBar]:
        """
        Fetch data from specified source or try all sources in order.
        
        Priority order:
        1. yfinance (free, reliable for stocks)
        2. Alpha Vantage (free, 25 req/day)
        3. IBKR (requires connection)
        
        Args:
            symbol: Ticker symbol
            start: Start date (ISO string)
            end: End date (ISO string)
            interval: Time interval
            source: Force specific source
            
        Returns:
            List of NormalizedBar objects
        """
        # If source specified, use only that source
        if source:
            return self._try_source(source, symbol, start, end, interval)
        
        # Try sources in priority order
        sources_to_try: list[DataSource] = []
        
        if self.preferred_source:
            sources_to_try.append(self.preferred_source)
        
        # Add remaining sources in default order
        for src in ["yfinance", "alphavantage", "ibkr"]:
            if src not in sources_to_try:
                sources_to_try.append(src)  # type: ignore
        
        for src in sources_to_try:
            bars = self._try_source(src, symbol, start, end, interval)
            if bars:
                logger.info(
                    "Successfully fetched data",
                    symbol=symbol,
                    source=src,
                    bars_count=len(bars)
                )
                return bars
        
        logger.error(
            "Failed to fetch data from all sources",
            symbol=symbol,
            start=start,
            end=end,
            interval=interval
        )
        return []
    
    def _try_source(
        self,
        source: DataSource,
        symbol: str,
        start: str,
        end: str,
        interval: str
    ) -> list[NormalizedBar]:
        """
        Try fetching from a specific source.
        
        Args:
            source: Data source to try
            symbol: Ticker symbol
            start: Start date (ISO string)
            end: End date (ISO string)
            interval: Time interval
            
        Returns:
            List of NormalizedBar objects (empty if failed)
        """
        try:
            if source == "yfinance":
                data = self.yfinance.fetch(symbol, start, end, interval)
                return self.normalizer.normalize_yfinance(data, symbol, interval)
            
            elif source == "alphavantage":
                data = self.alphavantage.fetch(symbol, start, end, interval)
                return self.normalizer.normalize_alphavantage(data, symbol, interval)
            
            elif source == "ibkr":
                data = self.ibkr.fetch(symbol, start, end, interval)
                return self.normalizer.normalize_ibkr(data, symbol, interval)
            
            else:
                logger.warning(f"Unknown source: {source}")
                return []
                
        except Exception as e:
            logger.warning(
                f"Failed to fetch from {source}",
                symbol=symbol,
                error=str(e),
                source=source
            )
            return []

    def _filter_date_range(
        self,
        bars: list[NormalizedBar],
        start: str,
        end: str,
    ) -> list[NormalizedBar]:
        """Filter bars so only records within [start, end] are returned."""

        if not bars:
            return []

        start_dt = self._parse_iso_datetime(start, default_hour=0)
        end_dt = self._parse_iso_datetime(end, default_hour=23, default_minute=59, default_second=59)

        filtered = [bar for bar in bars if start_dt <= bar.timestamp <= end_dt]

        if len(filtered) != len(bars):
            logger.debug(
                "Filtered bars by date range",
                original=len(bars),
                filtered=len(filtered),
                start=start,
                end=end,
            )

        return filtered

    @staticmethod
    def _parse_iso_datetime(
        value: str,
        *,
        default_hour: int = 0,
        default_minute: int = 0,
        default_second: int = 0,
    ) -> datetime:
        """Parse date/date-time strings into datetime with safe defaults."""

        try:
            if "T" in value:
                return datetime.fromisoformat(value)
            return datetime.fromisoformat(value + f"T{default_hour:02d}:{default_minute:02d}:{default_second:02d}")
        except ValueError:
            return datetime.utcnow()
    
    def pre_cache_symbol(
        self,
        symbol: str,
        days_back: int = 365,
        interval: str = "1d",
        source: Optional[DataSource] = None
    ) -> int:
        """
        Pre-cache historical data for a symbol (useful before backtesting).
        
        Args:
            symbol: Ticker symbol
            days_back: Number of days to fetch
            interval: Time interval
            source: Force specific source
            
        Returns:
            Number of bars cached
        """
        end = date.today()
        start = end - timedelta(days=days_back)
        
        logger.info(
            "Pre-caching symbol",
            symbol=symbol,
            start=start.isoformat(),
            end=end.isoformat(),
            interval=interval
        )
        
        bars = self.get_historical_bars(
            symbol,
            start,
            end,
            interval,
            source=source,
            force_refresh=True  # Force fresh fetch
        )
        
        logger.info(f"Pre-cached {len(bars)} bars for {symbol}")
        return len(bars)
    
    def pre_cache_symbols(
        self,
        symbols: list[str],
        days_back: int = 365,
        interval: str = "1d",
        source: Optional[DataSource] = None
    ) -> dict[str, int]:
        """
        Pre-cache multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            days_back: Number of days to fetch
            interval: Time interval
            source: Force specific source
            
        Returns:
            Dict mapping symbol → bars count
        """
        results = {}
        
        for symbol in symbols:
            try:
                count = self.pre_cache_symbol(symbol, days_back, interval, source)
                results[symbol] = count
            except Exception as e:
                logger.error(f"Failed to pre-cache {symbol}", error=str(e))
                results[symbol] = 0
        
        total_bars = sum(results.values())
        logger.info(
            "Pre-caching complete",
            symbols_count=len(symbols),
            total_bars=total_bars,
            results=results
        )
        
        return results
    
    def get_latest_bar(
        self,
        symbol: str,
        interval: str = "1d",
        source: Optional[DataSource] = None
    ) -> Optional[NormalizedBar]:
        """
        Get the most recent bar for a symbol.
        
        Args:
            symbol: Ticker symbol
            interval: Time interval
            source: Force specific source
            
        Returns:
            Latest NormalizedBar or None
        """
        end = date.today()
        start = end - timedelta(days=7)  # Last week
        
        bars = self.get_historical_bars(symbol, start, end, interval, source)
        return bars[-1] if bars else None
    
    def clear_cache(self, symbol: Optional[str] = None) -> int:
        """
        Clear cached data.
        
        Args:
            symbol: If provided, only clear this symbol. Otherwise clear all.
            
        Returns:
            Number of cache files deleted
        """
        return self.cache.clear(symbol)

