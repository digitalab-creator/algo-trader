"""Backtesting strategy implementations"""

from apps.backtesting.strategies.high_intraday import HighIntradayStrategy
from apps.backtesting.strategies.medium_swing import MediumSwingStrategy
from apps.backtesting.strategies.low_passive import LowPassiveStrategy

STRATEGIES = {
    HighIntradayStrategy.version: HighIntradayStrategy,
    MediumSwingStrategy.version: MediumSwingStrategy,
    LowPassiveStrategy.version: LowPassiveStrategy,
}
