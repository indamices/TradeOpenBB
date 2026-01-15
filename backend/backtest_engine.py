import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging
import math

try:
    from .schemas import BacktestRequest, BacktestResult
    from .openbb_service import openbb_service
    from .models import Strategy
    from .services.data_service import DataService
except ImportError:
    from schemas import BacktestRequest, BacktestResult
    from openbb_service import openbb_service
    from models import Strategy
    from services.data_service import DataService

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Engine for backtesting trading strategies"""
    
    def __init__(self, initial_cash: float = 100000):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}  # symbol -> quantity
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []
    
    def execute_trade(self, symbol: str, signal: int, price: float, date: datetime):
        """
        Execute a trade based on signal
        
        Args:
            symbol: Stock symbol
            signal: 1 (buy), -1 (sell), 0 (hold)
            price: Current price
            date: Trade date
        """
        if signal == 0:
            return
        
        current_qty = self.positions.get(symbol, 0)
        
        if signal == 1:  # Buy
            # Calculate how many shares we can buy (accounting for commission)
            # We need: shares * price + commission <= cash
            # commission = max(1, shares * price * 0.0003)
            # Try to find the maximum shares we can buy
            max_shares = int(self.cash / price)
            if max_shares > 0:
                # Try buying max_shares and check if we have enough cash
                for shares_to_buy in range(max_shares, 0, -1):
                    cost = shares_to_buy * price
                    commission = max(1, cost * 0.0003)  # 3 bps, min $1
                    total_cost = cost + commission
                    
                    if total_cost <= self.cash:
                        self.cash -= total_cost
                        self.positions[symbol] = current_qty + shares_to_buy
                        
                        self.trades.append({
                            'date': date,
                            'symbol': symbol,
                            'side': 'BUY',
                            'quantity': shares_to_buy,
                            'price': price,
                            'commission': commission
                        })
                        break
        
        elif signal == -1:  # Sell
            if current_qty > 0:
                shares_to_sell = current_qty
                revenue = shares_to_sell * price
                commission = max(1, revenue * 0.0003)
                net_revenue = revenue - commission
                
                self.cash += net_revenue
                self.positions[symbol] = 0
                
                self.trades.append({
                    'date': date,
                    'symbol': symbol,
                    'side': 'SELL',
                    'quantity': shares_to_sell,
                    'price': price,
                    'commission': commission
                })
    
    def calculate_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        position_value = sum(qty * prices.get(symbol, 0) for symbol, qty in self.positions.items())
        return self.cash + position_value
    
    def calculate_metrics(self, equity_curve: List[float]) -> Dict:
        """Calculate performance metrics"""
        if len(equity_curve) < 2:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'annualized_return': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'total_return': 0.0
            }
        
        equity_array = np.array(equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]
        
        # Total return
        total_return = (equity_array[-1] - equity_array[0]) / equity_array[0] * 100
        
        # Annualized return (assuming daily data)
        days = len(equity_curve)
        annualized_return = ((equity_array[-1] / equity_array[0]) ** (252 / days) - 1) * 100 if days > 0 else 0
        
        # Sharpe Ratio (assuming risk-free rate = 0)
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Sortino Ratio (only downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            sortino_ratio = 0.0
        
        # Max Drawdown
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = abs(drawdown.min()) * 100
        
        # Win rate
        if len(self.trades) >= 2:
            # Calculate P&L for each trade pair
            trade_pnl = []
            for i in range(0, len(self.trades) - 1, 2):
                if i + 1 < len(self.trades):
                    buy_trade = self.trades[i]
                    sell_trade = self.trades[i + 1]
                    if buy_trade['side'] == 'BUY' and sell_trade['side'] == 'SELL':
                        pnl = (sell_trade['price'] - buy_trade['price']) * buy_trade['quantity']
                        trade_pnl.append(pnl)
            
            if trade_pnl:
                winning_trades = sum(1 for pnl in trade_pnl if pnl > 0)
                win_rate = (winning_trades / len(trade_pnl)) * 100
            else:
                win_rate = 0.0
        else:
            win_rate = 0.0
        
        # Helper function to sanitize float values for JSON
        def sanitize_float(val):
            if isinstance(val, (float, np.floating)):
                if math.isnan(val) or math.isinf(val):
                    return 0.0
                return float(val)
            return val
        
        return {
            'sharpe_ratio': sanitize_float(sharpe_ratio),
            'sortino_ratio': sanitize_float(sortino_ratio),
            'annualized_return': sanitize_float(annualized_return),
            'max_drawdown': sanitize_float(max_drawdown),
            'win_rate': sanitize_float(win_rate),
            'total_trades': len(self.trades),
            'total_return': sanitize_float(total_return)
        }

async def run_backtest(request: BacktestRequest, db: Session) -> BacktestResult:
    """
    Run backtest for a strategy
    
    Args:
        request: BacktestRequest with strategy_id, dates, symbols, etc.
        db: Database session
    
    Returns:
        BacktestResult with performance metrics
    """
    try:
        # Get strategy from database
        strategy = db.query(Strategy).filter(Strategy.id == request.strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {request.strategy_id} not found")
        
        # Initialize backtest engine
        engine = BacktestEngine(initial_cash=request.initial_cash)
        
        # Get historical data for all symbols using DataService (with caching)
        all_data: Dict[str, pd.DataFrame] = {}
        try:
            from .database import SessionLocal
            db = SessionLocal()
        except ImportError:
            from database import SessionLocal
            db = SessionLocal()
        
        try:
            async with DataService(db=db) as data_service:
                # Batch fetch data with rate limiting
                data_dict = await data_service.batch_fetch_historical_data(
                    symbols=request.symbols,
                    start_date=request.start_date,
                    end_date=request.end_date
                )
                all_data = data_dict
        except Exception as e:
            logger.error(f"Failed to fetch data using DataService: {e}, falling back to openbb_service")
            # Fallback to direct API calls
            for symbol in request.symbols:
                try:
                    data = openbb_service.get_stock_data(symbol, request.start_date, request.end_date)
                    all_data[symbol] = data
                except Exception as e2:
                    logger.warning(f"Failed to load data for {symbol}: {str(e2)}")
                    continue
        finally:
            if db:
                db.close()
        
        if not all_data:
            raise ValueError("No data available for backtesting")
        
        # Align all dataframes by date
        common_dates = None
        for symbol, df in all_data.items():
            if common_dates is None:
                common_dates = set(df.index)
            else:
                common_dates = common_dates.intersection(set(df.index))
        
        if not common_dates:
            raise ValueError("No common dates found across symbols")
        
        common_dates = sorted(list(common_dates))
        
        # Track equity curve with dates
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
                    # Execute strategy code (sandboxed)
                    # Note: In production, this should be done in a secure sandbox
                    strategy_func = compile(strategy.logic_code, '<string>', 'exec')
                    namespace = {
                        'pd': pd,
                        'np': np,
                        'df': historical_data
                    }
                    exec(strategy_func, namespace)
                    
                    # Get signal from strategy
                    if 'signal' in namespace:
                        signal = namespace['signal']
                    elif 'strategy_logic' in namespace:
                        signal_series = namespace['strategy_logic'](historical_data)
                        signal = int(signal_series.iloc[-1]) if hasattr(signal_series, 'iloc') else int(signal_series[-1])
                    else:
                        signal = 0
                    
                    # Execute trade
                    price = current_prices.get(symbol, 0)
                    if price > 0:
                        engine.execute_trade(symbol, signal, price, date)
                
                except Exception as e:
                    logger.warning(f"Strategy execution failed for {symbol} on {date}: {str(e)}")
                    continue
            
            # Calculate portfolio value
            portfolio_value = engine.calculate_portfolio_value(current_prices)
            engine.equity_curve.append(portfolio_value)
            # Track equity curve with dates
            equity_curve_with_dates.append({
                'date': date.isoformat() if isinstance(date, datetime) else str(date),
                'value': float(portfolio_value)
            })
        
        # Calculate metrics
        metrics = engine.calculate_metrics(engine.equity_curve)
        
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
            trade_date = trade['date']
            trades_data.append({
                'date': trade_date.isoformat() if isinstance(trade_date, datetime) else str(trade_date),
                'symbol': trade['symbol'],
                'side': trade['side'],
                'price': float(trade['price']),
                'quantity': int(trade['quantity']),
                'commission': float(trade.get('commission', 0))
            })
        
        # Return BacktestResult with time series data
        return BacktestResult(
            **metrics,
            equity_curve=equity_curve_with_dates,
            drawdown_series=drawdown_series,
            trades=trades_data
        )
        
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}")
        raise
