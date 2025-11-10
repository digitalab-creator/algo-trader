from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from ib_insync import Stock

from app.core.orders import place_bracket_buy
from app.models.trade import Trade
from app.services.market_data import DataSource, fetch_historical_data
from app.strategies.base import BaseStrategyRunner, StrategyResult


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared.columns = [col.lower() for col in prepared.columns]
    if "date" in prepared.columns:
        prepared = prepared.sort_values("date")
    elif "datetime" in prepared.columns:
        prepared = prepared.sort_values("datetime")
    return prepared.reset_index(drop=True)


class HighIntradayRunner(BaseStrategyRunner):
    strategy_name = "high_intraday"
    layer_name = "high"

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
            self.logger.warning("High layer universe is empty; skipping")
            return StrategyResult(trades_created=0, status="skipped", notes="Universe not configured")

        allocation_per_trade = budget * 0.005
        trades_created = 0
        total_budget_used = 0.0
        estimated_profit = 0.0

        for symbol in universe:
            self.logger.info("Evaluating high-risk strategy for %s", symbol)

            df = self._load_price_history(
                symbol=symbol,
                simulate=simulate,
                ib=ib,
                market_source=market_source,
            )
            if df is None:
                continue

            df = _prepare_dataframe(df)

            if len(df) < 20:
                self.logger.warning("Insufficient bars for %s (found %s)", symbol, len(df))
                continue

            df["vwap"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()
            df["high12"] = df["high"].rolling(12).max()
            df["low12"] = df["low"].rolling(12).min()
            df["atr"] = (df["high"] - df["low"]).rolling(14).mean()

            latest = df.iloc[-1]

            if latest["close"] > latest["high12"] and latest["close"] > latest["vwap"]:
                atr = latest["atr"]
                entry = latest["close"]
                stop = entry - 1.2 * atr
                take = entry + 2.5 * atr
                risk_per_share = entry - stop
                quantity = int(allocation_per_trade / max(risk_per_share, 0.01))

                if quantity <= 0:
                    continue

                capital_required = quantity * entry
                total_budget_used += capital_required
                potential_profit = max((take - entry) * quantity, 0.0)
                estimated_profit += potential_profit

                if simulate:
                    self.logger.info(
                        "Simulated high-risk signal %s qty=%s entry=%.2f",
                        symbol,
                        quantity,
                        entry,
                    )
                else:
                    self.logger.info(
                        "Placing high-risk order %s qty=%s entry=%.2f",
                        symbol,
                        quantity,
                        entry,
                    )

                statuses = place_bracket_buy(
                    ib,
                    symbol,
                    quantity,
                    entry,
                    stop,
                    take,
                    simulate=simulate,
                )
                order_status = statuses[0].status if statuses else ("simulated" if simulate else None)

                notes = (
                    "Simulated signal - no live order executed"
                    if simulate
                    else "High intraday breakout executed"
                )

                trade = Trade(
                    symbol=symbol,
                    layer=self.layer_name,
                    strategy=self.strategy_name,
                    side="BUY",
                    qty=quantity,
                    entry_price=entry,
                    budget_allocated=capital_required,
                    entry_signal="intraday_breakout_vwap",
                    order_status=order_status,
                    signal_snapshot={
                        "vwap": float(df["vwap"].iloc[-1]),
                        "high12": float(df["high12"].iloc[-1]),
                        "low12": float(df["low12"].iloc[-1]),
                        "atr": float(atr),
                        "simulate": simulate,
                    },
                    strategy_run_id=strategy_run.id,
                    notes=notes,
                )
                session.add(trade)
                trades_created += 1

        status = "completed" if trades_created else "no_trades"
        notes = None if trades_created else "No qualifying breakouts detected"

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
        """Fetch intraday price history depending on simulation mode."""

        if simulate:
            history = fetch_historical_data(symbol, days=7, interval="5m", source=market_source)
            if history.is_empty():
                self.logger.warning(
                    "No intraday data for %s via %s",
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
            durationStr="1 D",
            barSizeSetting="5 mins",
            whatToShow="TRADES",
            useRTH=True,
        )
        if len(bars) < 20:
            self.logger.warning("Not enough bars for %s", symbol)
            return None
        return pd.DataFrame([bar.__dict__ for bar in bars])

