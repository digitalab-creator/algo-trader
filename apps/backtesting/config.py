"""Backtesting app configuration"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class BacktestingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    backtesting_database_url: str = (
        "postgresql+psycopg://backtest_user:backtest_pass@localhost:5433/backtesting_db"
    )
    initial_capital: float = 100_000.0
    simulation_commission: float = 0.0
    simulation_slippage: float = 0.0


@lru_cache
def get_settings() -> BacktestingSettings:
    return BacktestingSettings()
