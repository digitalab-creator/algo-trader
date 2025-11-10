from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from lib.infrastructure.logger import get_logger

from app.config import get_settings
from app.core.broker_client import BrokerClient
from app.core.risk import RiskManager
from app.main import context
from app.models.strategy_run import StrategyRun
from app.services.market_data import get_data_source


@dataclass(slots=True)
class StrategyResult:
    """Container for strategy execution outcomes."""

    trades_created: int = 0
    signals_triggered: int | None = None
    status: str | None = None
    notes: str | None = None
    budget_used: float = 0.0
    estimated_profit: float = 0.0


class BaseStrategyRunner:
    """
    Base class encapsulating shared orchestration for strategy execution.

    Subclasses must define:
        - strategy_name: Name of the strategy (e.g., "medium_swing")
        - layer_name: Portfolio layer key (e.g., "medium")
    """

    strategy_name: str = ""
    layer_name: str = ""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(f"{self.strategy_name or self.__class__.__name__}")
        self.market_source = get_data_source()
        self.client = BrokerClient(settings=self.settings)

    async def run(self, budget_override: float | None = None) -> StrategyResult:
        """Execute the strategy lifecycle."""

        if not self.strategy_name or not self.layer_name:
            raise ValueError("strategy_name and layer_name must be defined on subclasses.")

        self.logger.info("Starting %s strategy execution", self.strategy_name)
        self.client.connect()

        try:
            risk = RiskManager(self.client.ib, self.settings, simulated=self.client.simulated)
            budget = (
                float(budget_override)
                if budget_override is not None
                else risk.budget(self.layer_name)
            )
            if budget <= 0:
                raise ValueError("Budget must be positive when running a strategy")
            layer_cfg = self._layer_config()

            async with context.db.session() as session:
                run_record = StrategyRun(
                    strategy=self.strategy_name,
                    layer=self.layer_name,
                    status="running",
                    budget=budget,
                    started_at=datetime.utcnow(),
                )
                session.add(run_record)
                await session.flush()

                result = StrategyResult()

                try:
                    result = await self.execute_strategy(
                        ib=self.client.ib,
                        session=session,
                        strategy_run=run_record,
                        budget=budget,
                        layer_cfg=layer_cfg,
                        simulate=self.client.simulated,
                        market_source=self.market_source,
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    run_record.status = "failed"
                    run_record.notes = str(exc)
                    self.logger.exception("%s strategy execution failed", self.strategy_name, error=str(exc))
                    raise
                else:
                    run_record.trades_executed = result.trades_created
                    run_record.signals_triggered = (
                        result.signals_triggered
                        if result.signals_triggered is not None
                        else result.trades_created
                    )
                    run_record.status = result.status or (
                        "completed" if result.trades_created else "no_trades"
                    )
                    run_record.notes = result.notes

                    self.logger.info(
                        "Strategy execution completed",
                        trades_created=result.trades_created,
                        budget=budget,
                        budget_used=result.budget_used,
                        estimated_profit=result.estimated_profit,
                        status=run_record.status,
                    )
                finally:
                    run_record.finished_at = datetime.utcnow()

                    if context.monitoring:
                        await context.monitoring.metric("strategy.executed", 1)
                        await context.monitoring.event(
                            "strategy.completed",
                            strategy=self.strategy_name,
                            trades=run_record.trades_executed or 0,
                            status=run_record.status,
                            budget=budget,
                            budget_used=result.budget_used,
                        )

            return result
        finally:
            self.client.disconnect()
            self.logger.info("Strategy execution finished")

    def _layer_config(self) -> Dict[str, Any]:
        """Return the configuration dictionary for the configured layer."""

        try:
            layer_settings = self.settings.portfolio.layers[self.layer_name]
        except KeyError as exc:
            raise ValueError(f"Layer configuration '{self.layer_name}' not found in settings.") from exc
        return layer_settings.model_dump()

    async def execute_strategy(
        self,
        *,
        ib,
        session,
        strategy_run: StrategyRun,
        budget: float,
        layer_cfg: Dict[str, Any],
        simulate: bool,
        market_source: str,
    ) -> StrategyResult:
        """
        Perform strategy-specific logic.

        Must be implemented by subclasses.
        """

        raise NotImplementedError


