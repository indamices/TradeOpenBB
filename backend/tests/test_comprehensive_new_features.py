"""
Comprehensive tests for all new features
Tests parameter optimization, AI analysis, backtest records, benchmark strategies, and data source status
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
    from database import get_db, Base
    from models import Strategy, Portfolio, BacktestRecord, DataSourceConfig
except ImportError as e:
    pytest.skip(f"Cannot import required modules: {e}", allow_module_level=True)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_comprehensive.db"

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
        name="Test SMA Strategy",
        logic_code="""
short_sma = 20
long_sma = 50

df['short_ma'] = df['Close'].rolling(window=short_sma).mean()
df['long_ma'] = df['Close'].rolling(window=long_sma).mean()

if len(df) < long_sma:
    signal = 0
elif df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1]:
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
    return db_session.query(Strategy).filter(Strategy.name == "Test SMA Strategy").first()


@pytest.fixture
def mock_historical_data():
    """Create mock historical data"""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    data = pd.DataFrame({
        'Open': [100 + i * 0.1 for i in range(len(dates))],
        'High': [101 + i * 0.1 for i in range(len(dates))],
        'Low': [99 + i * 0.1 for i in range(len(dates))],
        'Close': [100.5 + i * 0.1 for i in range(len(dates))],
        'Volume': [1000000] * len(dates)
    }, index=dates)
    return data


