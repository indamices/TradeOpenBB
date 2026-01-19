"""
Redis 分布式缓存服务

功能：
- 分布式缓存（跨多实例共享）
- 持久化缓存（重启不丢失）
- 高性能缓存读写
- 缓存统计和监控

使用方式：
- 缓存 API 响应
- 缓存数据库查询结果
- 缓存外部数据（行情、历史数据）
"""

import redis
import json
import logging
import os
from typing import Optional, Any, List
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Redis 分布式缓存服务

    Benefits:
    - 持久化缓存（重启不丢失）
    - 跨实例共享（支持多实例部署）
    - 高容量（受 Redis 内存限制）
    - 高性能（毫秒级读写）
    """

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.redis = redis.from_url(
                redis_url,
                decode_responses=True,  # 自动解码 bytes 为字符串
                socket_timeout=5,  # 5 秒 socket 超时
                socket_connect_timeout=5,
                health_check_interval=30,  # 30 秒健康检查
                db=0  # 使用 DB 0
            )

            # 测试连接
            self.redis.ping()
            logger.info("✅ Redis 缓存连接成功")

        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}. 使用内存缓存回退。")
            self.redis = None

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取值

        Args:
            key: 缓存键

        Returns:
            缓存的值，如果不存在返回 None
        """
        if not self.redis:
            return None

        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET 错误: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 60):
        """
        设置值到缓存（带过期时间）

        Args:
            key: 缓存键
            value: 要缓存的值
            ttl: 过期时间（秒），默认 60 秒
        """
        if not self.redis:
            return

        try:
            serialized = json.dumps(value, ensure_ascii=False)
            self.redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis SET 错误: {e}")

    def delete(self, key: str):
        """
        删除缓存键

        Args:
            key: 缓存键
        """
        if not self.redis:
            return
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE 错误: {e}")

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            True 如果键存在
        """
        if not self.redis:
            return False
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS 错误: {e}")
            return False

    def clear_pattern(self, pattern: str):
        """
        清除匹配模式的所有键

        Args:
            pattern: 键模式（如 "quote:*"）

        Returns:
            清除的键数量
        """
        if not self.redis:
            return 0
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"清除了 {len(keys)} 个键匹配 {pattern}")
            return len(keys)
        except Exception as e:
            logger.error(f"Redis CLEAR_PATTERN 错误: {e}")
            return 0

    def get_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        if not self.redis:
            return {
                "status": "disconnected",
                "message": "Redis 未连接"
            }
        try:
            info = self.redis.info()
            return {
                "status": "connected",
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "used_memory_bytes": info.get("used_memory"),
                "total_keys": info.get("db0", {}).get("keys", 0),
                "uptime_days": info.get("uptime_in_days", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """
        批量获取多个键的值

        Args:
            keys: 键列表

        Returns:
            值列表
        """
        if not self.redis:
            return [None] * len(keys)

        try:
            values = self.redis.mget(keys)
            result = []
            for v in values:
                if v:
                    result.append(json.loads(v))
                else:
                    result.append(None)
            return result
        except Exception as e:
            logger.error(f"Redis MGET 错误: {e}")
            return [None] * len(keys)

    def mset(self, mapping: dict, ttl: int = 60):
        """
        批量设置多个键值对

        Args:
            mapping: 键值对字典
            ttl: 过期时间（秒）
        """
        if not self.redis:
            return

        try:
            pipe = self.redis.pipeline()
            for key, value in mapping.items():
                serialized = json.dumps(value, ensure_ascii=False)
                pipe.setex(key, ttl, serialized)
            pipe.execute()
        except Exception as e:
            logger.error(f"Redis MSET 错误: {e}")

    def increment(self, key: str, amount: int = 1) -> int:
        """
        原子递增计数器

        Args:
            key: 键
            amount: 递增量

        Returns:
            递增后的值
        """
        if not self.redis:
            return 0
        try:
            return self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR 错误: {e}")
            return 0

    def expire(self, key: str, ttl: int):
        """
        设置键的过期时间

        Args:
            key: 键
            ttl: 过期时间（秒）
        """
        if not self.redis:
            return
        try:
            self.redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE 错误: {e}")


# 全局 Redis 缓存实例
redis_cache = RedisCacheService()
