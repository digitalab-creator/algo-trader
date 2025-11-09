"""
Market data fetcher with multiple sources.

Supports:
- IBKR (primary, for live trading)
- yfinance (free, has rate limits)
- Alpha Vantage (free with API key, 25 requests/day)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Literal

import pandas as pd
import polars as pl

DataSource = Literal["ibkr", "yfinance", "alphavantage"]


def get_data_source() -> DataSource:
    """
    Get configured data source from environment.
    
    Returns:
        Data source name (ibkr, yfinance, or alphavantage)
    """
    source = os.getenv("MARKET_DATA_SOURCE", "ibkr").lower()
    if source not in ["ibkr", "yfinance", "alphavantage"]:
        raise ValueError(f"Invalid MARKET_DATA_SOURCE: {source}")
    return source  # type: ignore


def fetch_historical_data(
    symbol: str,
    days: int = 30,
    interval: str = "1d",
    source: DataSource | None = None,
) -> pl.DataFrame:
    """
    Fetch historical market data from configured source.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL")
        days: Number of days of history
        interval: Data interval (1m, 5m, 15m, 1h, 1d)
        source: Override data source (default: from env)
    
    Returns:
        Polars DataFrame with OHLCV data
    
    Example:
        ```python
        df = fetch_historical_data("AAPL", days=30)
        print(df.head())
        ```
    """
    source = source or get_data_source()
    
    if source == "ibkr":
        return _fetch_ibkr(symbol, days, interval)
    elif source == "yfinance":
        return _fetch_yfinance(symbol, days, interval)
    elif source == "alphavantage":
        return _fetch_alphavantage(symbol, days, interval)
    else:
        raise ValueError(f"Unknown source: {source}")


def fetch_current_price(symbol: str, source: DataSource | None = None) -> float:
    """
    Fetch current/latest price for a symbol.
    
    Args:
        symbol: Stock symbol
        source: Override data source
    
    Returns:
        Current price
    """
    source = source or get_data_source()
    
    if source == "ibkr":
        return _fetch_ibkr_price(symbol)
    elif source == "yfinance":
        return _fetch_yfinance_price(symbol)
    elif source == "alphavantage":
        return _fetch_alphavantage_price(symbol)
    else:
        raise ValueError(f"Unknown source: {source}")


# ============================================================================
# IBKR Implementation
# ============================================================================

def _fetch_ibkr(symbol: str, days: int, interval: str) -> pl.DataFrame:
    """Fetch data from Interactive Brokers."""
    from ib_insync import IB, Stock, util
    
    # Map interval to IBKR format
    duration_map = {
        "1m": ("60 S", "1 min"),
        "5m": ("300 S", "5 mins"),
        "15m": ("900 S", "15 mins"),
        "1h": ("3600 S", "1 hour"),
        "1d": (f"{days} D", "1 day"),
    }
    
    if interval not in duration_map:
        raise ValueError(f"Unsupported interval: {interval}")
    
    duration, bar_size = duration_map[interval]
    
    ib = IB()
    try:
        # Connect using env vars
        host = os.getenv("IBKR_HOST", "127.0.0.1")
        port = int(os.getenv("IBKR_PORT", "7497"))
        client_id = int(os.getenv("IBKR_CLIENT_ID", "101"))
        
        ib.connect(host, port, clientId=client_id)
        
        # Create contract
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        
        # Fetch historical bars
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=True,
        )
        
        # Convert to DataFrame
        df = util.df(bars)
        
        # Convert to Polars
        if not df.empty:
            df_pl = pl.from_pandas(df)
            # Rename columns to match standard format
            return df_pl.rename({
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            })
        else:
            return pl.DataFrame()
            
    finally:
        ib.disconnect()


def _fetch_ibkr_price(symbol: str) -> float:
    """Fetch current price from IBKR."""
    from ib_insync import IB, Stock
    
    ib = IB()
    try:
        host = os.getenv("IBKR_HOST", "127.0.0.1")
        port = int(os.getenv("IBKR_PORT", "7497"))
        client_id = int(os.getenv("IBKR_CLIENT_ID", "101"))
        
        ib.connect(host, port, clientId=client_id)
        
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        
        # Request market data
        ticker = ib.reqMktData(contract, "", False, False)
        ib.sleep(1)  # Wait for data
        
        price = ticker.last or ticker.close or ticker.marketPrice()
        
        if price:
            return float(price)
        else:
            raise ValueError(f"No price available for {symbol}")
            
    finally:
        ib.disconnect()


# ============================================================================
# yfinance Implementation (free, has rate limits)
# ============================================================================

def _fetch_yfinance(symbol: str, days: int, interval: str) -> pl.DataFrame:
    """Fetch data from Yahoo Finance."""
    import yfinance as yf
    
    data = yf.download(
        symbol,
        period=f"{days}d",
        interval=interval,
        progress=False,
        auto_adjust=False,
    )
    
    if data.empty:
        return pl.DataFrame()
    
    return pl.from_pandas(data.reset_index())


def _fetch_yfinance_price(symbol: str) -> float:
    """Fetch current price from yfinance."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol)
    data = yf.download(symbol, period="1d", interval="1m", progress=False)
    
    if not data.empty:
        return float(data["Close"].iloc[-1])
    else:
        raise ValueError(f"No price available for {symbol}")


# ============================================================================
# Alpha Vantage Implementation (free with API key)
# ============================================================================

def _fetch_alphavantage(symbol: str, days: int, interval: str) -> pl.DataFrame:
    """
    Fetch data from Alpha Vantage (free tier: 25 requests/day).
    
    Requires ALPHA_VANTAGE_API_KEY environment variable.
    Get free key at: https://www.alphavantage.co/support/#api-key
    """
    import requests
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY not set. Get free key at https://www.alphavantage.co/support/#api-key")
    
    url = "https://www.alphavantage.co/query"
    interval_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "60min",
    }

    if interval == "1d":
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": api_key,
            "outputsize": "full" if days > 100 else "compact",
        }
        key = "Time Series (Daily)"
    elif interval in interval_map:
        api_interval = interval_map[interval]
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "apikey": api_key,
            "interval": api_interval,
            "outputsize": "full" if days > 3 else "compact",
        }
        key = f"Time Series ({api_interval})"
    else:
        raise ValueError(f"Alpha Vantage does not support interval '{interval}'")
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if key not in data:
        raise ValueError(f"Alpha Vantage error: {data.get('Note') or data.get('Error Message', 'Unknown error')}")
    
    # Convert to DataFrame
    time_series = data[key]
    records = []
    
    for date_str, values in time_series.items():
        if interval == "1d":
            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            timestamp = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        records.append({
            "Date": timestamp,
            "Open": float(values["1. open"]),
            "High": float(values["2. high"]),
            "Low": float(values["3. low"]),
            "Close": float(values["4. close"]),
            "Volume": int(float(values["5. volume"])),
        })
    
    df = pl.DataFrame(records)
    df = df.sort("Date", descending=True)
    
    # Limit to requested days
    cutoff_date = datetime.now() - timedelta(days=days)
    df = df.filter(pl.col("Date") >= cutoff_date)
    
    return df


def _fetch_alphavantage_price(symbol: str) -> float:
    """Fetch current price from Alpha Vantage."""
    import requests
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY not set")
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key,
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if "Global Quote" not in data:
        raise ValueError(f"Alpha Vantage error: {data.get('Note') or data.get('Error Message', 'Unknown error')}")
    
    quote = data["Global Quote"]
    return float(quote["05. price"])

