"""
混合缓存服务：Redis (L1) + 内存 (L2 回退)

优先级：
1. Redis 缓存（持久化、跨实例共享）
2. 内存缓存（回退方案）

使用场景：
- 行情数据缓存
- 历史数据缓存
- 数据库查询结果缓存
- API 响应缓存
"""

import logging
from typing import Optional, Any
from cachetools import TTLCache

try:
    from .redis_cache import redis_cache
except ImportError:
    from services.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class HybridCacheService:
    """
    混合缓存服务

    L1: Redis 缓存（优先）
    - 持久化
    - 跨实例共享
    - 高容量

    L2: 内存缓存（回退）
    - 仅单实例
    - 不持久化
    - 低延迟
    """

    # L2: 内存回退缓存
    quote_cache = TTLCache(maxsize=100, ttl=60)  # 1分钟
    historical_cache = TTLCache(maxsize=50, ttl=3600)  # 1小时
    stock_info_cache = TTLCache(maxsize=200, ttl=86400)  # 1天

    @classmethod
    def get_quote(cls, symbol: str) -> Optional[Any]:
        """
        获取行情数据（优先 Redis，回退内存）

        Args:
            symbol: 股票代码

        Returns:
            缓存的行情数据
        """
        cache_key = f"quote:{symbol}"

        # 优先从 Redis 获取
        if redis_cache.redis:
            value = redis_cache.get(cache_key)
            if value is not None:
                logger.debug(f"Redis 缓存命中: {symbol}")
                return value

        # 回退到内存缓存
        value = cls.quote_cache.get(cache_key)
        if value is not None:
            logger.debug(f"内存缓存命中: {symbol}")
        return value

    @classmethod
    def set_quote(cls, symbol: str, value: Any, ttl: int = 60):
        """
        设置行情数据（同时存储到 Redis 和内存）

        Args:
            symbol: 股票代码
            value: 行情数据
            ttl: 过期时间（秒）
        """
        cache_key = f"quote:{symbol}"

        # 存储到 Redis
        if redis_cache.redis:
            redis_cache.set(cache_key, value, ttl)

        # 存储到内存缓存
        cls.quote_cache[cache_key] = value

    @classmethod
    def get_historical(cls, symbol: str, start_date: str, end_date: str) -> Optional[Any]:
        """
        获取历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            缓存的历史数据
        """
        cache_key = f"historical:{symbol}:{start_date}:{end_date}"

        # 优先从 Redis 获取
        if redis_cache.redis:
            value = redis_cache.get(cache_key)
            if value is not None:
                logger.debug(f"Redis 缓存命中: 历史数据 {symbol}")
                return value

        # 回退到内存缓存
        value = cls.historical_cache.get(cache_key)
        if value is not None:
            logger.debug(f"内存缓存命中: 历史数据 {symbol}")
        return value

    @classmethod
    def set_historical(cls, symbol: str, start_date: str, end_date: str, value: Any, ttl: int = 3600):
        """
        设置历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            value: 历史数据
            ttl: 过期时间（秒），默认 1 小时
        """
        cache_key = f"historical:{symbol}:{start_date}:{end_date}"

        # 存储到 Redis
        if redis_cache.redis:
            redis_cache.set(cache_key, value, ttl)

        # 存储到内存缓存
        cls.historical_cache[cache_key] = value

    @classmethod
    def get_stock_info(cls, symbol: str) -> Optional[Any]:
        """
        获取股票信息

        Args:
            symbol: 股票代码

        Returns:
            缓存的股票信息
        """
        cache_key = f"stock_info:{symbol}"

        # 优先从 Redis 获取
        if redis_cache.redis:
            value = redis_cache.get(cache_key)
            if value is not None:
                logger.debug(f"Redis 缓存命中: 股票信息 {symbol}")
                return value

        # 回退到内存缓存
        value = cls.stock_info_cache.get(cache_key)
        if value is not None:
            logger.debug(f"内存缓存命中: 股票信息 {symbol}")
        return value

    @classmethod
    def set_stock_info(cls, symbol: str, value: Any, ttl: int = 86400):
        """
        设置股票信息

        Args:
            symbol: 股票代码
            value: 股票信息
            ttl: 过期时间（秒），默认 1 天
        """
        cache_key = f"stock_info:{symbol}"

        # 存储到 Redis
        if redis_cache.redis:
            redis_cache.set(cache_key, value, ttl)

        # 存储到内存缓存
        cls.stock_info_cache[cache_key] = value

    @classmethod
    def invalidate_symbol(cls, symbol: str):
        """
        使股票的所有缓存失效

        Args:
            symbol: 股票代码
        """
        patterns = [
            f"quote:{symbol}",
            f"historical:{symbol}:*",
            f"stock_info:{symbol}"
        ]

        # 从 Redis 清除
        if redis_cache.redis:
            for pattern in patterns:
                if '*' in pattern:
                    redis_cache.clear_pattern(pattern.replace('*', '*'))
                else:
                    redis_cache.delete(pattern)

        # 从内存缓存清除
        try:
            del cls.quote_cache[f"quote:{symbol}"]
        except KeyError:
            pass

        logger.info(f"已清除 {symbol} 的所有缓存")

    @classmethod
    def get_cache_stats(cls) -> dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计
        """
        redis_stats = redis_cache.get_stats() if redis_cache.redis else {"status": "disconnected"}

        return {
            "redis": redis_stats,
            "memory": {
                "quote_cache_size": len(cls.quote_cache),
                "historical_cache_size": len(cls.historical_cache),
                "stock_info_cache_size": len(cls.stock_info_cache),
            }
        }


# 全局混合缓存实例
hybrid_cache = HybridCacheService()
