"""Indicator helper functions for strategies"""

from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"].shift(1)
    tr = np.maximum.reduce([
        high - low,
        (high - close).abs(),
        (low - close).abs(),
    ])
    return pd.Series(tr, index=df.index).rolling(window=period, min_periods=1).mean()


def rolling_max(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).max()


def rolling_min(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).min()


def vwap(df: pd.DataFrame, window: int) -> pd.Series:
    price_volume = df["close"] * df["volume"]
    pv_cumsum = price_volume.cumsum()
    volume_cumsum = df["volume"].cumsum().replace(0, np.nan)
    vwap_series = pv_cumsum / volume_cumsum
    if window:
        vwap_series = vwap_series.rolling(window=window, min_periods=1).mean()
    return vwap_series
