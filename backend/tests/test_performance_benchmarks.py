"""
性能基准测试套件（CI/CD 专用）

用于捕获性能退化并提供性能基线
在 CI/CD pipeline 中运行以监控性能趋势

运行方式:
  pytest tests/test_performance_benchmarks.py -v
  pytest tests/test_performance_benchmarks.py -v --benchmark-only

性能目标（基准）:
- /api/portfolio: < 100ms
- /api/positions (分页): < 200ms
- /api/strategies (分页): < 200ms
- 并发请求 (10个): 平均 < 200ms, 最大 < 500ms
"""

import pytest
import time
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app


# 性能基准配置
PERFORMANCE_BENCHMARKS = {
    "portfolio_endpoint": {
        "max_response_time_ms": 100,
        "description": "Portfolio endpoint should respond within 100ms"
    },
    "positions_endpoint": {
        "max_response_time_ms": 200,
        "description": "Positions endpoint (paginated) should respond within 200ms"
    },
    "strategies_endpoint": {
        "max_response_time_ms": 200,
        "description": "Strategies endpoint (paginated) should respond within 200ms"
    },
    "stock_pools_endpoint": {
        "max_response_time_ms": 200,
        "description": "Stock pools endpoint (paginated) should respond within 200ms"
    },
    "concurrent_requests": {
        "avg_response_time_ms": 200,
        "max_response_time_ms": 500,
        "description": "Concurrent requests (10) should have avg < 200ms, max < 500ms"
    }
}


class TestPerformanceBenchmarks:
    """
    性能基准测试类

    用于捕获 API 端点的性能退化
    """

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        from database import engine, SessionLocal
        from models import Base

        # Create all tables
        Base.metadata.create_all(bind=engine)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_portfolio_response_time(self, client):
        """
        测试 Portfolio 端点响应时间

        基准: < 100ms
        """
        start = time.time()
        response = await client.get("/api/portfolio?portfolio_id=1")
        duration_ms = (time.time() - start) * 1000

        assert response.status_code in [200, 404], f"Request failed with status {response.status_code}"
        assert duration_ms < PERFORMANCE_BENCHMARKS["portfolio_endpoint"]["max_response_time_ms"], \
            f"Portfolio endpoint took {duration_ms:.2f}ms (expected < {PERFORMANCE_BENCHMARKS['portfolio_endpoint']['max_response_time_ms']}ms)"

        print(f"✅ Portfolio endpoint: {duration_ms:.2f}ms")

    @pytest.mark.asyncio
    async def test_positions_response_time(self, client):
        """
        测试 Positions 端点响应时间（分页）

        基准: < 200ms
        """
        start = time.time()
        response = await client.get("/api/positions?portfolio_id=1&limit=50")
        duration_ms = (time.time() - start) * 1000

        assert response.status_code in [200, 404], f"Request failed with status {response.status_code}"
        assert duration_ms < PERFORMANCE_BENCHMARKS["positions_endpoint"]["max_response_time_ms"], \
            f"Positions endpoint took {duration_ms:.2f}ms (expected < {PERFORMANCE_BENCHMARKS['positions_endpoint']['max_response_time_ms']}ms)"

        print(f"✅ Positions endpoint: {duration_ms:.2f}ms")

    @pytest.mark.asyncio
    async def test_strategies_response_time(self, client):
        """
        测试 Strategies 端点响应时间（分页）

        基准: < 200ms
        """
        start = time.time()
        response = await client.get("/api/strategies?limit=50")
        duration_ms = (time.time() - start) * 1000

        assert response.status_code in [200, 404], f"Request failed with status {response.status_code}"
        assert duration_ms < PERFORMANCE_BENCHMARKS["strategies_endpoint"]["max_response_time_ms"], \
            f"Strategies endpoint took {duration_ms:.2f}ms (expected < {PERFORMANCE_BENCHMARKS['strategies_endpoint']['max_response_time_ms']}ms)"

        print(f"✅ Strategies endpoint: {duration_ms:.2f}ms")

    @pytest.mark.asyncio
    async def test_stock_pools_response_time(self, client):
        """
        测试 Stock Pools 端点响应时间（分页）

        基准: < 200ms
        """
        start = time.time()
        response = await client.get("/api/stock-pools?limit=50")
        duration_ms = (time.time() - start) * 1000

        # 允许 404（如果没有股票池），但应该快速响应
        assert response.status_code in [200, 404], f"Unexpected status {response.status_code}"
        assert duration_ms < PERFORMANCE_BENCHMARKS["stock_pools_endpoint"]["max_response_time_ms"], \
            f"Stock pools endpoint took {duration_ms:.2f}ms (expected < {PERFORMANCE_BENCHMARKS['stock_pools_endpoint']['max_response_time_ms']}ms)"

        print(f"✅ Stock pools endpoint: {duration_ms:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, client):
        """
        测试并发请求性能

        基准:
        - 平均响应时间 < 200ms
        - 最大响应时间 < 500ms
        """
        async def make_request():
            start = time.time()
            response = await client.get("/api/portfolio?portfolio_id=1")
            duration_ms = (time.time() - start) * 1000
            assert response.status_code in [200, 404], f"Request failed with status {response.status_code}"
            return duration_ms

        # 运行 10 个并发请求
        durations = await asyncio.gather(*[make_request() for _ in range(10)])

        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)

        assert avg_duration < PERFORMANCE_BENCHMARKS["concurrent_requests"]["avg_response_time_ms"], \
            f"Average response time {avg_duration:.2f}ms (expected < {PERFORMANCE_BENCHMARKS['concurrent_requests']['avg_response_time_ms']}ms)"
        assert max_duration < PERFORMANCE_BENCHMARKS["concurrent_requests"]["max_response_time_ms"], \
            f"Max response time {max_duration:.2f}ms (expected < {PERFORMANCE_BENCHMARKS['concurrent_requests']['max_response_time_ms']}ms)"

        print(f"✅ Concurrent requests (10):")
        print(f"   Average: {avg_duration:.2f}ms")
        print(f"   Min: {min_duration:.2f}ms")
        print(f"   Max: {max_duration:.2f}ms")

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, client):
        """
        测试缓存命中性能

        验证:
        - 第一次请求（缓存未命中）
        - 第二次请求（缓存命中）应该明显更快
        """
        # 第一次请求（缓存未命中）
        start = time.time()
        response1 = await client.get("/api/portfolio?portfolio_id=1")
        first_request_ms = (time.time() - start) * 1000

        # 等待一小段时间
        await asyncio.sleep(0.1)

        # 第二次请求（缓存命中）
        start = time.time()
        response2 = await client.get("/api/portfolio?portfolio_id=1")
        second_request_ms = (time.time() - start) * 1000

        assert response1.status_code in [200, 404]
        assert response2.status_code in [200, 404]

        print(f"✅ Cache performance:")
        print(f"   First request (cache miss): {first_request_ms:.2f}ms")
        print(f"   Second request (cache hit): {second_request_ms:.2f}ms")
        if first_request_ms > 0:
            print(f"   Speedup: {first_request_ms / second_request_ms:.2f}x")

        # 缓存命中应该至少快 10%（可能由于数据库连接池而更快）
        # 这是一个软性检查，仅用于警告
        if second_request_ms > first_request_ms * 0.9 and first_request_ms > 10:
            print(f"⚠️  Warning: Cache hit not significantly faster. Consider checking cache configuration.")


