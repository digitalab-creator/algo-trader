"""
Run medium swing strategy.

Uses centralized infrastructure from lib/infrastructure.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from lib.infrastructure.logger import get_logger

from app.config import get_settings
from app.core.broker_client import BrokerClient
from app.core.risk import RiskManager
from app.main import context
from app.models.strategy_run import StrategyRun
from app.services.market_data import get_data_source
from app.strategies.medium_swing import run_medium

logger = get_logger(__name__)


async def main() -> None:
    """Execute medium swing strategy."""
    logger.info("Starting medium swing strategy execution")
    
    settings = get_settings()
    client = BrokerClient(settings=settings)
    client.connect()

    try:
        risk = RiskManager(client.ib, settings, simulated=client.simulated)
        budget = risk.budget("medium")
        layer_cfg = settings.portfolio.layers["medium"].model_dump()
        market_source = get_data_source()

        # Use centralized database from context
        async with context.db.session() as session:
            run_record = StrategyRun(
                strategy="medium_swing",
                layer="medium",
                status="running",
                budget=budget,
                started_at=datetime.utcnow(),
            )
            session.add(run_record)
            await session.flush()

            try:
                trades_created = run_medium(
                    client.ib,
                    layer_cfg,
                    budget,
                    session=session,
                    strategy_run=run_record,
                    layer_name="medium",
                    simulate=client.simulated,
                    market_source=market_source,
                )
                run_record.trades_executed = trades_created
                run_record.signals_triggered = trades_created
                run_record.status = "completed" if trades_created else "no_trades"
                
                logger.info(
                    "Strategy execution completed",
                    trades_created=trades_created,
                    budget=budget,
                )
            except Exception as exc:
                logger.exception("Medium strategy execution failed", error=str(exc))
                run_record.status = "failed"
                run_record.notes = str(exc)
                raise
            finally:
                run_record.finished_at = datetime.utcnow()
                
                # Record metric
                if context.monitoring:
                    await context.monitoring.metric("strategy.executed", 1)
                    await context.monitoring.event(
                        "strategy.completed",
                        strategy="medium_swing",
                        trades=trades_created,
                        status=run_record.status,
                    )
    finally:
        client.disconnect()
        logger.info("Strategy execution finished")


if __name__ == "__main__":
    asyncio.run(main())

