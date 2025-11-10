from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from ib_insync import Stock

from app.core.orders import place_bracket_buy
from app.models.trade import Trade
from app.services.market_data import DataSource, fetch_historical_data
from app.strategies.base import BaseStrategyRunner, StrategyResult


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe columns for indicator calculations."""
    normalized = df.copy()
    normalized.columns = [col.lower() for col in normalized.columns]

    if "date" in normalized.columns:
        normalized = normalized.sort_values("date")
    elif "datetime" in normalized.columns:
        normalized = normalized.sort_values("datetime")

    return normalized.reset_index(drop=True)


class MediumSwingRunner(BaseStrategyRunner):
    strategy_name = "medium_swing"
    layer_name = "medium"

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
        universe = layer_cfg.get("universe", [])
        if not universe:
            self.logger.warning("Medium layer universe is empty; skipping")
            return StrategyResult(trades_created=0, status="skipped", notes="Universe not configured")

        allocation_per_trade = budget * 0.01
        trades_created = 0
        total_budget_used = 0.0
        estimated_profit = 0.0

        for symbol in universe:
            self.logger.info("Evaluating medium strategy for %s", symbol)

            df = self._load_price_history(
                symbol=symbol,
                simulate=simulate,
                ib=ib,
                market_source=market_source,
            )
            if df is None:
                continue

            df = _prepare_dataframe(df)

            if len(df) < 50:
                self.logger.warning("Insufficient bars for %s (found %s)", symbol, len(df))
                continue

            df["ema20"] = df["close"].ewm(span=20).mean()
            df["ema50"] = df["close"].ewm(span=50).mean()
            df["high10"] = df["high"].rolling(10).max()
            df["atr"] = (df["high"] - df["low"]).rolling(14).mean()

            latest = df.iloc[-1]
            previous = df.iloc[-2]

            if latest["ema20"] > latest["ema50"] and latest["close"] > previous["high10"]:
                atr = latest["atr"]
                close_price = latest["close"]
                stop = close_price - 1.5 * atr
                take = close_price + 3 * atr
                risk_per_share = close_price - stop
                quantity = int(allocation_per_trade / max(risk_per_share, 0.01))

                if quantity <= 0:
                    continue

                capital_required = quantity * close_price
                total_budget_used += capital_required
                potential_profit = max((take - close_price) * quantity, 0.0)
                estimated_profit += potential_profit

                if simulate:
                    self.logger.info(
                        "Simulated medium swing signal %s qty=%s close=%.2f",
                        symbol,
                        quantity,
                        close_price,
                    )
                else:
                    self.logger.info(
                        "Placing medium swing order %s qty=%s close=%.2f",
                        symbol,
                        quantity,
                        close_price,
                    )

                statuses = place_bracket_buy(
                    ib,
                    symbol,
                    quantity,
                    close_price,
                    stop,
                    take,
                    simulate=simulate,
                )
                order_status = statuses[0].status if statuses else ("simulated" if simulate else None)

                notes = (
                    "Simulated signal - no live order executed"
                    if simulate
                    else "Medium swing breakout executed"
                )

                trade = Trade(
                    symbol=symbol,
                    layer=self.layer_name,
                    strategy=self.strategy_name,
                    side="BUY",
                    qty=quantity,
                    entry_price=close_price,
                    budget_allocated=capital_required,
                    entry_signal="ema20_gt_ema50_breakout",
                    order_status=order_status,
                    signal_snapshot={
                        "ema20": float(latest["ema20"]),
                        "ema50": float(latest["ema50"]),
                        "high10_prev": float(previous["high10"]),
                        "atr": float(atr),
                        "simulate": simulate,
                    },
                    strategy_run_id=strategy_run.id,
                    notes=notes,
                )
                session.add(trade)
                trades_created += 1

        status = "completed" if trades_created else "no_trades"
        notes = None if trades_created else "No qualifying signals detected"

        return StrategyResult(
            trades_created=trades_created,
            signals_triggered=trades_created,
            status=status,
            notes=notes,
            budget_used=total_budget_used,
            estimated_profit=estimated_profit,
        )

    def _load_price_history(
        self,
        *,
        symbol: str,
        simulate: bool,
        ib,
        market_source: DataSource | str | None,
    ) -> pd.DataFrame | None:
        """Fetch price history depending on simulation mode."""

        if simulate:
            history = fetch_historical_data(symbol, days=90, interval="1d", source=market_source)
            if history.is_empty():
                self.logger.warning(
                    "No historical data for %s via %s",
                    symbol,
                    market_source or "default source",
                )
                return None
            time_col = "Date" if "Date" in history.columns else history.columns[0]
            return pd.DataFrame(history.sort(time_col).to_dicts())

        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr="2 M",
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True,
        )
        if not bars:
            self.logger.warning("No historical data for %s", symbol)
            return None
        return pd.DataFrame([bar.__dict__ for bar in bars])

