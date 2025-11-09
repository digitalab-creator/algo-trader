from __future__ import annotations

import logging
from typing import Any, Dict, List

from ib_insync import IB, Stock
from sqlmodel import Session

from app.core.orders import place_market_order
from app.models.strategy_run import StrategyRun
from app.models.trade import Trade
from app.services.market_data import DataSource, fetch_current_price

logger = logging.getLogger(__name__)


def maintain_mix(
    ib: IB,
    layer_cfg: Dict[str, Any],
    equity_budget: float,
    *,
    session: Session,
    strategy_run: StrategyRun,
    layer_name: str = "low",
    simulate: bool = False,
    market_source: DataSource | None = None,
) -> int:
    target_instruments: List[Dict[str, float]] = layer_cfg.get("target_instruments", [])
    if not target_instruments:
        logger.warning("Low layer target instruments missing; skipping rebalance")
        return 0

    if simulate:
        holdings: Dict[str, float] = {}
    else:
        holdings = {pos.contract.symbol: float(pos.position) for pos in ib.positions()}  # type: ignore[attr-defined]

    trades_created = 0

    for instrument in target_instruments:
        symbol = instrument["symbol"]
        weight = instrument["weight"]
        target_value = equity_budget * weight

        if simulate:
            try:
                price = fetch_current_price(symbol, source=market_source)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Unable to fetch price for %s: %s", symbol, exc)
                continue
        else:
            contract = Stock(symbol, "SMART", "USD")
            qualified = ib.qualifyContracts(contract)[0]
            ticker = ib.reqMktData(qualified, "", False, False)
            ib.sleep(1)
            price = ticker.last or ticker.close or 0.0
            ib.cancelMktData(qualified)

        if price <= 0:
            logger.warning("Price unavailable for %s", symbol)
            continue

        target_qty = int(target_value / price)
        current_qty = int(holdings.get(symbol, 0.0))
        delta = target_qty - current_qty

        if delta == 0:
            logger.info("Position %s already balanced", symbol)
            continue

        action = "BUY" if delta > 0 else "SELL"
        logger.info(
            "%s rebalance %s: target=%s current=%s delta=%s",
            "Simulated" if simulate else "Executing",
            symbol,
            target_qty,
            current_qty,
            delta,
        )
        status = place_market_order(ib, action, symbol, abs(delta), simulate=simulate)
        order_status = status.status if status else ("simulated" if simulate else None)

        notes = (
            "Simulated rebalance - no live order executed"
            if simulate
            else "Rebalance execution"
        )

        trade = Trade(
            symbol=symbol,
            layer=layer_name,
            strategy="low_passive",
            side=action.upper(),
            qty=abs(delta),
            entry_price=price,
            budget_allocated=target_value,
            entry_signal="target_rebalance",
            order_status=order_status,
            signal_snapshot={
                "target_qty": float(target_qty),
                "current_qty": float(current_qty),
                "target_value": float(target_value),
                "weight": float(weight),
                "simulate": simulate,
            },
            strategy_run_id=strategy_run.id,
            notes=notes,
        )
        session.add(trade)
        trades_created += 1

    return trades_created

