from __future__ import annotations

from typing import Any, Dict, List

from ib_insync import Stock

from app.core.orders import place_market_order
from app.models.trade import Trade
from app.services.market_data import DataSource, fetch_current_price
from app.strategies.base import BaseStrategyRunner, StrategyResult


class LowPassiveRunner(BaseStrategyRunner):
    strategy_name = "low_passive"
    layer_name = "low"

    async def execute_strategy(
        self,
        *,
        ib,
        session,
        strategy_run,
        budget: float,
        layer_cfg: Dict[str, Any],
        simulate: bool,
        market_source: str,
    ) -> StrategyResult:
        target_instruments: List[Dict[str, float]] = layer_cfg.get("target_instruments", [])
        if not target_instruments:
            self.logger.warning("Low layer target instruments missing; skipping rebalance")
            return StrategyResult(trades_created=0, status="skipped", notes="No target instruments configured")

        holdings = (
            {}
            if simulate
            else {pos.contract.symbol: float(pos.position) for pos in ib.positions()}  # type: ignore[attr-defined]
        )

        trades_created = 0
        total_budget_used = 0.0

        for instrument in target_instruments:
            symbol = instrument["symbol"]
            weight = instrument["weight"]
            target_value = budget * weight

            price = self._current_price(
                symbol=symbol,
                simulate=simulate,
                ib=ib,
                market_source=market_source,
            )
            if price is None or price <= 0:
                self.logger.warning("Price unavailable for %s", symbol)
                continue

            target_qty = int(target_value / price)
            current_qty = int(holdings.get(symbol, 0.0))
            delta = target_qty - current_qty

            if delta == 0:
                self.logger.info("Position %s already balanced", symbol)
                continue

            action = "BUY" if delta > 0 else "SELL"
            trade_value = abs(delta) * price
            total_budget_used += trade_value
            self.logger.info(
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
                layer=self.layer_name,
                strategy=self.strategy_name,
                side=action.upper(),
                qty=abs(delta),
                entry_price=price,
                budget_allocated=trade_value,
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

        status = "completed" if trades_created else "no_trades"
        notes = None if trades_created else "All positions already balanced"

        return StrategyResult(
            trades_created=trades_created,
            signals_triggered=trades_created,
            status=status,
            notes=notes,
            budget_used=total_budget_used,
            estimated_profit=0.0,
        )

    def _current_price(
        self,
        *,
        symbol: str,
        simulate: bool,
        ib,
        market_source: DataSource | str | None,
    ) -> float | None:
        """Resolve the current price depending on simulation mode."""

        if simulate:
            try:
                return fetch_current_price(symbol, source=market_source)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Unable to fetch price for %s: %s", symbol, exc)
                return None

        contract = Stock(symbol, "SMART", "USD")
        qualified = ib.qualifyContracts(contract)[0]
        ticker = ib.reqMktData(qualified, "", False, False)
        ib.sleep(1)
        price = ticker.last or ticker.close or 0.0
        ib.cancelMktData(qualified)
        return float(price) if price else None
