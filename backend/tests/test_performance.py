"""
Performance tests using pytest-benchmark
"""
import pytest
import time

def test_portfolio_creation_performance(client, benchmark):
    """Test portfolio creation performance"""
    data = {"name": "Perf Test", "initial_cash": 1000.0}
    
    def create_portfolio():
        return client.post("/api/portfolio", json=data)
    
    result = benchmark(create_portfolio)
    assert result.status_code == 201

def test_bulk_portfolio_creation(client):
    """Test creating multiple portfolios"""
    start_time = time.time()
    
    for i in range(10):
        data = {"name": f"Portfolio {i}", "initial_cash": 1000.0}
        response = client.post("/api/portfolio", json=data)
        assert response.status_code == 201
    
    elapsed = time.time() - start_time
    # Should complete 10 creations in reasonable time (< 5 seconds)
    assert elapsed < 5.0, f"Bulk creation took {elapsed:.2f} seconds"

def test_bulk_order_creation(client, sample_order_data):
    """Test creating multiple orders"""
    # First create a portfolio
    portfolio_data = {"name": "Test", "initial_cash": 100000.0}
    portfolio_resp = client.post("/api/portfolio", json=portfolio_data)
    assert portfolio_resp.status_code in [200, 201], f"Expected 200/201, got {portfolio_resp.status_code}: {portfolio_resp.text}"
    portfolio_id = portfolio_resp.json()["id"]
    
    start_time = time.time()
    
    for i in range(20):
        order_data = sample_order_data.copy()
        order_data["portfolio_id"] = portfolio_id
        order_data["symbol"] = f"STOCK{i}"
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 201
    
    elapsed = time.time() - start_time
    # Should complete 20 orders in reasonable time (< 10 seconds)
    assert elapsed < 10.0, f"Bulk order creation took {elapsed:.2f} seconds"

def test_query_performance(client):
    """Test query performance with multiple records"""
    # Create multiple portfolios
    for i in range(50):
        data = {"name": f"Portfolio {i}", "initial_cash": 1000.0}
        client.post("/api/portfolio", json=data)
    
    # Test query performance
    start_time = time.time()
    
    for _ in range(10):
        response = client.get("/api/portfolio?portfolio_id=1")
        assert response.status_code in [200, 404]
    
    elapsed = time.time() - start_time
    # Should complete 10 queries quickly (< 2 seconds)
    assert elapsed < 2.0, f"Query took {elapsed:.2f} seconds"

def test_concurrent_requests(client):
    """Test handling concurrent requests"""
    import concurrent.futures
    
    def create_portfolio(i):
        data = {"name": f"Concurrent {i}", "initial_cash": 1000.0}
        return client.post("/api/portfolio", json=data)
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_portfolio, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    elapsed = time.time() - start_time
    
    # All should succeed
    assert all(r.status_code == 201 for r in results)
    # Should complete in reasonable time
    assert elapsed < 10.0, f"Concurrent requests took {elapsed:.2f} seconds"

def test_large_response_handling(client):
    """Test handling large response data"""
    # Create many orders
    portfolio_data = {"name": "Test", "initial_cash": 100000.0}
    portfolio_resp = client.post("/api/portfolio", json=portfolio_data)
    assert portfolio_resp.status_code in [200, 201], f"Expected 200/201, got {portfolio_resp.status_code}: {portfolio_resp.text}"
    portfolio_id = portfolio_resp.json()["id"]
    
    # Create 100 orders
    for i in range(100):
        order_data = {
            "portfolio_id": portfolio_id,
            "symbol": f"STOCK{i}",
            "side": "BUY",
            "type": "MARKET",
            "quantity": 10
        }
        client.post("/api/orders", json=order_data)
    
    # Test querying all orders
    start_time = time.time()
    response = client.get(f"/api/orders?portfolio_id={portfolio_id}")
    elapsed = time.time() - start_time
    
    assert response.status_code == 200
    assert len(response.json()) == 100
    # Should complete quickly even with 100 records
    assert elapsed < 2.0, f"Large response query took {elapsed:.2f} seconds"
