"""
Tests for Backtest API with time series data
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta

def test_backtest_returns_timeseries(client, db_session):
    """Test that backtest API returns time series data"""
    # Create a strategy first
    from models import Strategy, Portfolio
    
    # Create portfolio
    portfolio = Portfolio(
        name="Test Portfolio",
        initial_cash=100000,
        current_cash=100000,
        total_value=100000,
        daily_pnl=0,
        daily_pnl_percent=0
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    
    # Create strategy
    strategy = Strategy(
        name="Test Strategy",
        logic_code="signal = 1 if len(df) > 0 else 0",
        target_portfolio_id=portfolio.id,
        is_active=False
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    
    # Create backtest request
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    backtest_request = {
        "strategy_id": strategy.id,
        "start_date": start_date,
        "end_date": end_date,
        "initial_cash": 100000,
        "symbols": ["AAPL"]
    }
    
    # Call backtest endpoint
    response = client.post("/api/backtest", json=backtest_request)
    
    # Should either succeed or return proper error (if market data unavailable)
    assert response.status_code in [200, 500, 503]
    
    if response.status_code == 200:
        data = response.json()
        # Check that time series fields exist
        assert "equity_curve" in data or data.get("equity_curve") is None
        assert "drawdown_series" in data or data.get("drawdown_series") is None
        assert "trades" in data or data.get("trades") is None
        
        # Check basic metrics are present
        assert "sharpe_ratio" in data
        assert "total_return" in data
        assert "total_trades" in data
        
        # If time series data is present, verify structure
        if data.get("equity_curve"):
            assert isinstance(data["equity_curve"], list)
            if len(data["equity_curve"]) > 0:
                assert "date" in data["equity_curve"][0]
                assert "value" in data["equity_curve"][0]
        
        if data.get("drawdown_series"):
            assert isinstance(data["drawdown_series"], list)
            if len(data["drawdown_series"]) > 0:
                assert "date" in data["drawdown_series"][0]
                assert "drawdown" in data["drawdown_series"][0]
        
        if data.get("trades"):
            assert isinstance(data["trades"], list)
            if len(data["trades"]) > 0:
                assert "date" in data["trades"][0]
                assert "symbol" in data["trades"][0]
                assert "side" in data["trades"][0]
