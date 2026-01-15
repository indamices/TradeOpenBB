# API速率限制与缓存配置说明

## 概述

本系统已实现保守的API速率限制策略，适用于免费版数据源（OpenBB默认使用免费数据源）。

## 配置参数

### API速率限制配置

| 参数 | 默认值 | 说明 | 环境变量 |
|------|--------|------|----------|
| `requests_per_minute` | 5 | 每分钟最多请求次数（免费版） | `API_REQUESTS_PER_MINUTE` |
| `min_interval` | 12.0 | 单次请求最小间隔（秒） | `API_MIN_INTERVAL` |
| `batch_size` | 1 | 批量请求大小（免费版通常不支持批量） | `API_BATCH_SIZE` |
| `batch_interval` | 15.0 | 批次间隔（秒） | `API_BATCH_INTERVAL` |
| `daily_limit` | 25 | 每日请求限制 | `API_DAILY_LIMIT` |
| `warning_threshold` | 0.8 | 警告阈值（80%） | `API_WARNING_THRESHOLD` |

### 缓存配置

| 缓存类型 | 默认TTL | 说明 | 环境变量 |
|----------|---------|------|----------|
| 报价缓存 | 60秒 | 实时报价数据 | `CACHE_QUOTE_TTL` |
| 历史数据缓存 | 24小时 | 历史OHLCV数据 | `CACHE_HISTORICAL_TTL` |
| 股票信息缓存 | 7天 | 公司基本信息 | `CACHE_STOCK_INFO_TTL` |
| 技术指标缓存 | 30分钟 | 技术分析指标 | `CACHE_INDICATOR_TTL` |

## 自动降级机制

系统会在以下情况自动启用降级模式：

1. **达到警告阈值（80%）**：自动增加请求间隔至原来的2倍
2. **遇到429错误**：自动启用降级模式
3. **超过每日限制（100%）**：拒绝请求，等待第二天重置

## 监控API

### 获取速率限制状态

```bash
GET /api/admin/rate-limit-status
```

返回示例：
```json
{
  "daily_requests": 15,
  "daily_limit": 25,
  "usage_rate": 0.6,
  "degraded": false,
  "requests_per_minute": 2,
  "min_interval": 12.0,
  "batch_size": 1,
  "batch_interval": 15.0
}
```

### 重置每日计数（紧急情况）

```bash
POST /api/admin/reset-daily-limit
```

**注意**：仅在紧急情况下使用，不建议频繁重置。

## 环境变量配置示例

在 `backend/.env` 文件中添加以下配置：

```bash
# API速率限制配置
API_REQUESTS_PER_MINUTE=5
API_MIN_INTERVAL=12.0
API_BATCH_SIZE=1
API_BATCH_INTERVAL=15.0
API_DAILY_LIMIT=25
API_WARNING_THRESHOLD=0.8

# 缓存配置
CACHE_QUOTE_TTL=60
CACHE_HISTORICAL_TTL=86400
CACHE_STOCK_INFO_TTL=604800
CACHE_INDICATOR_TTL=1800
```

## 设计原则

1. **保守优先**：默认配置适用于最严格的免费版限制
2. **配置化**：所有参数可通过环境变量调整
3. **自动监控**：实时监控请求量，自动降级避免超限
4. **历史数据优先**：通过长TTL缓存减少API调用，符合"历史数据全面性 > 实时性"的要求

## 升级建议

如果升级到付费版数据源，可以调整以下参数：

```bash
# 付费版示例配置
API_REQUESTS_PER_MINUTE=60
API_MIN_INTERVAL=1.0
API_BATCH_SIZE=10
API_BATCH_INTERVAL=1.0
API_DAILY_LIMIT=10000
CACHE_QUOTE_TTL=5  # 更短的缓存以获取更实时数据
```
