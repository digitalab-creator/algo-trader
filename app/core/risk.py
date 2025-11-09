from __future__ import annotations

import logging
import os
from typing import Dict

from ib_insync import IB

from app.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_SIM_EQUITY = 100_000.0


def get_simulated_equity() -> float:
    """Return simulated equity from env or default."""
    env_value = os.getenv("SIMULATED_EQUITY")
    if env_value:
        try:
            return float(env_value)
        except ValueError:
            logger.warning("Invalid SIMULATED_EQUITY=%s; falling back to %.2f", env_value, _DEFAULT_SIM_EQUITY)
    return _DEFAULT_SIM_EQUITY


class RiskManager:
    def __init__(self, ib: IB | None, settings: Settings, *, simulated: bool = False) -> None:
        self.ib = ib
        self.settings = settings
        self.simulated = simulated

    def equity(self) -> float:
        if self.simulated or self.ib is None or not self.ib.isConnected():
            equity = get_simulated_equity()
            logger.debug("Using simulated equity: %.2f", equity)
            return equity

        summary = {item.tag: item.value for item in self.ib.accountSummary()}
        equity = float(summary.get("NetLiquidation", 0.0))
        logger.debug("Current equity: %.2f", equity)
        return equity

    def budget(self, layer: str) -> float:
        targets = self.settings.portfolio.targets
        weights: Dict[str, float] = {
            "high": targets.high,
            "medium": targets.medium,
            "low": targets.low,
        }
        equity = self.equity()
        weight = weights.get(layer, 0.0)
        budget_value = equity * weight
        logger.debug("Budget for layer %s: %.2f", layer, budget_value)
        return budget_value

