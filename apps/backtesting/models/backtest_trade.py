"""BacktestTrade model - stores individual simulated trades"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON


class BacktestTrade(SQLModel, table=True):
    """
    Stores details of each simulated trade in a backtest.
    
    Like lotto-predictor's PredictionDetail model, this stores:
    - Entry and exit details
    - P/L calculation
    - Exit reason
    - Metadata (indicators, signals, etc.)
    
    Many BacktestTrades belong to one BacktestRun (many-to-one relationship)
    """
    __tablename__ = "backtest_trades"
    
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign key to BacktestRun
    backtest_run_id: int = Field(foreign_key="backtest_runs.id", index=True)
    
    # Symbol
    symbol: str = Field(index=True)
    
    # Entry details
    entry_time: datetime = Field(index=True)
    entry_price: float
    entry_signal: Optional[str] = Field(default=None)  # What triggered entry
    
    # Exit details
    exit_time: datetime
    exit_price: float
    exit_signal: Optional[str] = Field(default=None)  # What triggered exit
    exit_reason: str  # 'take_profit', 'stop_loss', 'signal_reversal', 'end_of_period'
    
    # Position details
    side: str  # 'long' or 'short'
    qty: float  # Position size
    
    # P/L calculation
    pnl: float  # Absolute P/L in currency
    pnl_percent: float  # P/L as percentage of entry
    
    # Risk management
    stop_loss: Optional[float] = Field(default=None)
    take_profit: Optional[float] = Field(default=None)
    risk_amount: Optional[float] = Field(default=None)  # $ risked on trade
    
    # Trade duration
    duration_seconds: int  # How long trade was open
    
    # Commission and slippage
    commission: float = Field(default=0.0)
    slippage: float = Field(default=0.0)
    
    # Metadata (store indicators, signals, etc.)
    details: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_metrics(self):
        """Calculate derived metrics"""
        # P/L percent
        if self.entry_price > 0:
            if self.side == "long":
                self.pnl_percent = ((self.exit_price - self.entry_price) / self.entry_price) * 100
            else:  # short
                self.pnl_percent = ((self.entry_price - self.exit_price) / self.entry_price) * 100
        
        # Duration
        self.duration_seconds = int((self.exit_time - self.entry_time).total_seconds())
        
        # Absolute P/L
        price_diff = self.exit_price - self.entry_price
        if self.side == "short":
            price_diff = -price_diff
        
        self.pnl = (price_diff * self.qty) - self.commission - self.slippage