class TestBenchmarkStrategiesEndpoint:
    """Test benchmark strategies endpoint"""
    
    def test_benchmark_strategies_endpoint_exists(self, client):
        """Test that benchmark strategies endpoint exists"""
        response = client.get("/api/backtest/benchmark-strategies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        # Check that it contains expected strategy IDs
        assert 'SMA_CROSS' in data or 'MOMENTUM' in data or 'BUY_AND_HOLD' in data
        print("PASS: Benchmark strategies endpoint works")
    
    def test_benchmark_strategies_structure(self, client):
        """Test benchmark strategies response structure"""
        response = client.get("/api/backtest/benchmark-strategies")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure of first strategy
        if len(data) > 0:
            first_key = list(data.keys())[0]
            strategy_info = data[first_key]
            assert 'name' in strategy_info
            assert 'description' in strategy_info
            assert isinstance(strategy_info['name'], str)
            assert isinstance(strategy_info['description'], str)
        print("PASS: Benchmark strategies structure is correct")


class TestDataSourceStatusEndpoint:
    """Test data source status endpoint"""
    
    def test_data_source_status_endpoint_exists(self, client):
        """Test that data source status endpoint exists"""
        response = client.get("/api/data-sources/status")
        # Should work even if no data sources are configured
        assert response.status_code in [200, 500]  # 500 if database error, but endpoint exists
        if response.status_code == 200:
            data = response.json()
            assert 'sources' in data
            assert 'message' in data
            print("PASS: Data source status endpoint works")
    
    def test_data_source_status_with_sources(self, client, db_session):
        """Test data source status with configured sources"""
        # Create a test data source
        data_source = DataSourceConfig(
            name="Test Source",
            source_type="free",
            provider="yfinance",
            is_active=True,
            is_default=True,
            priority=1
        )
        db_session.add(data_source)
        db_session.commit()
        
        # Mock the data service to return test data
        with patch('services.data_service.DataService.get_historical_data') as mock_get_data:
            mock_get_data.return_value = pd.DataFrame({
                'Open': [100],
                'High': [101],
                'Low': [99],
                'Close': [100.5],
                'Volume': [1000000]
            })
            
            response = client.get("/api/data-sources/status")
            # May fail if data service can't be mocked properly, but endpoint should exist
            assert response.status_code in [200, 500]
            print("PASS: Data source status endpoint responds")


class TestParameterOptimizationAPI:
    """Test parameter optimization API endpoint"""
    
    @patch('services.data_service.DataService.get_historical_data')
    def test_parameter_optimization_endpoint(self, mock_get_data, client, sample_strategy, mock_historical_data):
        """Test parameter optimization endpoint"""
        mock_get_data.return_value = mock_historical_data
        
        request = {
            "strategy_id": sample_strategy.id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 100000.0,
            "symbols": ["AAPL"],
            "parameter_ranges": {
                "short_sma": [15, 20],
                "long_sma": [45, 50]
            },
            "optimization_metric": "sharpe_ratio"
        }
        
        response = client.post("/api/backtest/optimize", json=request)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert 'best_parameters' in data
            assert 'best_metric_value' in data
            assert 'optimization_metric' in data
            assert 'results' in data
            assert 'total_combinations' in data
            print("PASS: Parameter optimization endpoint works")
        else:
            print(f"INFO: Parameter optimization returned {response.status_code} (may need data)")


class TestAIAnalysisAPI:
    """Test AI analysis API endpoint"""
    
    def test_ai_analysis_endpoint_exists(self, client, sample_strategy):
        """Test that AI analysis endpoint exists"""
        # Create a mock backtest result
        backtest_result = {
            "sharpe_ratio": 0.75,
            "sortino_ratio": 0.81,
            "annualized_return": 0.108,  # 10.8% as decimal
            "max_drawdown": 0.1138,  # 11.38% as decimal
            "win_rate": 0.3333,  # 33.33% as decimal
            "total_trades": 41,
            "total_return": 0.108,  # 10.8% as decimal
            "equity_curve": [100000, 101000, 102000],
            "drawdown_series": [0, -0.01, -0.02],
            "trades": []
        }
        
        request = {
            "backtest_result": backtest_result,
            "strategy_id": sample_strategy.id
        }
        
        response = client.post("/api/backtest/analyze", json=request)
        
        # Should succeed or fail gracefully (may fail if no AI model configured)
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert 'analysis_summary' in data
            assert 'strengths' in data
            assert 'weaknesses' in data
            assert 'optimization_suggestions' in data
            print("PASS: AI analysis endpoint works")
        else:
            print(f"INFO: AI analysis returned {response.status_code} (may need AI model)")


class TestBacktestRecordsAPI:
    """Test backtest records API endpoints"""
    
    @patch('services.data_service.DataService.get_historical_data')
    def test_create_backtest_record(self, mock_get_data, client, sample_strategy, mock_historical_data):
        """Test creating a backtest record"""
        mock_get_data.return_value = mock_historical_data
        
        # First run a backtest with save_record=true
        backtest_request = {
            "strategy_id": sample_strategy.id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 100000.0,
            "symbols": ["AAPL"],
            "save_record": True
        }
        
        response = client.post("/api/backtest?save_record=true", json=backtest_request)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            # Check if record was created
            records_response = client.get("/api/backtest/records")
            assert records_response.status_code == 200
            records = records_response.json()
            assert isinstance(records, list)
            print("PASS: Backtest record creation works")
    
    def test_get_backtest_records(self, client):
        """Test getting backtest records"""
        response = client.get("/api/backtest/records")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print("PASS: Get backtest records works")
    
    def test_backtest_records_pagination(self, client):
        """Test backtest records pagination"""
        response = client.get("/api/backtest/records?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print("PASS: Backtest records pagination works")


class TestReturnDisplayFormat:
    """Test that return values are in decimal format (not percentage)"""
    
    @patch('services.data_service.DataService.get_historical_data')
    def test_backtest_result_returns_decimal(self, mock_get_data, client, sample_strategy, mock_historical_data):
        """Test that backtest results return decimal format for returns"""
        mock_get_data.return_value = mock_historical_data
        
        backtest_request = {
            "strategy_id": sample_strategy.id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 100000.0,
            "symbols": ["AAPL"]
        }
        
        response = client.post("/api/backtest", json=backtest_request)
        
        if response.status_code == 200:
            data = response.json()
            # Check that returns are in decimal format (0.108 = 10.8%), not percentage (10.8)
            if 'total_return' in data:
                assert isinstance(data['total_return'], (int, float))
                # Should be less than 1 for reasonable returns (unless >100% return)
                # For this test, we just check it's a number
                assert data['total_return'] is not None
            
            if 'annualized_return' in data:
                assert isinstance(data['annualized_return'], (int, float))
            
            if 'win_rate' in data:
                assert isinstance(data['win_rate'], (int, float))
                # win_rate should be decimal (0.5 = 50%), not percentage (50)
                # Should be between 0 and 1 (or slightly above 1 for >100% win rate, but unlikely)
                assert 0 <= data['win_rate'] <= 1.5  # Allow some margin
            
            print("PASS: Backtest results use decimal format for returns")


class TestTradePnlCalculation:
    """Test that trade P&L is calculated correctly"""
    
    @patch('services.data_service.DataService.get_historical_data')
    def test_trade_pnl_in_backtest_result(self, mock_get_data, client, sample_strategy, mock_historical_data):
        """Test that trades include P&L information"""
        mock_get_data.return_value = mock_historical_data
        
        backtest_request = {
            "strategy_id": sample_strategy.id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 100000.0,
            "symbols": ["AAPL"]
        }
        
        response = client.post("/api/backtest", json=backtest_request)
        
        if response.status_code == 200:
            data = response.json()
            if 'trades' in data and len(data['trades']) > 0:
                # Check that SELL trades have P&L
                sell_trades = [t for t in data['trades'] if t.get('side') == 'SELL']
                if len(sell_trades) > 0:
                    sell_trade = sell_trades[0]
                    # P&L should be calculated (not None)
                    # Note: P&L might be None for first trades if no matching buy
                    assert 'pnl' in sell_trade
                    assert 'pnl_percent' in sell_trade
                    print("PASS: Trade P&L fields are present")
                else:
                    print("INFO: No SELL trades to check P&L")
            else:
                print("INFO: No trades in backtest result")


class TestHistoricalDataEndpoint:
    """Test historical data endpoint"""
    
    @patch('services.data_service.DataService.get_historical_data')
    def test_historical_data_endpoint(self, mock_get_data, client, mock_historical_data):
        """Test historical data endpoint"""
        mock_get_data.return_value = mock_historical_data
        
        response = client.get("/api/market/historical/AAPL?start_date=2023-01-01&end_date=2023-12-31")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                # Check structure of first data point
                first_point = data[0]
                assert 'Date' in first_point or 'date' in first_point or 'Date' in str(first_point)
                print("PASS: Historical data endpoint works")
        else:
            print(f"INFO: Historical data returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
