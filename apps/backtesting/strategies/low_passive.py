"""Low-risk passive allocation strategy evaluator"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd

from libs.strategies.base import BaseBacktestStrategy, TradeSignal, strategy_registry
from apps.backtesting.strategies.utils import bars_to_dataframe


DEFAULT_PARAMS: Dict[str, float] = {
    "target_weight": 0.2,
    "rebalance_days": 7,
}


@strategy_registry.register
class LowPassiveStrategy(BaseBacktestStrategy):
    version = "low_passive_v1"
    description = "Passive ETF allocation with periodic rebalancing"

    def generate_signals(
        self,
        symbol: str,
        bars: list,
        *,
        params: dict,
    ) -> List[TradeSignal]:
        df = bars_to_dataframe(bars)
        if df.empty:
            return []

        cfg = {**DEFAULT_PARAMS, **params}
        target_weight = float(cfg["target_weight"])
        rebalance_days = int(cfg["rebalance_days"])

        signals: List[TradeSignal] = []
        last_rebalance: datetime | None = None

        for dt in df.index:
            price = float(df.loc[dt, "close"])
            timestamp = dt.to_pydatetime() if isinstance(dt, pd.Timestamp) else datetime.fromisoformat(str(dt))

            if last_rebalance is None or (timestamp - last_rebalance).days >= rebalance_days:
                signal = TradeSignal(
                    symbol=symbol,
                    timestamp=timestamp,
                    side="buy" if target_weight >= 0 else "sell",
                    entry_price=price,
                    confidence=0.6,
                    target_weight=target_weight,
                    metadata={
                        "rebalance": True,
                        "target_weight": target_weight,
                        "price": price,
                    },
                )
                signals.append(signal)
                last_rebalance = timestamp

        return signals
