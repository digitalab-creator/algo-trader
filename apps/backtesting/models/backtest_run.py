"""BacktestRun model - stores backtest execution metadata and results"""

from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON


class BacktestRun(SQLModel, table=True):
    """
    Stores metadata and results for each backtest execution.
    
    Like lotto-predictor's Prediction model, this stores:
    - Strategy configuration
    - Parameter set (as JSON hash for uniqueness)
    - Aggregate metrics (ROI, Sharpe, drawdown)
    - Time period tested
    
    Each BacktestRun has many BacktestTrades (one-to-many relationship)
    """
    __tablename__ = "backtest_runs"
    
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Strategy identification
    strategy_name: str = Field(index=True)
    strategy_version: str = Field(default="v1")
    params_hash: str = Field(index=True)  # MD5 hash of params JSON
    params_json: dict = Field(sa_column=Column(JSON))  # Full params for reference
    
    # Symbols and period
    symbols: list[str] = Field(sa_column=Column(JSON))
    start_date: date
    end_date: date
    interval: str = Field(default="1d")  # 1m, 5m, 1h, 1d, etc.
    
    # Trade statistics
    total_trades: int = Field(default=0)
    winning_trades: int = Field(default=0)
    losing_trades: int = Field(default=0)
    
    # Financial metrics
    initial_capital: float = Field(default=100000.0)
    final_capital: float = Field(default=100000.0)
    total_pnl: float = Field(default=0.0)
    roi: float = Field(default=0.0, index=True)  # Return on investment (%)
    
    # Risk metrics
    sharpe_ratio: Optional[float] = Field(default=None)
    max_drawdown: Optional[float] = Field(default=None)  # Max % drawdown
    max_drawdown_duration: Optional[int] = Field(default=None)  # Days
    
    # Win/Loss metrics
    win_rate: float = Field(default=0.0)  # % of winning trades
    avg_win: Optional[float] = Field(default=None)
    avg_loss: Optional[float] = Field(default=None)
    profit_factor: Optional[float] = Field(default=None)  # gross_profit / gross_loss
    
    # Execution metadata
    execution_time_seconds: Optional[float] = Field(default=None)
    data_source: str = Field(default="cache")  # Where data came from
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Notes
    notes: Optional[str] = Field(default=None)
    
    def calculate_metrics(self):
        """Calculate derived metrics from totals"""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        if self.initial_capital > 0:
            self.roi = ((self.final_capital - self.initial_capital) / self.initial_capital) * 100
        
        if self.avg_win and self.avg_loss and self.avg_loss != 0:
            gross_profit = self.avg_win * self.winning_trades
            gross_loss = abs(self.avg_loss * self.losing_trades)
            self.profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

