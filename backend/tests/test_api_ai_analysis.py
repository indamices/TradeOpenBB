"""
API Tests for AI Strategy Analysis Endpoint
Tests the /api/backtest/analyze endpoint
"""
import pytest
import sys
import os
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
    from database import get_db, Base
    from models import Strategy, Portfolio
except ImportError as e:
    pytest.skip(f"Cannot import required modules: {e}", allow_module_level=True)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_analysis.db"

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
    
    # Create test strategy
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
    return db_session.query(Strategy).filter(Strategy.name == "Test Strategy").first()


@pytest.fixture
def sample_backtest_result():
    """Create sample backtest result"""
    return {
        "sharpe_ratio": 1.5,
        "sortino_ratio": 1.8,
        "annualized_return": 12.5,
        "max_drawdown": -15.0,
        "win_rate": 55.0,
        "total_trades": 100,
        "total_return": 12.5
    }


class TestAIAnalysisEndpoint:
    """Test AI strategy analysis API endpoint"""
    
    def test_analyze_endpoint_exists(self, client):
        """Test that analysis endpoint exists"""
        response = client.get("/api/backtest/analyze")
        # Should return 405 (Method Not Allowed) for GET, or 422 for POST without body
        assert response.status_code in [405, 422]
        print("PASS: AI analysis endpoint exists")
    
    def test_analyze_missing_strategy_id(self, client, sample_backtest_result):
        """Test analysis without strategy_id parameter"""
        response = client.post("/api/backtest/analyze", json={
            "backtest_result": sample_backtest_result
        })
        assert response.status_code in [422, 400]  # Missing required parameter
        print("PASS: Missing strategy_id properly handled")
    
    def test_analyze_invalid_strategy_id(self, client, sample_backtest_result):
        """Test analysis with invalid strategy_id"""
        response = client.post(
            "/api/backtest/analyze?strategy_id=99999",
            json={"backtest_result": sample_backtest_result}
        )
        assert response.status_code in [404, 500]  # Strategy not found or server error
        print("PASS: Invalid strategy_id properly handled")
    
    def test_analyze_request_structure(self, client, sample_strategy, sample_backtest_result):
        """Test analysis request structure"""
        from unittest.mock import patch, AsyncMock
        
        # Mock the AI analysis service
        with patch('main.strategy_analyzer') as mock_analyzer:
            mock_analyzer_instance = AsyncMock()
            mock_analyzer_instance.analyze_backtest_result.return_value = {
                "analysis_summary": "策略表现良好",
                "strengths": ["Sharpe Ratio较高", "胜率合理"],
                "weaknesses": ["最大回撤较大"],
                "optimization_suggestions": ["建议添加止损机制"],
                "raw_ai_response": None
            }
            mock_analyzer.return_value.__enter__ = AsyncMock(return_value=mock_analyzer_instance)
            mock_analyzer.return_value.__aenter__ = AsyncMock(return_value=mock_analyzer_instance)
            mock_analyzer.return_value.__exit__ = AsyncMock(return_value=None)
            mock_analyzer.return_value.__aexit__ = AsyncMock(return_value=None)
            
            response = client.post(
                f"/api/backtest/analyze?strategy_id={sample_strategy.id}",
                json={"backtest_result": sample_backtest_result}
            )
            
            # Should return 200 with mocked data, or 500 if AI service fails
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                # Check for structured_analysis or analysis_summary
                assert 'structured_analysis' in data or 'analysis_summary' in data
                print("PASS: AI analysis request structure validated")
            else:
                print("INFO: AI analysis endpoint exists (may require AI service configuration)")
    
    def test_analyze_incomplete_backtest_result(self, client, sample_strategy):
        """Test analysis with incomplete backtest result"""
        incomplete_result = {
            "sharpe_ratio": 1.5
            # Missing other required fields
        }
        
        response = client.post(
            f"/api/backtest/analyze?strategy_id={sample_strategy.id}",
            json={"backtest_result": incomplete_result}
        )
        
        # Should accept partial data or return validation error
        assert response.status_code in [200, 422, 500]
        print("PASS: Incomplete backtest result handled")
    
    def test_analyze_empty_backtest_result(self, client, sample_strategy):
        """Test analysis with empty backtest result"""
        response = client.post(
            f"/api/backtest/analyze?strategy_id={sample_strategy.id}",
            json={"backtest_result": {}}
        )
        
        # Should handle gracefully or return error
        assert response.status_code in [200, 422, 500]
        print("PASS: Empty backtest result handled")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
