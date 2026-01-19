"""
结构化日志和监控系统

功能：
- 统一的日志格式
- 性能监控
- 错误追踪
- 请求追踪
- 缓存命中率统计
"""

import logging
import time
import functools
from typing import Callable, Optional
from datetime import datetime
from fastapi import Request
import json

# 配置结构化日志
def setup_logging():
    """
    设置结构化日志

    格式：时间 | 级别 | 模块 | 消息
    """
    logger = logging.getLogger("tradeopenbb")
    logger.setLevel(logging.INFO)

    # 清除现有的处理器
    logger.handlers.clear()

    # 控制台处理器（带颜色）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    console_handler.setLevel(logging.INFO)

    # 文件处理器（轮转，JSON 格式）
    from logging.handlers import RotatingFileHandler

    try:
        file_handler = RotatingFileHandler(
            'logs/tradeopenbb.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
            )
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        logger.addHandler(file_handler)
    except Exception as e:
        # 如果无法创建文件日志，仅使用控制台
        logger.warning(f"无法创建文件日志: {e}")

    logger.addHandler(console_handler)

    return logger


# 请求计时中间件
async def log_requests_middleware(request: Request, call_next):
    """
    记录所有请求及耗时

    格式：
    ➡️  GET /api/positions
    ⬅️  GET /api/positions | 200 | 45.23ms
    """
    start_time = time.time()

    # 记录请求
    logger.info(f"➡️  {request.method} {request.url.path}")

    # 处理请求
    response = await call_next(request)

    # 计算耗时
    duration = time.time() - start_time

    # 记录响应
    logger.info(
        f"⬅️  {request.method} {request.url.path} "
        f"| {response.status_code} | {duration*1000:.2f}ms"
    )

    # 添加性能头
    response.headers["X-Process-Time"] = f"{duration:.3f}"

    # 记录慢请求（>1秒）
    if duration > 1.0:
        logger.warning(f"⚠️  慢请求: {request.method} {request.url.path} 耗时 {duration:.2f}s")

    return response


# 性能监控装饰器
def monitor_performance(func: Callable) -> Callable:
    """
    性能监控装饰器

    用于监控关键函数的执行时间

    使用：
    @monitor_performance
    async def my_function():
        # ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(f"✅ {func_name} 完成 | 耗时: {duration:.2f}s")

            # 记录慢操作（>500ms）
            if duration > 0.5:
                logger.warning(f"⚠️  慢操作: {func_name} 耗时 {duration:.2f}s")

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {func_name} 失败 | 耗时: {duration:.2f}s | 错误: {str(e)}")
            raise

    return wrapper


# 指标收集类
class Metrics:
    """
    简单的内存指标收集

    生产环境建议使用 Prometheus + Grafana
    """
    def __init__(self):
        self.request_count = {}
        self.response_times = {}
        self.error_count = {}
        self.slow_requests = []  # 耗时请求（>1秒）
        self.cache_hits = 0
        self.cache_misses = 0

    def record_request(
        self,
        endpoint: str,
        duration: float,
        status_code: int,
        is_cached: bool = False
    ):
        """记录请求指标"""
        # 请求计数
        if endpoint not in self.request_count:
            self.request_count[endpoint] = 0
        self.request_count[endpoint] += 1

        # 响应时间
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        self.response_times[endpoint].append(duration)

        # 错误计数
        if status_code >= 400:
            if endpoint not in self.error_count:
                self.error_count[endpoint] = 0
            self.error_count[endpoint] += 1

        # 慢请求记录
        if duration > 1.0:
            self.slow_requests.append({
                "endpoint": endpoint,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })

        # 缓存命中
        if is_cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_metrics(self) -> dict:
        """获取收集的指标"""
        stats = {}

        for endpoint in self.request_count:
            response_times = self.response_times.get(endpoint, [])

            if response_times:
                stats[endpoint] = {
                    "request_count": self.request_count[endpoint],
                    "avg_response_time_ms": sum(response_times) / len(response_times) * 1000,
                    "min_response_time_ms": min(response_times) * 1000,
                    "max_response_time_ms": max(response_times) * 1000,
                    "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)] * 1000 if len(response_times) > 0 else 0,
                    "error_count": self.error_count.get(endpoint, 0),
                }

        # 缓存命中率
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops > 0:
            stats["cache"] = {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate_percent": (self.cache_hits / total_cache_ops) * 100
            }

        # 慢请求
        if self.slow_requests:
            stats["slow_requests"] = {
                "count": len(self.slow_requests),
                "requests": self.slow_requests[-10:]  # 最近 10 个
            }

        return stats

    def get_slow_requests(self, limit: int = 10) -> list:
        """获取慢请求列表"""
        return self.slow_requests[-limit:]


# 全局指标实例
metrics = Metrics()


# 结构化日志助手
def log_structured(level: str, event: str, **kwargs):
    """
    记录结构化日志

    Args:
        level: 日志级别（info, warning, error）
        event: 事件名称
        **kwargs: 事件数据
    """
    logger_func = getattr(logger, level.lower(), logger.info)
    log_data = {
        "event": event,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }

    logger_func(json.dumps(log_data, ensure_ascii=False))
