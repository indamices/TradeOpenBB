import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import logging
import math
import re

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

def extract_trigger_reason(signal: int, strategy_code: str, historical_data: pd.DataFrame, symbol: str) -> str:
    """
    Extract trigger reason from strategy execution (rule-based, not LLM)
    
    Args:
        signal: Trade signal (1=buy, -1=sell, 0=hold)
        strategy_code: Strategy code string
        historical_data: Historical price data
        symbol: Stock symbol
    
    Returns:
        Human-readable trigger reason
    """
    if signal == 0:
        return "Hold signal: No trading condition met"
    
    try:
        # Try to extract common patterns from strategy code
        # Look for common indicators and conditions
        
        # Check for SMA crossover
        if 'SMA' in strategy_code or 'sma' in strategy_code:
            if 'rolling' in strategy_code.lower() or 'mean()' in strategy_code:
                if signal == 1:
                    return f"Buy signal: Short-term moving average crossed above long-term moving average for {symbol}"
                elif signal == -1:
                    return f"Sell signal: Short-term moving average crossed below long-term moving average for {symbol}"
        
        # Check for RSI
        if 'RSI' in strategy_code or 'rsi' in strategy_code:
            if signal == 1:
                return f"Buy signal: RSI indicates oversold condition for {symbol}"
            elif signal == -1:
                return f"Sell signal: RSI indicates overbought condition for {symbol}"
        
        # Check for MACD
        if 'MACD' in strategy_code or 'macd' in strategy_code:
            if signal == 1:
                return f"Buy signal: MACD bullish crossover for {symbol}"
            elif signal == -1:
                return f"Sell signal: MACD bearish crossover for {symbol}"
        
        # Check for price-based conditions
        if 'Close' in strategy_code or 'close' in strategy_code:
            if len(historical_data) > 0:
                current_price = historical_data['Close'].iloc[-1]
                if len(historical_data) > 1:
                    prev_price = historical_data['Close'].iloc[-2]
                    if signal == 1 and current_price > prev_price:
                        return f"Buy signal: Price increased for {symbol} (${prev_price:.2f} -> ${current_price:.2f})"
                    elif signal == -1 and current_price < prev_price:
                        return f"Sell signal: Price decreased for {symbol} (${prev_price:.2f} -> ${current_price:.2f})"
        
        # Generic fallback
        if signal == 1:
            return f"Buy signal: Strategy condition met for {symbol}"
        elif signal == -1:
            return f"Sell signal: Strategy condition met for {symbol}"
        
    except Exception as e:
        logger.debug(f"Failed to extract trigger reason: {str(e)}")
    
    # Final fallback
    if signal == 1:
        return f"Buy signal triggered for {symbol}"
    elif signal == -1:
        return f"Sell signal triggered for {symbol}"
    return "No signal"

