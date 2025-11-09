from __future__ import annotations

import logging
import os
from typing import Optional

from ib_insync import IB, Contract, Stock

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

_TRUTHY = {"1", "true", "yes", "y", "on"}


class BrokerClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.ib = IB()
        self.simulated = os.getenv("BROKER_SIMULATED", "").strip().lower() in _TRUTHY

        if self.simulated:
            logger.info("BrokerClient initialized in simulated mode; IBKR connection disabled")

    def connect(self) -> None:
        if self.simulated:
            logger.info("Simulated broker mode: skipping IBKR connection")
            return

        mode = self.settings.mode
        port = (
            self.settings.ib.port_paper
            if mode == "paper"
            else self.settings.ib.port_live
        )
        client_id = (
            self.settings.ib.client_id_paper
            if mode == "paper"
            else self.settings.ib.client_id_live
        )
        logger.info("Connecting to IBKR [%s] on %s:%s", mode, self.settings.ib.host, port)
        self.ib.connect(self.settings.ib.host, port, clientId=client_id)
        logger.info("Connected to IBKR in %s mode", mode)

    def disconnect(self) -> None:
        if self.simulated:
            logger.info("Simulated broker mode: skipping disconnect")
            return

        if self.ib.isConnected():
            self.ib.disconnect()

    def ensure_connected(self) -> None:
        if self.simulated:
            return

        if not self.ib.isConnected():
            self.connect()

    def qualify(self, contract: Contract) -> Contract:
        if self.simulated:
            return contract

        self.ensure_connected()
        qualified = self.ib.qualifyContracts(contract)
        return qualified[0] if qualified else contract

    def stock(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Stock:
        contract = Stock(symbol, exchange, currency)
        return self.qualify(contract)

    def last_price(self, symbol: str) -> float | None:
        if self.simulated:
            logger.warning("Simulated broker mode: last_price not available via IBKR client")
            return None

        contract = self.stock(symbol)
        ticker = self.ib.reqMktData(contract, "", False, False)
        self.ib.sleep(1)
        self.ib.cancelMktData(contract)
        return ticker.last or ticker.close or None

    def account_equity(self) -> float:
        if self.simulated:
            from app.core.risk import get_simulated_equity

            equity = get_simulated_equity()
            logger.debug("Simulated broker mode: using simulated equity %.2f", equity)
            return equity

        self.ensure_connected()
        summary = {item.tag: item.value for item in self.ib.accountSummary()}
        return float(summary.get("NetLiquidation", 0.0))

