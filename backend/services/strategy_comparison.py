"""
Strategy comparison service
Runs benchmark strategies and compares results with the main strategy
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy.orm import Session

from ..backtest_engine import BacktestEngine, run_backtest
from ..schemas import BacktestRequest, BacktestResult
from .benchmark_strategies import BENCHMARK_STRATEGIES, get_benchmark_strategy
from .index_comparison import get_index_performance

logger = logging.getLogger(__name__)

async def run_benchmark_strategy(
    strategy_id: str,
    symbols: List[str],
    start_date: str,
    end_date: str,
    initial_cash: float,
    all_data: Dict[str, pd.DataFrame]
) -> Optional[BacktestResult]:
    """
    Run a benchmark strategy on the same data
    
    Args:
        strategy_id: Benchmark strategy ID (e.g., 'SMA_CROSS', 'MOMENTUM')
        symbols: List of stock symbols
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        initial_cash: Initial cash amount
        all_data: Dictionary mapping symbol to DataFrame with historical data
    
    Returns:
        BacktestResult or None if failed
    """
    try:
        strategy_func = get_benchmark_strategy(strategy_id)
        if not strategy_func:
            logger.warning(f"Unknown benchmark strategy: {strategy_id}")
            return None
        
        # Initialize backtest engine
        engine = BacktestEngine(initial_cash=initial_cash)
        
        # Align all dataframes by date
        common_dates = None
        for symbol, df in all_data.items():
            if common_dates is None:
                common_dates = set(df.index)
            else:
                common_dates = common_dates.intersection(set(df.index))
        
        if not common_dates:
            logger.warning(f"No common dates found for benchmark strategy {strategy_id}")
            return None
        
        common_dates = sorted(list(common_dates))
        
        # Track equity curve
        equity_curve_with_dates = []
        
        # Execute strategy for each date
        for date in common_dates:
            current_prices = {}
            
            # Get current prices for all symbols
            for symbol, df in all_data.items():
                if date in df.index:
                    current_prices[symbol] = float(df.loc[date, 'Close'])
            
            # Execute strategy for each symbol
            for symbol, df in all_data.items():
                if date not in df.index:
                    continue
                
                # Get data up to current date for strategy
                historical_data = df.loc[:date]
                
                try:
                    # Execute benchmark strategy
                    signal_series = strategy_func(historical_data)
                    signal = int(signal_series.iloc[-1]) if hasattr(signal_series, 'iloc') else int(signal_series[-1])
                    
                    # Execute trade
                    price = current_prices.get(symbol, 0)
                    if price > 0:
                        trigger_reason = f"{BENCHMARK_STRATEGIES[strategy_id.upper()]['name']} signal"
                        engine.execute_trade(symbol, signal, price, date, trigger_reason)
                
                except Exception as e:
                    logger.warning(f"Benchmark strategy {strategy_id} execution failed for {symbol} on {date}: {str(e)}")
                    continue
            
            # Calculate portfolio value
            portfolio_value = engine.calculate_portfolio_value(current_prices)
            engine.equity_curve.append(portfolio_value)
            equity_curve_with_dates.append({
                'date': date.isoformat() if isinstance(date, datetime) else str(date),
                'value': float(portfolio_value)
            })
        
        # Calculate metrics
        metrics = engine.calculate_metrics(engine.equity_curve)
        
        # Calculate per-stock performance (if method exists)
        per_stock_performance = []
        if hasattr(engine, 'calculate_per_stock_performance'):
            try:
                per_stock_performance = engine.calculate_per_stock_performance()
            except Exception as e:
                logger.warning(f"Failed to calculate per-stock performance: {str(e)}")
        metrics['per_stock_performance'] = per_stock_performance
        
        # Calculate drawdown series
        equity_array = np.array(engine.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        
        drawdown_series = []
        for i, date in enumerate(common_dates):
            drawdown_series.append({
                'date': date.isoformat() if isinstance(date, datetime) else str(date),
                'drawdown': float(abs(drawdown[i])) if i < len(drawdown) else 0.0
            })
        
        # Format trades data
        trades_data = []
        for trade in engine.trades:
            trade_date = trade.get('date', '')
            if isinstance(trade_date, datetime):
                date_str = trade_date.isoformat()
            else:
                date_str = str(trade_date)
            
            trades_data.append({
                'date': date_str,
                'symbol': trade['symbol'],
                'side': trade['side'],
                'price': float(trade['price']),
                'quantity': int(trade['quantity']),
                'commission': float(trade.get('commission', 0)),
                'trigger_reason': trade.get('trigger_reason', ''),
                'pnl': trade.get('pnl'),
                'pnl_percent': trade.get('pnl_percent')
            })
        
        # Return as dict (will be converted to BacktestResult later)
        return {
            **metrics,
            'equity_curve': equity_curve_with_dates,
            'drawdown_series': drawdown_series,
            'trades': trades_data,
            'per_stock_performance': per_stock_performance
        }
        
    except Exception as e:
        logger.error(f"Failed to run benchmark strategy {strategy_id}: {str(e)}")
        return None

async def compare_strategies(
    main_result: BacktestResult,
    request: BacktestRequest,
    compare_items: List[str],
    all_data: Dict[str, pd.DataFrame],
    db: Session
) -> Dict[str, Any]:
    """
    Compare main strategy with benchmarks and indices
    
    Args:
        main_result: Main strategy backtest result
        request: Original backtest request
        compare_items: List of items to compare (e.g., ['NASDAQ', 'SMA_CROSS', 'MOMENTUM'])
        all_data: Historical data for all symbols
        db: Database session
    
    Returns:
        Dictionary with comparison results
    """
    comparisons = {
        'main': {
            'name': '当前策略',
            'type': 'strategy',
            'result': main_result.model_dump()
        }
    }
    
    # Run benchmark strategies
    benchmark_ids = [item for item in compare_items if item in BENCHMARK_STRATEGIES]
    for benchmark_id in benchmark_ids:
        try:
            benchmark_result = await run_benchmark_strategy(
                strategy_id=benchmark_id,
                symbols=request.symbols,
                start_date=request.start_date,
                end_date=request.end_date,
                initial_cash=request.initial_cash,
                all_data=all_data
            )
            if benchmark_result:
                comparisons[benchmark_id] = {
                    'name': BENCHMARK_STRATEGIES[benchmark_id]['name'],
                    'type': 'benchmark',
                    'result': benchmark_result  # Already a dict
                }
        except Exception as e:
            logger.error(f"Failed to run benchmark {benchmark_id}: {str(e)}")
    
    # Get index performances
    index_names = [item for item in compare_items if item in ['NASDAQ', 'SP500', 'DOW', 'CSI300', 'SZSE', 'SSE']]
    for index_name in index_names:
        try:
            index_perf = await get_index_performance(
                index_name=index_name,
                start_date=request.start_date,
                end_date=request.end_date
            )
            if index_perf:
                # Convert index performance to BacktestResult-like format
                comparisons[index_name] = {
                    'name': index_name,
                    'type': 'index',
                    'result': {
                        'total_return': index_perf['total_return'],
                        'annualized_return': index_perf['annualized_return'],
                        'sharpe_ratio': index_perf['sharpe_ratio'],
                        'max_drawdown': index_perf['max_drawdown'],
                        'total_trades': 0,  # Indices don't have trades
                        'win_rate': None,
                        'sortino_ratio': None
                    }
                }
        except Exception as e:
            logger.error(f"Failed to get index {index_name}: {str(e)}")
    
    return comparisons
