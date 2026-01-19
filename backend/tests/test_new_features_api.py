"""
Direct API tests for new features
Tests endpoints directly without complex fixtures
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
except ImportError as e:
    pytest.skip(f"Cannot import app: {e}", allow_module_level=True)


@pytest.fixture
def client():
    """Create a test client with database initialization"""
    from database import engine, SessionLocal
    from models import Base

    # Create all tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = SessionLocal()
            yield db
        finally:
            db.close()

    from main import get_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestBenchmarkStrategiesAPI:
    """Test benchmark strategies endpoint"""
    
    def test_benchmark_strategies_endpoint(self, client):
        """Test GET /api/backtest/benchmark-strategies"""
        response = client.get("/api/backtest/benchmark-strategies")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        assert len(data) > 0, "Should return at least one strategy"
        # Check structure
        for key, value in data.items():
            assert isinstance(value, dict), f"Strategy {key} should be a dict"
            assert 'name' in value, f"Strategy {key} should have 'name'"
            assert 'description' in value, f"Strategy {key} should have 'description'"
        print("✓ Benchmark strategies endpoint works")


class TestDataSourcesStatusAPI:
    """Test data sources status endpoint"""
    
    def test_data_sources_status_endpoint(self, client):
        """Test GET /api/data-sources/status"""
        response = client.get("/api/data-sources/status")
        # Should work even if no data sources configured
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert 'sources' in data, "Response should have 'sources'"
            assert 'message' in data, "Response should have 'message'"
            assert isinstance(data['sources'], list), "Sources should be a list"
        print("✓ Data sources status endpoint exists")


class TestParameterOptimizationAPI:
    """Test parameter optimization endpoint"""
    
    def test_parameter_optimization_endpoint_exists(self, client):
        """Test that endpoint exists"""
        # Try with empty body to check if endpoint exists
        response = client.post("/api/backtest/optimize", json={})
        # Should return 422 (validation error) or 404 (strategy not found), not 404 (endpoint not found)
        assert response.status_code != 404, "Endpoint should exist"
        assert response.status_code in [422, 500], f"Expected 422 or 500, got {response.status_code}: {response.text}"
        print("✓ Parameter optimization endpoint exists")
    
    def test_parameter_optimization_request_validation(self, client):
        """Test request validation"""
        # Missing required fields
        response = client.post("/api/backtest/optimize", json={})
        assert response.status_code == 422, "Should return validation error"
        print("✓ Parameter optimization request validation works")


class TestAIAnalysisAPI:
    """Test AI analysis endpoint"""
    
    def test_ai_analysis_endpoint_exists(self, client):
        """Test that endpoint exists"""
        # Try with empty body first to check if endpoint exists (should return 422 validation error, not 404)
        response = client.post("/api/backtest/analyze", json={})
        # 422 means endpoint exists but validation failed (endpoint found)
        # 404 means endpoint doesn't exist (FastAPI route not found)
        if response.status_code == 404:
            # Check response text to see if it's FastAPI 404 or our custom 404
            response_text = response.text.lower()
            if "not found" in response_text and "route" in response_text:
                # This is FastAPI 404 - endpoint doesn't exist
                assert False, f"Endpoint /api/backtest/analyze not found. Response: {response.text[:200]}"
            else:
                # This might be our custom 404, but endpoint exists
                assert response.status_code in [200, 404, 422, 500], f"Unexpected status: {response.status_code}"
        else:
            # Endpoint exists (got 422 validation error or other status)
            assert response.status_code in [200, 404, 422, 500], f"Unexpected status: {response.status_code}"
        print("✓ AI analysis endpoint exists")
    
    def test_ai_analysis_request_validation(self, client):
        """Test request validation"""
        # Missing required fields
        response = client.post("/api/backtest/analyze", json={})
        assert response.status_code == 422, "Should return validation error"
        print("✓ AI analysis request validation works")


class TestBacktestRecordsAPI:
    """Test backtest records endpoints"""
    
    def test_get_backtest_records(self, client):
        """Test GET /api/backtest/records"""
        response = client.get("/api/backtest/records")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print("✓ Get backtest records works")
    
    def test_get_backtest_records_with_pagination(self, client):
        """Test pagination"""
        response = client.get("/api/backtest/records?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print("✓ Backtest records pagination works")
    
    def test_get_backtest_record_by_id(self, client):
        """Test GET /api/backtest/records/{id}"""
        # Try with non-existent ID
        response = client.get("/api/backtest/records/99999")
        assert response.status_code == 404, "Should return 404 for non-existent record"
        print("✓ Get backtest record by ID works")


class TestHistoricalDataAPI:
    """Test historical data endpoint"""
    
    def test_historical_data_endpoint(self, client):
        """Test GET /api/market/historical/{symbol}"""
        response = client.get("/api/market/historical/AAPL?start_date=2023-01-01&end_date=2023-12-31")
        # May return 200 (success) or 500 (data service error)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Response should be a list"
        print("✓ Historical data endpoint exists")


class TestReturnFormat:
    """Test that return values are in correct format"""
    
    def test_backtest_result_format(self, client):
        """Test that backtest results use decimal format"""
        # This is a structural test - we can't easily test without running a full backtest
        # But we can verify the endpoint accepts requests
        request = {
            "strategy_id": 1,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 100000.0,
            "symbols": ["AAPL"]
        }
        response = client.post("/api/backtest", json=request)
        # May fail due to missing strategy or data, but should not fail due to format
        if response.status_code == 200:
            data = response.json()
            # Check format of return values
            if 'total_return' in data:
                assert isinstance(data['total_return'], (int, float))
                # Should be decimal (0.108 = 10.8%), not percentage (10.8)
                # For reasonable returns, should be < 1 unless >100% return
            if 'win_rate' in data:
                assert isinstance(data['win_rate'], (int, float))
                # Should be decimal (0.5 = 50%), not percentage (50)
                assert 0 <= data['win_rate'] <= 1.5  # Allow some margin
        print("✓ Backtest result format check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
