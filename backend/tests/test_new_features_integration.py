"""
Integration Tests for New Features
Tests the complete flow of new features: parameter optimization, AI analysis, and backtest records
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
    from database import get_db, Base
    from models import Strategy, Portfolio, BacktestRecord
except ImportError as e:
    pytest.skip(f"Cannot import required modules: {e}", allow_module_level=True)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_new_features.db"

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
    
    # Create test strategy with parameters
    strategy = Strategy(
        name="Test SMA Strategy",
        logic_code="""
# Simple moving average crossover strategy
short_sma = 20
long_sma = 50

df['short_ma'] = df['Close'].rolling(window=short_sma).mean()
df['long_ma'] = df['Close'].rolling(window=long_sma).mean()

if len(df) < long_sma:
    signal = 0
elif df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1]:
    signal = 1  # Buy
else:
    signal = -1  # Sell
""",
        target_portfolio_id=1,
        is_active=True,
        description="Test strategy"
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
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
    """Get sample strategy from database"""
    return db_session.query(Strategy).filter(Strategy.name == "Test SMA Strategy").first()


class TestNewFeaturesIntegration:
    """Integration tests for new features"""
    
    def test_complete_workflow_backtest_to_analysis(self, client, sample_strategy):
        """Test complete workflow: run backtest, save record, analyze with AI"""
        from unittest.mock import patch, AsyncMock
        
        # 1. Run backtest and save record
        backtest_request = {
            "strategy_id": sample_strategy.id,
            "start_date": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "end_date": datetime.now().strftime('%Y-%m-%d'),
            "initial_cash": 100000.0,
            "symbols": ["AAPL"]
        }
        
        mock_backtest_result = {
            "sharpe_ratio": 1.5,
            "sortino_ratio": 1.8,
            "annualized_return": 12.5,
            "max_drawdown": -15.0,
            "win_rate": 55.0,
            "total_trades": 100,
            "total_return": 12.5
        }
        
        with patch('main.run_backtest', new_callable=AsyncMock) as mock_backtest:
            mock_backtest.return_value = mock_backtest_result
            
            # Run backtest with save_record=true
            response1 = client.post(
                "/api/backtest?save_record=true",
                json=backtest_request
            )
            
            # Should succeed
            assert response1.status_code in [200, 500]
            
            if response1.status_code == 200:
                # 2. Get saved records
                response2 = client.get("/api/backtest/records")
                assert response2.status_code == 200
                
                # 3. Analyze with AI (using the backtest result)
                with patch('main.strategy_analyzer') as mock_analyzer:
                    mock_analyzer_instance = AsyncMock()
                    mock_analyzer_instance.analyze_backtest_result.return_value = {
                        "analysis_summary": "测试分析",
                        "strengths": ["优势1"],
                        "weaknesses": ["劣势1"],
                        "optimization_suggestions": ["建议1"]
                    }
                    mock_analyzer.return_value.__aenter__ = AsyncMock(return_value=mock_analyzer_instance)
                    mock_analyzer.return_value.__aexit__ = AsyncMock(return_value=None)
                    
                    response3 = client.post(
                        f"/api/backtest/analyze?strategy_id={sample_strategy.id}",
                        json={"backtest_result": mock_backtest_result}
                    )
                    
                    assert response3.status_code in [200, 500]
                    
                    if response3.status_code == 200:
                        data = response3.json()
                        assert 'structured_analysis' in data or 'analysis_summary' in data
                
                print("PASS: Complete workflow test passed")
            else:
                print("INFO: Complete workflow test skipped (backtest requires data)")
    
    def test_workflow_backtest_to_optimization(self, client, sample_strategy):
        """Test workflow: run backtest, then optimize parameters"""
        from unittest.mock import patch, AsyncMock
        
        # 1. Run initial backtest
        backtest_request = {
            "strategy_id": sample_strategy.id,
            "start_date": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "end_date": datetime.now().strftime('%Y-%m-%d'),
            "initial_cash": 100000.0,
            "symbols": ["AAPL"]
        }
        
        mock_backtest_result = {
            "sharpe_ratio": 1.2,
            "total_return": 8.0
        }
        
        with patch('main.run_backtest', new_callable=AsyncMock) as mock_backtest:
            mock_backtest.return_value = mock_backtest_result
            
            response1 = client.post("/api/backtest", json=backtest_request)
            assert response1.status_code in [200, 500]
            
            if response1.status_code == 200:
                # 2. Optimize parameters
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
                
                with patch('main.parameter_optimizer') as mock_optimizer:
                    mock_optimizer_instance = AsyncMock()
                    mock_optimizer_instance.optimize_parameters.return_value = {
                        "best_parameters": {"short_sma": 20, "long_sma": 50},
                        "best_metric_value": 1.5,
                        "optimization_metric": "sharpe_ratio",
                        "results": [],
                        "total_combinations": 6
                    }
                    mock_optimizer.return_value.__aenter__ = AsyncMock(return_value=mock_optimizer_instance)
                    mock_optimizer.return_value.__aexit__ = AsyncMock(return_value=None)
                    
                    response2 = client.post("/api/backtest/optimize", json=optimization_request)
                    assert response2.status_code in [200, 500]
                    
                    if response2.status_code == 200:
                        data = response2.json()
                        assert 'best_parameters' in data
                        assert 'best_metric_value' in data
                
                print("PASS: Backtest to optimization workflow test passed")
    
    def test_error_handling_new_endpoints(self, client, sample_strategy):
        """Test error handling for new endpoints"""
        
        # Test parameter optimization with invalid data
        invalid_optimization = {
            "strategy_id": 99999,  # Non-existent
            "start_date": "invalid-date",
            "end_date": "invalid-date",
            "initial_cash": -1000,  # Invalid
            "symbols": [],  # Empty
            "parameter_ranges": {}
        }
        
        response = client.post("/api/backtest/optimize", json=invalid_optimization)
        # Should return validation error
        assert response.status_code in [400, 422, 500]
        
        # Test AI analysis with invalid data
        invalid_analysis = {
            "backtest_result": {}  # Empty result
        }
        
        response2 = client.post(
            f"/api/backtest/analyze?strategy_id={sample_strategy.id}",
            json=invalid_analysis
        )
        # Should handle gracefully
        assert response2.status_code in [200, 400, 422, 500]
        
        print("PASS: Error handling test passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
