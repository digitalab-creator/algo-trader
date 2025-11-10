"""Utility helpers for backtesting strategies"""

from __future__ import annotations

import pandas as pd


def bars_to_dataframe(bars: list) -> pd.DataFrame:
    """Convert list of NormalizedBar to pandas DataFrame."""

    if not bars:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    data = [
        {
            "timestamp": bar.timestamp,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
        }
        for bar in bars
    ]

    df = pd.DataFrame(data)
    df.sort_values("timestamp", inplace=True)
    df.set_index("timestamp", inplace=True)
    return df
