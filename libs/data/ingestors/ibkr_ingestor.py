"""IBKR data ingestor"""

import os
from datetime import datetime
from ib_insync import IB, Stock, util
import structlog

logger = structlog.get_logger(__name__)


class IBKRIngestor:
    """
    Fetch data from Interactive Brokers.
    
    Pros:
    - Real-time and historical data
    - Best for live trading
    - Supports all asset classes
    
    Cons:
    - Requires TWS/IB Gateway running
    - Requires active connection
    - More complex setup
    """
    
    def __init__(self):
        """Initialize IBKR ingestor (connection created on demand)"""
        self.ib = None
        self.connected = False
    
    def _ensure_connection(self):
        """Ensure IBKR connection is active"""
        if self.connected and self.ib and self.ib.isConnected():
            return
        
        host = os.getenv("IBKR_HOST", "127.0.0.1")
        port = int(os.getenv("IBKR_PORT", "7497"))
        client_id = int(os.getenv("IBKR_CLIENT_ID", "101"))
        
        try:
            self.ib = IB()
            self.ib.connect(host, port, clientId=client_id, timeout=10)
            self.connected = True
            logger.info("IBKR connection established", host=host, port=port)
        except Exception as e:
            logger.error("IBKR connection failed", error=str(e))
            raise
    
    def fetch(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1d"
    ) -> list:
        """
        Fetch historical data from IBKR.
        
        Args:
            symbol: Ticker symbol
            start: Start date (ISO format)
            end: End date (ISO format)
            interval: Time interval (1d, 1h, 5m, etc.)
            
        Returns:
            List of BarData objects
            
        Raises:
            Exception: If fetch fails or not connected
        """
        self._ensure_connection()
        
        logger.debug(
            "Fetching from IBKR",
            symbol=symbol,
            start=start,
            end=end,
            interval=interval
        )
        
        try:
            # Create contract
            contract = Stock(symbol, "SMART", "USD")
            self.ib.qualifyContracts(contract)
            
            # Map interval to IBKR format
            interval_map = {
                "1d": "1 day",
                "1h": "1 hour",
                "5m": "5 mins",
                "15m": "15 mins",
                "1m": "1 min"
            }
            bar_size = interval_map.get(interval, "1 day")
            
            # Calculate duration (IBKR requires duration string like "1 Y", "6 M")
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            days = (end_dt - start_dt).days
            
            if days > 365:
                duration = f"{days // 365} Y"
            elif days > 30:
                duration = f"{days // 30} M"
            else:
                duration = f"{days} D"
            
            # Fetch bars
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime=end,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=True  # Regular trading hours only
            )
            
            if not bars:
                raise ValueError(f"No data returned for {symbol}")
            
            logger.info(
                "IBKR fetch successful",
                symbol=symbol,
                bars_count=len(bars)
            )
            
            return bars
            
        except Exception as e:
            logger.error(
                "IBKR fetch failed",
                symbol=symbol,
                error=str(e)
            )
            raise
    
    def disconnect(self):
        """Close IBKR connection"""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("IBKR connection closed")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.disconnect()

