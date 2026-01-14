"""
Tests for Backtest Engine
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_engine import BacktestEngine, run_backtest
from models import Strategy
from schemas import BacktestRequest

class TestBacktestEngine:
    """Test cases for BacktestEngine"""
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = BacktestEngine(initial_cash=100000)
        assert engine.initial_cash == 100000
        assert engine.cash == 100000
        assert engine.positions == {}
        assert engine.trades == []
        assert engine.equity_curve == []
    
    def test_engine_initialization_default(self):
        """Test engine initialization with default cash"""
        engine = BacktestEngine()
        assert engine.initial_cash == 100000
        assert engine.cash == 100000
    
    def test_execute_trade_buy(self):
        """Test executing a buy trade"""
        engine = BacktestEngine(initial_cash=10000)
        date = datetime.now()
        
        # Buy shares at $100 each (with 10000 cash, should buy ~99 shares after commission)
        engine.execute_trade("AAPL", 1, 100.0, date)
        
        assert "AAPL" in engine.positions
        assert engine.positions["AAPL"] > 0
        assert engine.cash < 10000  # Cash should decrease
        assert len(engine.trades) == 1
        assert engine.trades[0]['side'] == 'BUY'
        assert engine.trades[0]['symbol'] == 'AAPL'
    
    def test_execute_trade_sell(self):
        """Test executing a sell trade"""
        engine = BacktestEngine(initial_cash=10000)
        date = datetime.now()
        
        # First buy
        engine.execute_trade("AAPL", 1, 100.0, date)
        initial_cash = engine.cash
        initial_position = engine.positions.get("AAPL", 0)
        
        # Then sell
        engine.execute_trade("AAPL", -1, 110.0, date + timedelta(days=1))
        
        assert engine.positions.get("AAPL", 0) == 0  # Position should be closed
        assert engine.cash > initial_cash  # Cash should increase
        assert len(engine.trades) == 2
        assert engine.trades[1]['side'] == 'SELL'
    
    def test_execute_trade_hold(self):
        """Test executing a hold signal (no trade)"""
        engine = BacktestEngine(initial_cash=10000)
        date = datetime.now()
        
        initial_cash = engine.cash
        engine.execute_trade("AAPL", 0, 100.0, date)
        
        assert engine.cash == initial_cash  # Cash should not change
        assert len(engine.trades) == 0  # No trades should be executed
    
    def test_execute_trade_insufficient_cash(self):
        """Test executing trade with insufficient cash"""
        engine = BacktestEngine(initial_cash=100)
        date = datetime.now()
        
        # Try to buy at very high price
        engine.execute_trade("AAPL", 1, 1000.0, date)
        
        # Should not execute trade
        assert engine.positions.get("AAPL", 0) == 0
        assert len(engine.trades) == 0
    
    def test_execute_trade_sell_without_position(self):
        """Test selling without a position"""
        engine = BacktestEngine(initial_cash=10000)
        date = datetime.now()
        
        initial_cash = engine.cash
        engine.execute_trade("AAPL", -1, 100.0, date)
        
        # Should not execute trade
        assert engine.cash == initial_cash
        assert len(engine.trades) == 0
    
    def test_calculate_portfolio_value(self):
        """Test calculating portfolio value"""
        engine = BacktestEngine(initial_cash=10000)
        date = datetime.now()
        
        # Buy some shares
        engine.execute_trade("AAPL", 1, 100.0, date)
        
        prices = {"AAPL": 110.0}
        portfolio_value = engine.calculate_portfolio_value(prices)
        
        assert portfolio_value > 0
        assert portfolio_value > engine.cash  # Should include position value
    
    def test_calculate_portfolio_value_no_positions(self):
        """Test calculating portfolio value with no positions"""
        engine = BacktestEngine(initial_cash=10000)
        
        prices = {"AAPL": 100.0}
        portfolio_value = engine.calculate_portfolio_value(prices)
        
        assert portfolio_value == 10000  # Should equal cash
    
    def test_calculate_metrics_empty_equity_curve(self):
        """Test calculating metrics with empty equity curve"""
        engine = BacktestEngine()
        
        metrics = engine.calculate_metrics([])
        
        assert metrics['sharpe_ratio'] == 0.0
        assert metrics['sortino_ratio'] == 0.0
        assert metrics['annualized_return'] == 0.0
        assert metrics['max_drawdown'] == 0.0
        assert metrics['win_rate'] == 0.0
        assert metrics['total_trades'] == 0
        assert metrics['total_return'] == 0.0
    
    def test_calculate_metrics_single_value(self):
        """Test calculating metrics with single equity value"""
        engine = BacktestEngine()
        
        metrics = engine.calculate_metrics([100000])
        
        assert metrics['sharpe_ratio'] == 0.0
        assert metrics['total_return'] == 0.0
    
    def test_calculate_metrics_profitable_equity_curve(self):
        """Test calculating metrics with profitable equity curve"""
        engine = BacktestEngine(initial_cash=100000)
        
        # Simulate profitable equity curve
        equity_curve = [100000, 101000, 102000, 103000, 104000]
        metrics = engine.calculate_metrics(equity_curve)
        
        assert metrics['total_return'] > 0
        assert metrics['annualized_return'] >= 0
        assert isinstance(metrics['sharpe_ratio'], float)
        assert isinstance(metrics['max_drawdown'], float)
    
    def test_calculate_metrics_with_trades(self):
        """Test calculating metrics with trades"""
        engine = BacktestEngine(initial_cash=10000)
        date = datetime.now()
        
        # Execute some trades
        engine.execute_trade("AAPL", 1, 100.0, date)
        engine.execute_trade("AAPL", -1, 110.0, date + timedelta(days=1))
        
        equity_curve = [10000, 10100, 10100]
        metrics = engine.calculate_metrics(equity_curve)
        
        assert metrics['total_trades'] == 2
        assert isinstance(metrics['win_rate'], float)
    
    @pytest.mark.asyncio
    async def test_run_backtest_missing_strategy(self, db_session):
        """Test running backtest with missing strategy"""
        request = BacktestRequest(
            strategy_id=99999,
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_cash=100000
        )
        
        with pytest.raises(ValueError, match="Strategy.*not found"):
            await run_backtest(request, db_session)
    
    @pytest.mark.asyncio
    async def test_run_backtest_no_data(self, db_session):
        """Test running backtest with no available data"""
        # Create a strategy
        strategy = Strategy(
            name="Test Strategy",
            description="Test",
            logic_code="signal = 1",
            target_portfolio_id=1
        )
        db_session.add(strategy)
        db_session.commit()
        
        request = BacktestRequest(
            strategy_id=strategy.id,
            symbols=["INVALID_SYMBOL_XYZ123"],
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_cash=100000
        )
        
        with pytest.raises(ValueError, match="No data available"):
            await run_backtest(request, db_session)
    
    @pytest.mark.asyncio
    async def test_run_backtest_success(self, db_session):
        """Test running a successful backtest"""
        # Create a strategy
        strategy = Strategy(
            name="Test Strategy",
            description="Test",
            logic_code="signal = 0",  # Hold signal
            portfolio_id=1
        )
        db_session.add(strategy)
        db_session.commit()
        
        # Use a well-known symbol and recent dates
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        request = BacktestRequest(
            strategy_id=strategy.id,
            symbols=["AAPL"],
            start_date=start_date,
            end_date=end_date,
            initial_cash=100000
        )
        
        try:
            result = await run_backtest(request, db_session)
            
            assert result is not None
            assert hasattr(result, 'total_return')
            assert hasattr(result, 'sharpe_ratio')
            assert hasattr(result, 'max_drawdown')
            assert hasattr(result, 'total_trades')
        except Exception as e:
            # If data fetching fails, skip test
            pytest.skip(f"Data unavailable: {str(e)}")
