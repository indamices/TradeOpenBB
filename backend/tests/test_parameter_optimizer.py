"""
Unit tests for parameter optimizer
"""
import pytest
import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.parameter_optimizer import ParameterOptimizer
    from schemas import ParameterOptimizationRequest
    from models import Strategy
except ImportError:
    # Try alternative import paths
    try:
        from backend.services.parameter_optimizer import ParameterOptimizer
        from backend.schemas import ParameterOptimizationRequest
        from backend.models import Strategy
    except ImportError:
        # Final fallback
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from services.parameter_optimizer import ParameterOptimizer
        from schemas import ParameterOptimizationRequest
        from models import Strategy


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def sample_strategy():
    """Create a sample strategy for testing"""
    strategy = Strategy(
        id=1,
        name="Test Strategy",
        logic_code="""
short_sma = 20
long_sma = 50
df['short_ma'] = df['Close'].rolling(window=short_sma).mean()
df['long_ma'] = df['Close'].rolling(window=long_sma).mean()
if df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1]:
    signal = 1
else:
    signal = -1
""",
        target_portfolio_id=1,
        is_active=True
    )
    return strategy


@pytest.fixture
def optimizer(mock_db):
    """Create parameter optimizer instance"""
    return ParameterOptimizer(mock_db)


class TestParameterExtraction:
    """Test parameter extraction from strategy code"""
    
    def test_extract_parameters_simple(self, optimizer):
        """Test extracting simple numeric parameters"""
        code = """
short_sma = 20
long_sma = 50
rsi_period = 14
"""
        params = optimizer.extract_parameters_from_code(code)
        assert 'short_sma' in params
        assert 'long_sma' in params
        assert len(params['short_sma']) > 0
        assert len(params['long_sma']) > 0
    
    def test_extract_parameters_no_params(self, optimizer):
        """Test code with no extractable parameters"""
        code = """
signal = 0
if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
    signal = 1
"""
        params = optimizer.extract_parameters_from_code(code)
        # Should return empty dict or handle gracefully
        assert isinstance(params, dict)
    
    def test_extract_parameters_edge_cases(self, optimizer):
        """Test edge cases in parameter extraction"""
        code = """
threshold = 0.5  # Float value
count = 100  # Large value
small = 3  # Small value
"""
        params = optimizer.extract_parameters_from_code(code)
        assert isinstance(params, dict)


class TestParameterReplacement:
    """Test parameter replacement in strategy code"""
    
    def test_replace_parameters_simple(self, optimizer):
        """Test simple parameter replacement"""
        code = "short_sma = 20\nlong_sma = 50"
        params = {'short_sma': 30, 'long_sma': 60}
        modified = optimizer.replace_parameters_in_code(code, params)
        assert 'short_sma = 30' in modified
        assert 'long_sma = 60' in modified
        assert 'short_sma = 20' not in modified
    
    def test_replace_parameters_partial(self, optimizer):
        """Test replacing only some parameters"""
        code = "short_sma = 20\nlong_sma = 50\nrsi = 14"
        params = {'short_sma': 30}
        modified = optimizer.replace_parameters_in_code(code, params)
        assert 'short_sma = 30' in modified
        assert 'long_sma = 50' in modified  # Should remain unchanged


class TestParameterCombinations:
    """Test parameter combination generation"""
    
    def test_generate_combinations_simple(self, optimizer):
        """Test generating parameter combinations"""
        ranges = {
            'short_sma': [10, 20],
            'long_sma': [50, 100]
        }
        combinations = optimizer.generate_parameter_combinations(ranges)
        assert len(combinations) == 4  # 2 * 2 = 4 combinations
        assert {'short_sma': 10, 'long_sma': 50} in combinations
        assert {'short_sma': 20, 'long_sma': 100} in combinations
    
    def test_generate_combinations_empty(self, optimizer):
        """Test with empty parameter ranges"""
        ranges = {}
        combinations = optimizer.generate_parameter_combinations(ranges)
        assert len(combinations) == 1
        assert combinations[0] == {}
    
    def test_generate_combinations_large(self, optimizer):
        """Test with many parameter values"""
        ranges = {
            'param1': [1, 2, 3],
            'param2': [10, 20],
            'param3': [100]
        }
        combinations = optimizer.generate_parameter_combinations(ranges)
        assert len(combinations) == 6  # 3 * 2 * 1 = 6 combinations


class TestParameterOptimization:
    """Test full parameter optimization workflow"""
    
    @pytest.mark.asyncio
    async def test_optimize_parameters_basic(self, optimizer, mock_db, sample_strategy):
        """Test basic parameter optimization"""
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_strategy
        
        # Mock run_backtest
        from backtest_engine import run_backtest
        with patch('services.parameter_optimizer.run_backtest', new_callable=AsyncMock) as mock_backtest:
            # Create mock backtest result
            from schemas import BacktestResult
            mock_result = BacktestResult(
                sharpe_ratio=1.5,
                annualized_return=10.0,
                max_drawdown=-15.0,
                total_trades=50,
                total_return=10.0
            )
            mock_backtest.return_value = mock_result
            
            # Create optimization request
            request = ParameterOptimizationRequest(
                strategy_id=1,
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_cash=100000,
                symbols=["AAPL"],
                parameter_ranges={
                    'short_sma': [15, 20, 25],
                    'long_sma': [45, 50, 55]
                },
                optimization_metric='sharpe_ratio'
            )
            
            # Run optimization
            result = await optimizer.optimize_parameters(
                strategy_id=1,
                optimization_request=request,
                optimization_metric='sharpe_ratio'
            )
            
            # Verify results
            assert result is not None
            assert 'best_parameters' in result
            assert 'best_metric_value' in result
            assert result['total_combinations'] == 9  # 3 * 3 = 9
            assert result['valid_combinations'] == 9
            assert mock_backtest.call_count == 9
    
    @pytest.mark.asyncio
    async def test_optimize_parameters_with_failures(self, optimizer, mock_db, sample_strategy):
        """Test optimization with some failed backtests"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_strategy
        
        from backtest_engine import run_backtest
        with patch('services.parameter_optimizer.run_backtest', new_callable=AsyncMock) as mock_backtest:
            from schemas import BacktestResult
            mock_result = BacktestResult(
                sharpe_ratio=1.5,
                annualized_return=10.0,
                max_drawdown=-15.0,
                total_trades=50,
                total_return=10.0
            )
            
            # Make some calls fail
            call_count = [0]
            def mock_backtest_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] <= 3:  # First 3 succeed
                    return mock_result
                else:  # Rest fail
                    raise ValueError("Backtest failed")
            
            mock_backtest.side_effect = mock_backtest_side_effect
            
            request = ParameterOptimizationRequest(
                strategy_id=1,
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_cash=100000,
                symbols=["AAPL"],
                parameter_ranges={
                    'short_sma': [15, 20, 25],
                    'long_sma': [45, 50]
                },
                optimization_metric='sharpe_ratio'
            )
            
            result = await optimizer.optimize_parameters(
                strategy_id=1,
                optimization_request=request,
                optimization_metric='sharpe_ratio'
            )
            
            assert result is not None
            assert result['valid_combinations'] < result['total_combinations']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
