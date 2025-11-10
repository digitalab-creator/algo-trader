from __future__ import annotations

from functools import lru_cache
from typing import Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HighLayerSettings(BaseSettings):
    weight: float = Field(default=0.10)
    universe: List[str] = Field(
        default_factory=lambda: ["TSLA", "NVDA", "AMD", "MSFT", "QQQ"]
    )


class MediumLayerSettings(BaseSettings):
    weight: float = Field(default=0.30)
    universe: List[str] = Field(
        default_factory=lambda: ["AAPL", "AMZN", "GOOGL", "META", "UNG"]
    )


class LowLayerSettingsInstrument(BaseSettings):
    symbol: str
    weight: float


class LowLayerSettings(BaseSettings):
    weight: float = Field(default=0.60)
    target_instruments: List[LowLayerSettingsInstrument] = Field(
        default_factory=lambda: [
            LowLayerSettingsInstrument(symbol="VOO", weight=0.35),
            LowLayerSettingsInstrument(symbol="VXUS", weight=0.25),
            LowLayerSettingsInstrument(symbol="TLT", weight=0.20),
            LowLayerSettingsInstrument(symbol="GLD", weight=0.10),
            LowLayerSettingsInstrument(symbol="SHY", weight=0.10),
        ]
    )


class PortfolioTargets(BaseSettings):
    high: float = Field(default=0.10)
    medium: float = Field(default=0.30)
    low: float = Field(default=0.60)


class PortfolioSettings(BaseSettings):
    targets: PortfolioTargets = Field(default_factory=PortfolioTargets)
    layers: Dict[str, BaseSettings] = Field(
        default_factory=lambda: {
            "high": HighLayerSettings(),
            "medium": MediumLayerSettings(),
            "low": LowLayerSettings(),
        }
    )


class IBSettings(BaseSettings):
    host: str = Field(default="127.0.0.1")
    port_paper: int = Field(default=7497)
    port_live: int = Field(default=7496)
    client_id_paper: int = Field(default=101)
    client_id_live: int = Field(default=202)


class DatabaseSettings(BaseSettings):
    url: str = Field(default="postgresql+psycopg://user:pass@db:5432/algo")


class Settings(BaseSettings):
    mode: str = Field(default="paper", pattern="^(paper|live)$")
    log_level: str = Field(default="INFO")
    ib: IBSettings = Field(default_factory=IBSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    portfolio: PortfolioSettings = Field(default_factory=PortfolioSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

