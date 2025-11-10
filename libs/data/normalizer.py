"""
Data normalizer - converts different data sources to NormalizedBar format

Handles:
- yfinance DataFrames
- Alpha Vantage JSON responses
- IBKR BarData objects
- Dictionary formats
"""

from datetime import datetime
from typing import Any
import pandas as pd
import structlog

from libs.data.models import NormalizedBar, DataSource

logger = structlog.get_logger(__name__)


class DataNormalizer:
    """
    Normalize market data from multiple sources to NormalizedBar format.
    
    Pattern: Strategy pattern for different data source formats
    """
    
    @staticmethod
    def normalize_yfinance(
        df: pd.DataFrame,
        symbol: str,
        interval: str = "1d"
    ) -> list[NormalizedBar]:
        """
        Normalize yfinance DataFrame to NormalizedBar list.
        
        yfinance format:
                         Open    High     Low   Close    Volume
        Date                                                    
        2023-01-01   100.0   105.0    98.0   103.0   1000000
        
        Args:
            df: yfinance DataFrame with OHLCV columns
            symbol: Ticker symbol
            interval: Time interval
            
        Returns:
            List of NormalizedBar objects
        """
        bars = []
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # yfinance column names can be 'Open' or 'open', handle both
        df.columns = [col.capitalize() for col in df.columns]
        
        for _, row in df.iterrows():
            try:
                # Handle different date column names
                timestamp = row.get("Date") or row.get("Datetime")
                if pd.isna(timestamp):
                    continue
                
                # Convert to datetime if needed
                if not isinstance(timestamp, datetime):
                    timestamp = pd.to_datetime(timestamp).to_pydatetime()
                
                bar = NormalizedBar(
                    timestamp=timestamp,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row.get("Volume", 0)),
                    symbol=symbol,
                    source="yfinance",
                    interval=interval
                )
                bars.append(bar)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(
                    "Failed to normalize yfinance row",
                    error=str(e),
                    symbol=symbol,
                    row=row.to_dict()
                )
                continue
        
        logger.debug(f"Normalized {len(bars)} bars from yfinance", symbol=symbol)
        return bars
    
    @staticmethod
    def normalize_alphavantage(
        data: dict,
        symbol: str,
        interval: str = "1d"
    ) -> list[NormalizedBar]:
        """
        Normalize Alpha Vantage JSON to NormalizedBar list.
        
        Alpha Vantage format:
        {
            "Time Series (Daily)": {
                "2023-01-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "98.0",
                    "4. close": "103.0",
                    "5. volume": "1000000"
                }
            }
        }
        
        Args:
            data: Alpha Vantage JSON response
            symbol: Ticker symbol
            interval: Time interval
            
        Returns:
            List of NormalizedBar objects
        """
        bars = []
        
        # Find the time series key (varies by interval)
        time_series_key = None
        for key in data.keys():
            if key.startswith("Time Series"):
                time_series_key = key
                break
        
        if not time_series_key:
            logger.error("No time series found in Alpha Vantage response", symbol=symbol)
            return bars
        
        time_series = data[time_series_key]
        
        for date_str, values in time_series.items():
            try:
                timestamp = datetime.fromisoformat(date_str.replace(" ", "T"))
                
                bar = NormalizedBar(
                    timestamp=timestamp,
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    volume=int(values.get("5. volume", 0)),
                    symbol=symbol,
                    source="alphavantage",
                    interval=interval
                )
                bars.append(bar)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(
                    "Failed to normalize Alpha Vantage entry",
                    error=str(e),
                    symbol=symbol,
                    date=date_str
                )
                continue
        
        # Sort by timestamp (Alpha Vantage returns newest first)
        bars.sort(key=lambda b: b.timestamp)
        
        logger.debug(f"Normalized {len(bars)} bars from Alpha Vantage", symbol=symbol)
        return bars
    
    @staticmethod
    def normalize_ibkr(
        bars_data: list,
        symbol: str,
        interval: str = "1d"
    ) -> list[NormalizedBar]:
        """
        Normalize IBKR BarData objects to NormalizedBar list.
        
        IBKR BarData format:
        BarData(date=datetime(...), open=100.0, high=105.0, low=98.0, close=103.0, volume=1000000)
        
        Args:
            bars_data: List of IBKR BarData objects
            symbol: Ticker symbol
            interval: Time interval
            
        Returns:
            List of NormalizedBar objects
        """
        bars = []
        
        for bar_data in bars_data:
            try:
                bar = NormalizedBar(
                    timestamp=bar_data.date if isinstance(bar_data.date, datetime) else datetime.fromisoformat(str(bar_data.date)),
                    open=float(bar_data.open),
                    high=float(bar_data.high),
                    low=float(bar_data.low),
                    close=float(bar_data.close),
                    volume=int(bar_data.volume),
                    symbol=symbol,
                    source="ibkr",
                    interval=interval
                )
                bars.append(bar)
            except (AttributeError, ValueError, TypeError) as e:
                logger.warning(
                    "Failed to normalize IBKR bar",
                    error=str(e),
                    symbol=symbol
                )
                continue
        
        logger.debug(f"Normalized {len(bars)} bars from IBKR", symbol=symbol)
        return bars
    
    @staticmethod
    def normalize_dict(
        data_list: list[dict],
        symbol: str,
        interval: str = "1d",
        source: DataSource = "cache"
    ) -> list[NormalizedBar]:
        """
        Normalize list of dictionaries to NormalizedBar list.
        
        Used for:
        - Cache deserialization
        - Manual data input
        - Testing
        
        Args:
            data_list: List of dicts with OHLCV data
            symbol: Ticker symbol
            interval: Time interval
            source: Data source identifier
            
        Returns:
            List of NormalizedBar objects
        """
        bars = []
        
        for data in data_list:
            try:
                bar = NormalizedBar.from_dict(data) if "source" in data else NormalizedBar(
                    timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"],
                    open=float(data["open"]),
                    high=float(data["high"]),
                    low=float(data["low"]),
                    close=float(data["close"]),
                    volume=int(data["volume"]),
                    symbol=data.get("symbol", symbol),
                    source=data.get("source", source),
                    interval=data.get("interval", interval)
                )
                bars.append(bar)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(
                    "Failed to normalize dict",
                    error=str(e),
                    symbol=symbol,
                    data=data
                )
                continue
        
        logger.debug(f"Normalized {len(bars)} bars from dict", symbol=symbol)
        return bars
    
    @classmethod
    def auto_normalize(
        cls,
        data: Any,
        symbol: str,
        interval: str = "1d"
    ) -> list[NormalizedBar]:
        """
        Automatically detect data format and normalize.
        
        Args:
            data: Data in any supported format
            symbol: Ticker symbol
            interval: Time interval
            
        Returns:
            List of NormalizedBar objects
        """
        # DataFrame (yfinance)
        if isinstance(data, pd.DataFrame):
            return cls.normalize_yfinance(data, symbol, interval)
        
        # Dict (Alpha Vantage)
        elif isinstance(data, dict) and any(k.startswith("Time Series") for k in data.keys()):
            return cls.normalize_alphavantage(data, symbol, interval)
        
        # List of dicts
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            return cls.normalize_dict(data, symbol, interval)
        
        # List of IBKR BarData objects
        elif isinstance(data, list) and data and hasattr(data[0], "date") and hasattr(data[0], "open"):
            return cls.normalize_ibkr(data, symbol, interval)
        
        else:
            logger.error(
                "Unknown data format for normalization",
                data_type=type(data).__name__,
                symbol=symbol
            )
            return []

