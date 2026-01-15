"""
Multi-level cache service for market data
L1: In-memory cache (TTLCache) - Fast access, short TTL
L2: Database cache - Persistent storage, long-term cache
配置化支持：可从环境变量调整TTL
"""
from cachetools import TTLCache
from datetime import datetime
from typing import Optional, Any
import logging

try:
    from .api_limiter_config import get_cache_config
except ImportError:
    from services.api_limiter_config import get_cache_config

logger = logging.getLogger(__name__)

# 获取缓存配置
_cache_config = get_cache_config()


def get_cache_key(prefix: str, **kwargs) -> str:
    """Generate a unified cache key format"""
    parts = [prefix]
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}:{v}")
    return "|".join(parts)


class CacheService:
    """
    Multi-level cache service (使用配置化的TTL)
    
    L1: In-memory cache (TTLCache)
    - Quote cache: 60秒TTL（1分钟，保守配置减少API调用）
    - Historical cache: 24小时TTL（历史数据变化不频繁）
    - Stock info cache: 7天TTL（公司信息很少变化）
    - Indicator cache: 30分钟TTL
    """
    
    # L1: In-memory caches（使用配置的TTL）
    quote_cache = TTLCache(maxsize=1000, ttl=_cache_config.quote_ttl)  # Real-time quotes
    historical_cache = TTLCache(maxsize=500, ttl=_cache_config.historical_ttl)  # Historical data
    stock_info_cache = TTLCache(maxsize=2000, ttl=_cache_config.stock_info_ttl)  # Stock info
    indicator_cache = TTLCache(maxsize=300, ttl=_cache_config.indicator_ttl)  # Technical indicators
    
    @classmethod
    def get_quote(cls, symbol: str) -> Optional[Any]:
        """Get quote from L1 cache"""
        cache_key = get_cache_key("quote", symbol=symbol)
        return cls.quote_cache.get(cache_key)
    
    @classmethod
    def set_quote(cls, symbol: str, value: Any):
        """Set quote in L1 cache"""
        cache_key = get_cache_key("quote", symbol=symbol)
        cls.quote_cache[cache_key] = value
    
    @classmethod
    def get_historical(cls, symbol: str, start_date: str, end_date: str) -> Optional[Any]:
        """Get historical data from L1 cache"""
        cache_key = get_cache_key("historical", symbol=symbol, start=start_date, end=end_date)
        return cls.historical_cache.get(cache_key)
    
    @classmethod
    def set_historical(cls, symbol: str, start_date: str, end_date: str, value: Any):
        """Set historical data in L1 cache"""
        cache_key = get_cache_key("historical", symbol=symbol, start=start_date, end=end_date)
        cls.historical_cache[cache_key] = value
    
    @classmethod
    def get_stock_info(cls, symbol: str) -> Optional[Any]:
        """Get stock info from L1 cache"""
        cache_key = get_cache_key("stock_info", symbol=symbol)
        return cls.stock_info_cache.get(cache_key)
    
    @classmethod
    def set_stock_info(cls, symbol: str, value: Any):
        """Set stock info in L1 cache"""
        cache_key = get_cache_key("stock_info", symbol=symbol)
        cls.stock_info_cache[cache_key] = value
    
    @classmethod
    def get_indicator(cls, symbol: str, indicators: str, period: int) -> Optional[Any]:
        """Get indicator from L1 cache"""
        cache_key = get_cache_key("indicator", symbol=symbol, indicators=indicators, period=period)
        return cls.indicator_cache.get(cache_key)
    
    @classmethod
    def set_indicator(cls, symbol: str, indicators: str, period: int, value: Any):
        """Set indicator in L1 cache"""
        cache_key = get_cache_key("indicator", symbol=symbol, indicators=indicators, period=period)
        cls.indicator_cache[cache_key] = value
    
    @classmethod
    def clear_cache(cls, cache_type: Optional[str] = None):
        """Clear cache(s)"""
        if cache_type is None:
            cls.quote_cache.clear()
            cls.historical_cache.clear()
            cls.stock_info_cache.clear()
            cls.indicator_cache.clear()
        elif cache_type == "quote":
            cls.quote_cache.clear()
        elif cache_type == "historical":
            cls.historical_cache.clear()
        elif cache_type == "stock_info":
            cls.stock_info_cache.clear()
        elif cache_type == "indicator":
            cls.indicator_cache.clear()