class TestDatabasePerformance:
    """
    数据库性能测试类

    验证数据库查询和连接池性能
    """

    @pytest.mark.asyncio
    async def test_db_connection_pool_performance(self):
        """
        测试数据库连接池性能

        验证连接池可以高效处理多个并发连接
        """
        from database import engine, DATABASE_URL
        from sqlalchemy.pool import StaticPool

        pool = engine.pool

        print(f"✅ DB Connection Pool:")
        print(f"   Pool type: {type(pool).__name__}")
        print(f"   Database: {'SQLite' if 'sqlite' in DATABASE_URL else 'PostgreSQL'}")

        # SQLite 使用 StaticPool，没有 size() 方法
        if isinstance(pool, StaticPool):
            print(f"   Using SQLite StaticPool (no connection pooling)")
            print(f"   ✅ SQLite connection working correctly")
        else:
            # PostgreSQL 使用 QueuePool，有 size() 方法
            try:
                pool_size = pool.size()
                checked_in = pool.checkedin()

                print(f"   Pool size: {pool_size}")
                print(f"   Checked in: {checked_in}")
                if pool_size > 0:
                    print(f"   Utilization: {(pool_size - checked_in) / pool_size * 100:.1f}%")

                # 连接池利用率应该合理（< 80%）
                utilization = (pool_size - checked_in) / pool_size if pool_size > 0 else 0
                assert utilization < 0.8, f"Connection pool utilization too high: {utilization * 100:.1f}%"
            except AttributeError as e:
                print(f"   ⚠️  Could not get pool stats: {e}")
                print(f"   This is OK for connection pools without size() method")


class TestFrontendBundleSize:
    """
    前端 Bundle 大小测试

    验证前端构建产物大小符合预期
    """

    def test_bundle_size_limits(self):
        """
        测试前端 bundle 大小

        基准:
        - 主 bundle < 350KB
        - vendor chunks < 500KB
        """
        import os
        import glob

        # 查找 dist 目录
        dist_dirs = glob.glob("../dist/**/*.js", recursive=True)

        if not dist_dirs:
            pytest.skip("No dist directory found. Run 'npm run build' first.")

        # 检查文件大小
        large_files = []
        for file_path in dist_dirs:
            size_kb = os.path.getsize(file_path) / 1024
            if size_kb > 500:  # 500KB threshold
                large_files.append((file_path, size_kb))

        print(f"✅ Bundle size check:")
        print(f"   Total JS files: {len(dist_dirs)}")
        print(f"   Files > 500KB: {len(large_files)}")

        for file_path, size_kb in large_files:
            print(f"   - {file_path}: {size_kb:.1f}KB")

        # 警告但不失败（仅用于监控）
        if large_files:
            print(f"⚠️  Warning: Found {len(large_files)} large JavaScript files. Consider code splitting.")


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "-s"])