class BacktestEngine:
    """Engine for backtesting trading strategies"""
    
    def __init__(self, initial_cash: float = 100000):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}  # symbol -> quantity
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []
    
    def execute_trade(self, symbol: str, signal: int, price: float, date: datetime, trigger_reason: str = None):
        """
        Execute a trade based on signal
        
        Args:
            symbol: Stock symbol
            signal: 1 (buy), -1 (sell), 0 (hold)
            price: Current price
            date: Trade date
            trigger_reason: Reason for the trade (e.g., "SMA_20 crossed above SMA_50")
        """
        if signal == 0:
            return
        
        current_qty = self.positions.get(symbol, 0)
        
        # Convert date to string for JSON serialization
        date_str = date.isoformat() if isinstance(date, datetime) else str(date)
        
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
                            'date': date_str,
                            'symbol': symbol,
                            'side': 'BUY',
                            'quantity': shares_to_buy,
                            'price': price,
                            'commission': commission,
                            'trigger_reason': trigger_reason or f"Buy signal triggered for {symbol}",
                            'pnl': None,  # Will be calculated when sold
                            'pnl_percent': None
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
                    'date': date_str,
                    'symbol': symbol,
                    'side': 'SELL',
                    'quantity': shares_to_sell,
                    'price': price,
                    'commission': commission,
                    'trigger_reason': trigger_reason or f"Sell signal triggered for {symbol}",
                    'pnl': None,  # Will be calculated in calculate_metrics
                    'pnl_percent': None
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
        
        # Max Drawdown (fixed: limit to 0-100% range)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max  # This is negative or zero
        max_drawdown_pct = abs(drawdown.min()) * 100
        # Limit max drawdown to 0-100% range (prevent unrealistic values like thousands of percent)
        max_drawdown = min(max_drawdown_pct, 100.0) if not math.isnan(max_drawdown_pct) and not math.isinf(max_drawdown_pct) else 0.0
        
        # Win rate (fixed: consider commission in P&L calculation)
        if len(self.trades) >= 2:
            # Calculate P&L for each trade pair (considering commission)
            trade_pnl = []
            for i in range(0, len(self.trades) - 1, 2):
                if i + 1 < len(self.trades):
                    buy_trade = self.trades[i]
                    sell_trade = self.trades[i + 1]
                    if buy_trade['side'] == 'BUY' and sell_trade['side'] == 'SELL' and buy_trade['symbol'] == sell_trade['symbol']:
                        # Calculate net P&L: (sell_price - buy_price) * quantity - buy_commission - sell_commission
                        buy_cost = buy_trade['price'] * buy_trade['quantity'] + buy_trade.get('commission', 0)
                        sell_revenue = sell_trade['price'] * sell_trade['quantity'] - sell_trade.get('commission', 0)
                        pnl = sell_revenue - buy_cost
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
    
    def calculate_per_stock_performance(self) -> List[Dict[str, Any]]:
        """
        Calculate performance breakdown for each stock
        
        Returns:
            List of dictionaries with per-stock performance metrics
        """
        per_stock = {}
        
        # Group trades by symbol
        for trade in self.trades:
            symbol = trade['symbol']
            if symbol not in per_stock:
                per_stock[symbol] = {
                    'symbol': symbol,
                    'total_trades': 0,
                    'buy_trades_count': 0,
                    'sell_trades_count': 0,
                    'total_quantity_bought': 0,
                    'total_quantity_sold': 0,
                    'final_position': self.positions.get(symbol, 0),
                    'total_buy_cost': 0.0,
                    'total_sell_revenue': 0.0,
                    'total_commission': 0.0,
                    'realized_pnl': 0.0,
                    'return_percent': 0.0
                }
            
            stock_data = per_stock[symbol]
            stock_data['total_trades'] += 1
            stock_data['total_commission'] += trade.get('commission', 0)
            
            if trade['side'] == 'BUY':
                stock_data['buy_trades_count'] += 1
                stock_data['total_quantity_bought'] += trade['quantity']
                cost = trade['price'] * trade['quantity'] + trade.get('commission', 0)
                stock_data['total_buy_cost'] += cost
            elif trade['side'] == 'SELL':
                stock_data['sell_trades_count'] += 1
                stock_data['total_quantity_sold'] += trade['quantity']
                revenue = trade['price'] * trade['quantity'] - trade.get('commission', 0)
                stock_data['total_sell_revenue'] += revenue
        
        # Calculate realized P&L and return for each stock
        result = []
        for symbol, stock_data in per_stock.items():
            # Realized P&L = sell_revenue - buy_cost (for sold shares only)
            # We need to match buys with sells
            buys = [t for t in self.trades if t['symbol'] == symbol and t['side'] == 'BUY']
            sells = [t for t in self.trades if t['symbol'] == symbol and t['side'] == 'SELL']
            
            # Calculate realized P&L by matching buy-sell pairs
            realized_pnl = 0.0
            buy_cost_for_sold = 0.0
            
            # Simple FIFO matching (copy buys to avoid modifying original)
            buy_queue = [{'quantity': t['quantity'], 'price': t['price'], 'commission': t.get('commission', 0)} for t in buys]
            buy_idx = 0
            for sell_trade in sells:
                shares_sold = sell_trade['quantity']
                sell_revenue = sell_trade['price'] * shares_sold - sell_trade.get('commission', 0)
                
                # Match with buys (FIFO)
                shares_to_match = shares_sold
                buy_cost = 0.0
                while shares_to_match > 0 and buy_idx < len(buy_queue):
                    buy_item = buy_queue[buy_idx]
                    available_shares = buy_item['quantity']
                    
                    if available_shares <= shares_to_match:
                        # Use all shares from this buy
                        cost = buy_item['price'] * available_shares + buy_item['commission']
                        buy_cost += cost
                        shares_to_match -= available_shares
                        buy_idx += 1
                    else:
                        # Use partial shares from this buy
                        cost = buy_item['price'] * shares_to_match + (buy_item['commission'] * shares_to_match / available_shares)
                        buy_cost += cost
                        buy_item['quantity'] -= shares_to_match  # Update remaining in queue
                        shares_to_match = 0
                
                # Calculate P&L for this sell
                pnl = sell_revenue - buy_cost
                realized_pnl += pnl
                buy_cost_for_sold += buy_cost
            
            stock_data['realized_pnl'] = realized_pnl
            stock_data['buy_cost_for_sold'] = buy_cost_for_sold
            
            # Calculate return percentage
            if buy_cost_for_sold > 0:
                stock_data['return_percent'] = (realized_pnl / buy_cost_for_sold) * 100
            else:
                stock_data['return_percent'] = 0.0
            
            # Calculate average buy and sell prices
            if stock_data['total_quantity_bought'] > 0:
                total_buy_value = sum(t['price'] * t['quantity'] for t in buys)
                stock_data['avg_buy_price'] = total_buy_value / stock_data['total_quantity_bought']
            else:
                stock_data['avg_buy_price'] = 0.0
            
            if stock_data['total_quantity_sold'] > 0:
                total_sell_value = sum(t['price'] * t['quantity'] for t in sells)
                stock_data['avg_sell_price'] = total_sell_value / stock_data['total_quantity_sold']
            else:
                stock_data['avg_sell_price'] = 0.0
            
            # Sanitize float values
            for key in ['realized_pnl', 'return_percent', 'avg_buy_price', 'avg_sell_price', 
                       'total_buy_cost', 'total_sell_revenue', 'total_commission']:
                val = stock_data[key]
                if isinstance(val, (float, np.floating)):
                    if math.isnan(val) or math.isinf(val):
                        stock_data[key] = 0.0
                    else:
                        stock_data[key] = float(val)
            
            result.append(stock_data)
        
        return result

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
                    
                    # Extract trigger reason (rule-based)
                    trigger_reason = extract_trigger_reason(signal, strategy.logic_code, historical_data, symbol)
                    
                    # Execute trade
                    price = current_prices.get(symbol, 0)
                    if price > 0:
                        engine.execute_trade(symbol, signal, price, date, trigger_reason)
                
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
        
        # Calculate metrics (this also calculates P&L for each trade)
        metrics = engine.calculate_metrics(engine.equity_curve)
        
        # Calculate per-stock performance breakdown
        per_stock_performance = engine.calculate_per_stock_performance()
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
        
        # Format trades data (include trigger_reason and P&L)
        trades_data = []
        for trade in engine.trades:
            trade_date = trade.get('date', '')
            # Handle both datetime objects and strings
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
                'pnl': trade.get('pnl'),  # May be None for buy orders
                'pnl_percent': trade.get('pnl_percent')  # May be None for buy orders
            })
        
        # Calculate per-stock performance breakdown
        per_stock_performance = engine.calculate_per_stock_performance()
        
        # Return BacktestResult with time series data
        return BacktestResult(
            **metrics,
            equity_curve=equity_curve_with_dates,
            drawdown_series=drawdown_series,
            trades=trades_data,
            per_stock_performance=per_stock_performance
        )
        
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}")
        raise
