"""
Index comparison service
Compares backtest results with major market indices
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import logging
import yfinance as yf

logger = logging.getLogger(__name__)

# Index symbols mapping
INDEX_SYMBOLS = {
    'NASDAQ': '^IXIC',
    'SP500': '^GSPC',
    'DOW': '^DJI',
    'CSI300': '000300.SS',  # 沪深300
    'SZSE': '399001.SZ',    # 深证成指
    'SSE': '000001.SS',     # 上证指数
}

async def get_index_performance(
    index_name: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    Get index performance for comparison
    
    Args:
        index_name: Name of the index (e.g., 'NASDAQ', 'SP500', 'CSI300')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        Dict with performance metrics or None if failed
    """
    try:
        symbol = INDEX_SYMBOLS.get(index_name.upper())
        if not symbol:
            logger.warning(f"Unknown index: {index_name}")
            return None
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            logger.warning(f"No data for {index_name} ({symbol})")
            return None
        
        # Calculate performance metrics
        initial_price = hist['Close'].iloc[0]
        final_price = hist['Close'].iloc[-1]
        total_return = ((final_price - initial_price) / initial_price) * 100
        
        # Calculate daily returns
        daily_returns = hist['Close'].pct_change().dropna()
        
        # Annualized return (assuming daily data)
        days = len(hist)
        if days > 0:
            annualized_return = ((final_price / initial_price) ** (252 / days) - 1) * 100
        else:
            annualized_return = 0.0
        
        # Sharpe ratio (assuming risk-free rate = 0)
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Max drawdown
        running_max = hist['Close'].expanding().max()
        drawdown = (hist['Close'] - running_max) / running_max
        max_drawdown = abs(drawdown.min()) * 100
        # Limit to 0-100%
        max_drawdown = min(max_drawdown, 100.0)
        
        return {
            'index_name': index_name,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_price': float(initial_price),
            'final_price': float(final_price),
            'total_return': float(total_return),
            'annualized_return': float(annualized_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'days': days
        }
        
    except Exception as e:
        logger.error(f"Failed to get index performance for {index_name}: {str(e)}")
        return None

async def compare_with_indices(
    backtest_result: Dict,
    start_date: str,
    end_date: str,
    indices: Optional[List[str]] = None
) -> List[Dict]:
    """
    Compare backtest results with market indices
    
    Args:
        backtest_result: BacktestResult dict
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        indices: List of index names to compare (default: ['NASDAQ', 'SP500', 'CSI300'])
    
    Returns:
        List of comparison results
    """
    if indices is None:
        indices = ['NASDAQ', 'SP500', 'CSI300']
    
    comparisons = []
    
    # Get backtest metrics
    backtest_total_return = backtest_result.get('total_return', 0.0)
    backtest_annualized = backtest_result.get('annualized_return', 0.0)
    backtest_sharpe = backtest_result.get('sharpe_ratio', 0.0)
    backtest_drawdown = backtest_result.get('max_drawdown', 0.0)
    
    # Get index performances
    for index_name in indices:
        index_perf = await get_index_performance(index_name, start_date, end_date)
        if index_perf:
            comparison = {
                'index_name': index_name,
                'index_total_return': index_perf['total_return'],
                'index_annualized_return': index_perf['annualized_return'],
                'index_sharpe_ratio': index_perf['sharpe_ratio'],
                'index_max_drawdown': index_perf['max_drawdown'],
                'backtest_total_return': backtest_total_return,
                'backtest_annualized_return': backtest_annualized,
                'backtest_sharpe_ratio': backtest_sharpe,
                'backtest_max_drawdown': backtest_drawdown,
                'outperformance': backtest_total_return - index_perf['total_return'],
                'outperformance_pct': ((backtest_total_return - index_perf['total_return']) / abs(index_perf['total_return'])) * 100 if index_perf['total_return'] != 0 else 0.0
            }
            comparisons.append(comparison)
    
    return comparisons
