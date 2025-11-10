"""Data models for market data"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

DataSource = Literal["ibkr", "alphavantage", "yfinance", "cache"]


@dataclass
class NormalizedBar:
    """
    Unified price bar format - all data sources normalize to this.
    
    Inspired by lotto-predictor's Draw model pattern.
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str
    source: DataSource
    interval: str  # '1m', '5m', '1h', '1d', etc.
    
    def __post_init__(self):
        """Validate data"""
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) < Low ({self.low})")
        if self.close < 0 or self.open < 0:
            raise ValueError("Negative prices not allowed")
        if self.volume < 0:
            raise ValueError("Negative volume not allowed")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "symbol": self.symbol,
            "source": self.source,
            "interval": self.interval,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "NormalizedBar":
        """Create from dictionary (for cache deserialization)"""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

