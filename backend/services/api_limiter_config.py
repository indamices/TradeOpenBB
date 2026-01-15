"""
API Rate Limiting Configuration
保守配置：适用于免费版数据源（OpenBB 默认使用免费数据源）
"""
import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests_per_minute: int = 5  # 每分钟最多5次（免费版保守值）
    min_interval: float = 12.0  # 最小间隔12秒（60/5=12）
    batch_size: int = 1  # 免费版通常不支持批量，设为1
    batch_interval: float = 15.0  # 批次间隔15秒
    daily_limit: Optional[int] = 25  # 每日限制（如果有）
    warning_threshold: float = 0.8  # 警告阈值（80%）
    
@dataclass
class CacheConfig:
    """缓存配置"""
    quote_ttl: int = 60  # 报价缓存60秒（1分钟）
    historical_ttl: int = 86400  # 历史数据缓存24小时
    stock_info_ttl: int = 604800  # 股票信息缓存7天
    indicator_ttl: int = 1800  # 技术指标缓存30分钟

# 从环境变量读取配置，允许运行时调整
def get_rate_limit_config() -> RateLimitConfig:
    """获取速率限制配置（可从环境变量覆盖）"""
    daily_limit_str = os.getenv('API_DAILY_LIMIT', '25')
    daily_limit = int(daily_limit_str) if daily_limit_str else None
    
    return RateLimitConfig(
        requests_per_minute=int(os.getenv('API_REQUESTS_PER_MINUTE', '5')),
        min_interval=float(os.getenv('API_MIN_INTERVAL', '12.0')),
        batch_size=int(os.getenv('API_BATCH_SIZE', '1')),
        batch_interval=float(os.getenv('API_BATCH_INTERVAL', '15.0')),
        daily_limit=daily_limit,
        warning_threshold=float(os.getenv('API_WARNING_THRESHOLD', '0.8'))
    )

def get_cache_config() -> CacheConfig:
    """获取缓存配置（可从环境变量覆盖）"""
    return CacheConfig(
        quote_ttl=int(os.getenv('CACHE_QUOTE_TTL', '60')),
        historical_ttl=int(os.getenv('CACHE_HISTORICAL_TTL', '86400')),
        stock_info_ttl=int(os.getenv('CACHE_STOCK_INFO_TTL', '604800')),
        indicator_ttl=int(os.getenv('CACHE_INDICATOR_TTL', '1800'))
    )
