"""
增强的API速率限制器
支持每日请求量监控和自动降级机制
保守配置：适用于免费版数据源（OpenBB 默认使用免费数据源）
"""
import asyncio
from datetime import datetime, timedelta, date
from collections import deque
from typing import List, Callable, Any, Coroutine, Optional, Dict, Tuple
import logging
from sqlalchemy.orm import Session

try:
    from .api_limiter_config import get_rate_limit_config, RateLimitConfig
    from ..database import SessionLocal
except ImportError:
    from services.api_limiter_config import get_rate_limit_config, RateLimitConfig
    from database import SessionLocal

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    增强的API调用速率限制器
    - 单次请求间隔：≥12秒（免费版：每分钟5次）
    - 批量请求：每批≤1个（免费版通常不支持批量）
    - 批次间隔：≥15秒
    - 每日请求量监控
    - 自动降级机制
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None, db: Optional[Session] = None):
        """
        Initialize enhanced rate limiter
        
        Args:
            config: Rate limit configuration (default: from config file)
            db: Database session for logging (optional)
        """
        self.config = config or get_rate_limit_config()
        self.db = db
        self.request_times = deque()  # 滑动窗口：最近1分钟的请求时间
        self.daily_requests: Dict[date, int] = {}  # 每日请求计数
        
        # 降级状态
        self.degraded = False  # 是否处于降级模式
        self.degraded_multiplier = 2.0  # 降级时的时间间隔倍数
        
    def _get_today(self) -> date:
        """获取今天的日期"""
        return datetime.now().date()
    
    def _get_daily_request_count(self, target_date: Optional[date] = None) -> int:
        """获取指定日期的请求计数"""
        if target_date is None:
            target_date = self._get_today()
        return self.daily_requests.get(target_date, 0)
    
    def _increment_daily_count(self):
        """增加今日请求计数"""
        today = self._get_today()
        self.daily_requests[today] = self.daily_requests.get(today, 0) + 1
        
        # 清理7天前的记录
        week_ago = today - timedelta(days=7)
        self.daily_requests = {
            d: c for d, c in self.daily_requests.items() 
            if d >= week_ago
        }
    
    def _check_daily_limit(self) -> Tuple[bool, float]:
        """
        检查每日限制
        
        Returns:
            (是否超过限制, 使用率百分比)
        """
        if self.config.daily_limit is None:
            return False, 0.0
        
        today = self._get_today()
        count = self._get_daily_request_count(today)
        usage_rate = count / self.config.daily_limit if self.config.daily_limit > 0 else 0.0
        
        # 检查是否超过警告阈值
        if usage_rate >= self.config.warning_threshold:
            logger.warning(
                f"Daily request limit warning: {count}/{self.config.daily_limit} "
                f"({usage_rate*100:.1f}%)"
            )
            
            # 如果超过阈值，启用降级模式
            if not self.degraded and usage_rate >= self.config.warning_threshold:
                self.degraded = True
                logger.warning("Rate limiter entered degraded mode (slower requests)")
        
        # 检查是否超过每日限制
        if count >= self.config.daily_limit:
            return True, usage_rate
        
        return False, usage_rate
    
    async def wait_if_needed(self):
        """等待以避免超过速率限制（考虑降级模式）"""
        now = datetime.now()
        
        # 检查每日限制
        exceeded, usage_rate = self._check_daily_limit()
        if exceeded:
            wait_until_tomorrow = (
                (self._get_today() + timedelta(days=1)).replace(hour=0, minute=0, second=0) 
                - now
            ).total_seconds()
            logger.error(
                f"Daily request limit exceeded! "
                f"Waiting until tomorrow ({wait_until_tomorrow/3600:.1f} hours)"
            )
            raise ValueError(
                f"Daily API request limit ({self.config.daily_limit}) exceeded. "
                f"Please try again tomorrow or upgrade your plan."
            )
        
        # 移除1分钟前的记录
        while self.request_times and (now - self.request_times[0]).total_seconds() > 60:
            self.request_times.popleft()
        
        # 计算实际间隔（降级模式时增加间隔）
        actual_interval = self.config.min_interval
        if self.degraded:
            actual_interval *= self.degraded_multiplier
            logger.debug(f"Degraded mode: using interval {actual_interval}s")
        
        # 如果最近一次请求在间隔内，等待
        if self.request_times:
            last_request = self.request_times[-1]
            elapsed = (now - last_request).total_seconds()
            if elapsed < actual_interval:
                wait_time = actual_interval - elapsed
                logger.debug(f"Rate limiter: waiting {wait_time:.2f}s before next request")
                await asyncio.sleep(wait_time)
        
        # 记录请求时间
        self.request_times.append(datetime.now())
        self._increment_daily_count()
    
    async def batch_fetch(
        self, 
        items: List[Any], 
        fetch_func: Callable[[Any], Coroutine[Any, Any, Any]]
    ) -> List[Any]:
        """
        批量获取数据（考虑免费版限制，批次大小为1）
        
        Args:
            items: List of items to fetch
            fetch_func: Async function to fetch data for each item
        
        Returns:
            List of results (may include exceptions)
        """
        results = []
        batch_size = self.config.batch_size
        
        # 免费版：每批只处理1个，避免触发批量限制
        total_batches = (len(items) + batch_size - 1) // batch_size
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            # 等待批次间隔（除了第一个批次）
            if i > 0:
                actual_interval = self.config.batch_interval
                if self.degraded:
                    actual_interval *= self.degraded_multiplier
                
                logger.debug(
                    f"Rate limiter: waiting {actual_interval}s before batch "
                    f"{batch_num}/{total_batches}"
                )
                await asyncio.sleep(actual_interval)
            
            # 处理批次（免费版时每批只有1个）
            for item in batch:
                result = await self._fetch_with_rate_limit(item, fetch_func)
                results.append(result)
            
            logger.debug(
                f"Rate limiter: completed batch {batch_num}/{total_batches} "
                f"({len(batch)} items)"
            )
        
        return results
    
    async def _fetch_with_rate_limit(self, item: Any, fetch_func: Callable[[Any], Coroutine[Any, Any, Any]]):
        """获取单个项目（带速率限制）"""
        await self.wait_if_needed()
        try:
            return await fetch_func(item)
        except Exception as e:
            error_msg = str(e).lower()
            # 如果遇到429错误，进入降级模式
            if "429" in error_msg or "rate limit" in error_msg:
                if not self.degraded:
                    self.degraded = True
                    logger.warning("Rate limit error detected, entering degraded mode")
            raise
    
    def get_status(self) -> dict:
        """获取当前状态（用于监控）"""
        today = self._get_today()
        daily_count = self._get_daily_request_count(today)
        
        return {
            'daily_requests': daily_count,
            'daily_limit': self.config.daily_limit,
            'usage_rate': daily_count / self.config.daily_limit if self.config.daily_limit else 0.0,
            'degraded': self.degraded,
            'requests_per_minute': len(self.request_times),
            'min_interval': self.config.min_interval * (self.degraded_multiplier if self.degraded else 1.0),
            'batch_size': self.config.batch_size,
            'batch_interval': self.config.batch_interval
        }
    
    def reset_daily_count(self):
        """重置每日计数（用于测试或手动重置）"""
        self.daily_requests.clear()
        self.degraded = False
        logger.info("Daily request count reset")


# Global rate limiter instance
rate_limiter = RateLimiter()
