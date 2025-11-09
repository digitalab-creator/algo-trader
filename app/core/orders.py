from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Optional

from ib_insync import IB, OrderStatus, Stock

logger = logging.getLogger(__name__)


def place_bracket_buy(
    ib: IB,
    symbol: str,
    quantity: int,
    entry_price: float,
    stop_price: float,
    take_profit: float,
    *,
    simulate: bool = False,
) -> list[OrderStatus]:
    if simulate:
        logger.info(
            "Simulated bracket order %s qty=%s entry=%.2f stop=%.2f take=%.2f",
            symbol,
            quantity,
            entry_price,
            stop_price,
            take_profit,
        )
        return [SimpleNamespace(status="simulated")]  # type: ignore[list-item]

    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)
    logger.info(
        "Submitting bracket order %s qty=%s entry=%.2f stop=%.2f take=%.2f",
        symbol,
        quantity,
        entry_price,
        stop_price,
        take_profit,
    )
    parent = ib.bracketOrder(
        action="BUY",
        quantity=quantity,
        limitPrice=entry_price,
        takeProfitPrice=take_profit,
        stopLossPrice=stop_price,
    )
    trades = ib.placeOrder(contract, parent[0])
    # attach stops and take profits
    for order in parent[1:]:
        order.parentId = parent[0].orderId
        ib.placeOrder(contract, order)
    ib.sleep(0.5)
    statuses = [trade.orderStatus for trade in ib.trades() if trade.contract == contract]
    return statuses


def place_market_order(
    ib: IB,
    action: str,
    symbol: str,
    quantity: int,
    tif: str = "DAY",
    *,
    simulate: bool = False,
) -> Optional[OrderStatus]:
    if simulate:
        logger.info(
            "Simulated market order %s %s qty=%s",
            action,
            symbol,
            quantity,
        )
        return SimpleNamespace(status="simulated")  # type: ignore[return-value]

    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)
    order = ib.marketOrder(action.upper(), quantity, tif=tif)
    logger.info("Submitting market order %s %s qty=%s", action, symbol, quantity)
    trade = ib.placeOrder(contract, order)
    return trade.orderStatus if trade else None

