"""High-risk intraday breakout strategy evaluator"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd

from libs.strategies.base import BaseBacktestStrategy, TradeSignal, strategy_registry
from libs.strategies import indicators
from apps.backtesting.strategies.utils import bars_to_dataframe


DEFAULT_PARAMS: Dict[str, float] = {
    "lookback": 12,
    "atr_period": 14,
    "stop_atr_multiple": 1.2,
    "take_atr_multiple": 2.5,
    "risk_percent": 0.005,
    "vwap_window": 20,
}


@strategy_registry.register
class HighIntradayStrategy(BaseBacktestStrategy):
    version = "high_intraday_v1"
    description = "Intraday breakout strategy with ATR-based risk"

    def generate_signals(
        self,
        symbol: str,
        bars: list,
        *,
        params: dict,
    ) -> List[TradeSignal]:
        df = bars_to_dataframe(bars)
        if df.empty or len(df) < params.get("lookback", DEFAULT_PARAMS["lookback"]):
            return []

        cfg = {**DEFAULT_PARAMS, **params}

        lookback = int(cfg["lookback"])
        df["rolling_high"] = indicators.rolling_max(df["high"], lookback)
        df["rolling_low"] = indicators.rolling_min(df["low"], lookback)
        df["atr"] = indicators.atr(df, int(cfg["atr_period"]))
        df["vwap"] = indicators.vwap(df, int(cfg["vwap_window"]))

        signals: List[TradeSignal] = []

        for dt in df.index[lookback:]:
            row: pd.Series = df.loc[dt]
            prev_row: pd.Series = df.loc[df.index[df.index.get_loc(dt) - 1]]

            breakout = row["close"] > prev_row["rolling_high"]
            above_vwap = row["close"] > row["vwap"]

            if breakout and above_vwap:
                atr_value = row["atr"]
                if atr_value <= 0:
                    continue

                stop_loss = row["close"] - atr_value * cfg["stop_atr_multiple"]
                take_profit = row["close"] + atr_value * cfg["take_atr_multiple"]

                signal = TradeSignal(
                    symbol=symbol,
                    timestamp=dt.to_pydatetime() if isinstance(dt, pd.Timestamp) else datetime.fromisoformat(str(dt)),
                    side="buy",
                    entry_price=float(row["close"]),
                    confidence=0.9,
                    stop_loss=float(stop_loss),
                    take_profit=float(take_profit),
                    risk_percent=float(cfg["risk_percent"]),
                    holding_period_minutes=60,
                    metadata={
                        "atr": float(atr_value),
                        "rolling_high": float(prev_row["rolling_high"]),
                        "vwap": float(row["vwap"]),
                    },
                )
                signals.append(signal)

        return signals
