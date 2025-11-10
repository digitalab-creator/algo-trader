"""yfinance data ingestor"""

from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import structlog

logger = structlog.get_logger(__name__)


class YFinanceIngestor:
    """
    Fetch data from Yahoo Finance via yfinance library.
    
    Pros:
    - Free, no API key needed
    - Good coverage for stocks, ETFs
    - Reliable for daily data
    
    Cons:
    - Rate limited (429 errors possible)
    - Intraday data limited to ~60 days per request
    - No crypto support (use crypto-specific symbols like BTC-USD)
    """
    
    _INTRADAY_INTERVALS: set[str] = {
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
    }

    def fetch(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data from yfinance.
        
        Args:
            symbol: Ticker symbol
            start: Start date (ISO format)
            end: End date (ISO format)
            interval: Time interval (1d, 1h, 5m, etc.)
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            Exception: If fetch fails
        """
        logger.debug(
            "Fetching from yfinance",
            symbol=symbol,
            start=start,
            end=end,
            interval=interval,
        )
        
        try:
            if interval in self._INTRADAY_INTERVALS:
                df = self._fetch_intraday(symbol, start, end, interval)
            else:
                df = yf.download(
                    symbol,
                    start=start,
                    end=end,
                    interval=interval,
                    progress=False,
                    threads=False,
                )
            
            if df.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            logger.info(
                "yfinance fetch successful",
                symbol=symbol,
                bars_count=len(df)
            )
            
            return df
            
        except Exception as e:
            logger.error(
                "yfinance fetch failed",
                symbol=symbol,
                error=str(e)
            )
            raise

    def _fetch_intraday(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str,
    ) -> pd.DataFrame:
        """Fetch intraday data in 60-day chunks (yfinance limitation)."""

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        # Yahoo rejects ranges > 60 days for intraday intervals
        max_span = timedelta(days=59)
        frames: list[pd.DataFrame] = []

        current_start = start_dt
        while current_start <= end_dt:
            current_end = min(current_start + max_span, end_dt)

            # yfinance treats end as exclusive, so add one extra day to include the final boundary
            fetch_end = current_end + timedelta(days=1)

            logger.debug(
                "Fetching intraday chunk", symbol=symbol, start=current_start, end=current_end
            )

            chunk = yf.download(
                symbol,
                start=current_start,
                end=fetch_end,
                interval=interval,
                progress=False,
                threads=False,
            )

            if not chunk.empty:
                frames.append(chunk)

            current_start = current_end + timedelta(days=1)

        if not frames:
            raise ValueError(f"No intraday data returned for {symbol}")

        df = pd.concat(frames).sort_index()
        df = df[~ df.index.duplicated(keep="first")]
        return df

