"""Alpha Vantage data ingestor"""

import requests
import structlog

logger = structlog.get_logger(__name__)


class AlphaVantageIngestor:
    """
    Fetch data from Alpha Vantage API.
    
    Pros:
    - Free API key (get at: https://www.alphavantage.co/support/#api-key)
    - 25 requests/day on free tier
    - Good for stocks, forex, crypto
    
    Cons:
    - Rate limited (25 req/day free, 5 req/min)
    - Slower than yfinance
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str):
        """
        Initialize with API key.
        
        Args:
            api_key: Alpha Vantage API key
        """
        self.api_key = api_key
        
        if not api_key or api_key == "your_alpha_vantage_key_here":
            logger.warning(
                "Alpha Vantage API key not configured. "
                "Get one at: https://www.alphavantage.co/support/#api-key"
            )
    
    def fetch(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1d"
    ) -> dict:
        """
        Fetch historical data from Alpha Vantage.
        
        Args:
            symbol: Ticker symbol
            start: Start date (ISO format) - ignored, Alpha Vantage returns all data
            end: End date (ISO format) - ignored
            interval: Time interval (mapped to Alpha Vantage format)
            
        Returns:
            Dict with time series data
            
        Raises:
            Exception: If fetch fails or API key invalid
        """
        if not self.api_key or self.api_key == "your_alpha_vantage_key_here":
            raise ValueError("Alpha Vantage API key not configured")
        
        logger.debug(
            "Fetching from Alpha Vantage",
            symbol=symbol,
            interval=interval
        )
        
        # Map interval to Alpha Vantage function
        function_map = {
            "1d": "TIME_SERIES_DAILY",
            "1wk": "TIME_SERIES_WEEKLY",
            "1mo": "TIME_SERIES_MONTHLY",
            "1h": "TIME_SERIES_INTRADAY",
            "5m": "TIME_SERIES_INTRADAY",
            "15m": "TIME_SERIES_INTRADAY",
        }
        
        function = function_map.get(interval, "TIME_SERIES_DAILY")
        
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "full"  # Get all available data
        }
        
        # Add interval param for intraday
        if function == "TIME_SERIES_INTRADAY":
            params["interval"] = self._normalize_intraday_interval(interval)
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
            
            if "Note" in data:
                raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
            
            # Check if we got time series data
            if not any(key.startswith("Time Series") for key in data.keys()):
                raise ValueError(f"No time series data in response: {list(data.keys())}")
            
            logger.info(
                "Alpha Vantage fetch successful",
                symbol=symbol
            )
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "Alpha Vantage fetch failed",
                symbol=symbol,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "Alpha Vantage processing failed",
                symbol=symbol,
                error=str(e)
            )
            raise

    @staticmethod
    def _normalize_intraday_interval(interval: str) -> str:
        mapping = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "60m": "60min",
        }
        return mapping.get(interval, interval)

