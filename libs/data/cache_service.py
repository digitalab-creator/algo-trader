"""
File-based cache service for market data

Pattern inspired by lotto-predictor's CacheService:
- JSON storage for readability
- MD5 key generation
- Automatic expiration
- Type-aware serialization
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class MarketDataCache:
    """
    File-based cache with automatic expiration.
    
    Each cache entry is stored as JSON with metadata:
    {
        "value": [...],  # List of NormalizedBar dicts
        "timestamp": "2025-01-10T10:30:00",
        "expires_at": "2025-01-12T10:30:00"
    }
    """
    
    def __init__(self, cache_dir: str | Path = "data/cache", expiration_days: int = 2):
        """
        Initialize cache service.
        
        Args:
            cache_dir: Directory for cache files
            expiration_days: Days before cache expires (default: 2)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expiration_days = expiration_days
        
        logger.info(
            "MarketDataCache initialized",
            cache_dir=str(self.cache_dir),
            expiration_days=expiration_days
        )
    
    def _generate_key(self, symbol: str, start: str, end: str, interval: str) -> str:
        """
        Generate cache key from parameters.
        
        Args:
            symbol: Ticker symbol
            start: Start date (ISO format)
            end: End date (ISO format)
            interval: Time interval (1m, 1h, 1d, etc.)
            
        Returns:
            MD5 hash as cache key
        """
        key_string = f"{symbol}:{start}:{end}:{interval}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{key}.json"
    
    def get(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1d"
    ) -> Optional[list[dict]]:
        """
        Get cached bars.
        
        Args:
            symbol: Ticker symbol
            start: Start date (ISO format)
            end: End date (ISO format)
            interval: Time interval
            
        Returns:
            List of NormalizedBar dicts if cached and not expired, None otherwise
        """
        key = self._generate_key(symbol, start, end, interval)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            logger.debug("Cache miss - file not found", symbol=symbol, key=key)
            return None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # Check expiration
            expires_at = datetime.fromisoformat(cache_data["expires_at"])
            if datetime.now() > expires_at:
                logger.debug(
                    "Cache miss - expired",
                    symbol=symbol,
                    expired_at=cache_data["expires_at"]
                )
                cache_path.unlink()  # Delete expired file
                return None
            
            logger.debug(
                "Cache hit",
                symbol=symbol,
                bars_count=len(cache_data["value"]),
                cached_at=cache_data["timestamp"]
            )
            return cache_data["value"]
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Cache read error, treating as miss", error=str(e), symbol=symbol)
            return None
    
    def set(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str,
        bars: list[dict]
    ) -> None:
        """
        Cache bars.
        
        Args:
            symbol: Ticker symbol
            start: Start date (ISO format)
            end: End date (ISO format)
            interval: Time interval
            bars: List of NormalizedBar dicts to cache
        """
        key = self._generate_key(symbol, start, end, interval)
        cache_path = self._get_cache_path(key)
        
        now = datetime.now()
        expires_at = now + timedelta(days=self.expiration_days)
        
        cache_data = {
            "value": bars,
            "timestamp": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "metadata": {
                "symbol": symbol,
                "start": start,
                "end": end,
                "interval": interval,
                "bars_count": len(bars)
            }
        }
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(
                "Cached successfully",
                symbol=symbol,
                bars_count=len(bars),
                expires_at=expires_at.isoformat()
            )
        except Exception as e:
            logger.error("Cache write error", error=str(e), symbol=symbol)
    
    def clear(self, symbol: Optional[str] = None) -> int:
        """
        Clear cache files.
        
        Args:
            symbol: If provided, only clear this symbol. Otherwise clear all.
            
        Returns:
            Number of files deleted
        """
        deleted = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            if symbol:
                # Check if file is for this symbol
                try:
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                    if data.get("metadata", {}).get("symbol") != symbol:
                        continue
                except Exception:
                    pass
            
            cache_file.unlink()
            deleted += 1
        
        logger.info("Cache cleared", files_deleted=deleted, symbol=symbol)
        return deleted
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache files.
        
        Returns:
            Number of files deleted
        """
        deleted = 0
        now = datetime.now()
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                
                expires_at = datetime.fromisoformat(data["expires_at"])
                if now > expires_at:
                    cache_file.unlink()
                    deleted += 1
            except Exception as e:
                logger.warning("Error checking cache file", file=str(cache_file), error=str(e))
        
        logger.info("Expired cache cleanup complete", files_deleted=deleted)
        return deleted

