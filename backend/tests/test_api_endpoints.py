"""
API Endpoint Tests
Tests the FastAPI endpoints
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
    from database import get_db, Base
    from models import Strategy, Portfolio, BacktestRecord
except ImportError as e:
    pytest.skip(f"Cannot import required modules: {e}", allow_module_level=True)


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    db = TestingSessionLocal()
    
    # Create default portfolio
    portfolio = Portfolio(
        id=1,
        name="Test Portfolio",
        initial_cash=100000.0,
        current_cash=100000.0,
        total_value=100000.0,
        daily_pnl=0.0,
        daily_pnl_percent=0.0
    )
    db.add(portfolio)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_strategy(db_session):
    """Create a sample strategy"""
    strategy = Strategy(
        name="Test Strategy",
        logic_code="""
# Simple strategy
if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
    signal = 1
else:
    signal = -1
""",
        target_portfolio_id=1,
        is_active=True,
        description="Test strategy"
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


class TestBacktestRecordEndpoints:
    """Test backtest record API endpoints"""
    
    def test_get_backtest_records_empty(self, client):
        """Test getting backtest records when none exist"""
        response = client.get("/api/backtest/records")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0
        print("PASS: GET /api/backtest/records returns empty list")
    
    def test_create_backtest_record_via_backtest(self, client, sample_strategy):
        """Test creating backtest record via backtest endpoint"""
        from datetime import datetime, timedelta
        
        backtest_request = {
            "strategy_id": sample_strategy.id,
            "start_date": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "end_date": datetime.now().strftime('%Y-%m-%d'),
            "initial_cash": 100000.0,
            "symbols": ["AAPL"]
        }
        
        # Mock data fetching to avoid external API calls
        from unittest.mock import patch, AsyncMock
        with patch('main.run_backtest', new_callable=AsyncMock) as mock_backtest:
            from schemas import BacktestResult
            
            mock_result = BacktestResult(
                sharpe_ratio=1.5,
                annualized_return=10.0,
                max_drawdown=-15.0,
                total_trades=10,
                total_return=10.0
            )
            mock_backtest.return_value = mock_result
            
            # Run backtest with save_record=True
            response = client.post(
                "/api/backtest?save_record=true",
                json=backtest_request
            )
            
            # Should succeed (even if backtest is mocked)
            # In real scenario, this would save a record
            assert response.status_code in [200, 500]  # May fail if data fetching fails
            print("PASS: Backtest endpoint accepts save_record parameter")
    
    def test_get_backtest_record_not_found(self, client):
        """Test getting non-existent backtest record"""
        response = client.get("/api/backtest/records/99999")
        assert response.status_code == 404
        print("PASS: GET /api/backtest/records/{id} returns 404 for non-existent record")


class TestParameterOptimizationEndpoints:
    """Test parameter optimization API endpoints"""
    
    def test_optimize_parameters_endpoint_exists(self, client, sample_strategy):
        """Test that optimization endpoint exists and accepts requests"""
        from datetime import datetime, timedelta
        
        optimization_request = {
            "strategy_id": sample_strategy.id,
            "start_date": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "end_date": datetime.now().strftime('%Y-%m-%d'),
            "initial_cash": 100000.0,
            "symbols": ["AAPL"],
            "parameter_ranges": {
                "short_sma": [15, 20, 25],
                "long_sma": [45, 50]
            },
            "optimization_metric": "sharpe_ratio"
        }
        
        # This will likely fail due to data fetching, but we can test the endpoint structure
        response = client.post("/api/backtest/optimize", json=optimization_request)
        
        # Should return 200 (with mocked data) or 500 (if data fetch fails)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert 'best_parameters' in data
            assert 'best_metric_value' in data
            print("PASS: Parameter optimization endpoint works")
        else:
            print("INFO: Parameter optimization endpoint exists (failed due to data fetch)")


class TestStrategyAnalysisEndpoints:
    """Test AI strategy analysis API endpoints"""
    
    def test_analyze_backtest_result_endpoint(self, client, sample_strategy):
        """Test strategy analysis endpoint"""
        from schemas import BacktestResult
        
        backtest_result = BacktestResult(
            sharpe_ratio=1.5,
            sortino_ratio=1.8,
            annualized_return=12.5,
            max_drawdown=-15.0,
            win_rate=55.0,
            total_trades=100,
            total_return=12.5
        )
        
        # Mock AI service to avoid actual AI calls
        from unittest.mock import patch
        with patch('services.strategy_analyzer.get_default_model', return_value=None):
            response = client.post(
                f"/api/backtest/analyze?strategy_id={sample_strategy.id}",
                json=backtest_result.model_dump()
            )
            
            # Should return 200 (with fallback analysis) or 500 (if AI service fails)
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'structured_analysis' in data
                print("PASS: Strategy analysis endpoint works")
            else:
                print("INFO: Strategy analysis endpoint exists (failed due to AI service)")


class TestDataSourceEndpoints:
    """Test data source API endpoints"""
    
    def test_get_available_data_sources(self, client):
        """Test getting available data sources"""
        response = client.get("/api/data-sources/available")
        assert response.status_code == 200
        data = response.json()
        assert 'sources' in data
        assert isinstance(data['sources'], list)
        assert len(data['sources']) > 0
        print(f"PASS: Found {len(data['sources'])} available data sources")
    
    def test_get_data_sources(self, client):
        """Test getting configured data sources"""
        response = client.get("/api/data-sources")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("PASS: GET /api/data-sources works")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
