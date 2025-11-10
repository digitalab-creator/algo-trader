"""Medium-risk swing strategy evaluator"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd

from libs.strategies.base import BaseBacktestStrategy, TradeSignal, strategy_registry
from libs.strategies import indicators
from apps.backtesting.strategies.utils import bars_to_dataframe


DEFAULT_PARAMS: Dict[str, float] = {
    "ema_fast": 20,
    "ema_slow": 50,
    "breakout_lookback": 10,
    "atr_period": 14,
    "stop_atr_multiple": 1.5,
    "take_atr_multiple": 3.0,
    "risk_percent": 0.01,
}


@strategy_registry.register
class MediumSwingStrategy(BaseBacktestStrategy):
    version = "medium_swing_v1"
    description = "EMA crossover + breakout swing strategy"

    def generate_signals(
        self,
        symbol: str,
        bars: list,
        *,
        params: dict,
    ) -> List[TradeSignal]:
        df = bars_to_dataframe(bars)
        if df.empty or len(df) < params.get("ema_slow", DEFAULT_PARAMS["ema_slow"]):
            return []

        cfg = {**DEFAULT_PARAMS, **params}

        df["ema_fast"] = indicators.ema(df["close"], int(cfg["ema_fast"]))
        df["ema_slow"] = indicators.ema(df["close"], int(cfg["ema_slow"]))
        df["atr"] = indicators.atr(df, int(cfg["atr_period"]))
        df["recent_high"] = indicators.rolling_max(df["high"], int(cfg["breakout_lookback"]))

        signals: List[TradeSignal] = []

        for dt in df.index[int(cfg["ema_slow"]):]:
            row: pd.Series = df.loc[dt]
            prev_row: pd.Series = df.loc[df.index[df.index.get_loc(dt) - 1]]

            if pd.isna(row["ema_fast"]) or pd.isna(row["ema_slow"]):
                continue

            bullish_cross = row["ema_fast"] > row["ema_slow"] and prev_row["ema_fast"] <= prev_row["ema_slow"]
            breakout = row["close"] > prev_row["recent_high"]

            if bullish_cross and breakout:
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
                    confidence=0.8,
                    stop_loss=float(stop_loss),
                    take_profit=float(take_profit),
                    risk_percent=float(cfg["risk_percent"]),
                    metadata={
                        "ema_fast": float(row["ema_fast"]),
                        "ema_slow": float(row["ema_slow"]),
                        "atr": float(atr_value),
                        "recent_high": float(prev_row["recent_high"]),
                    },
                )
                signals.append(signal)

        return signals
