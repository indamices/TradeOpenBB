"""
Benchmark trading strategies for comparison
These are well-known strategies used to benchmark custom strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def sma_cross_strategy(df: pd.DataFrame) -> pd.Series:
    """
    SMA Crossover Strategy: Buy when 20-day SMA crosses above 50-day SMA, sell when below
    
    Args:
        df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
    
    Returns:
        Series of signals: 1 (buy), -1 (sell), 0 (hold)
    """
    if len(df) < 50:
        return pd.Series(0, index=df.index)
    
    df = df.copy()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    signals = pd.Series(0, index=df.index)
    
    # Buy when SMA_20 crosses above SMA_50
    signals[df['SMA_20'] > df['SMA_50']] = 1
    
    # Sell when SMA_20 crosses below SMA_50
    signals[df['SMA_20'] < df['SMA_50']] = -1
    
    # Remove signals before enough data for SMA_50
    signals.iloc[:50] = 0
    
    return signals

def momentum_strategy(df: pd.DataFrame, period: int = 10, threshold: float = 0.02) -> pd.Series:
    """
    Momentum Strategy: Buy when price momentum is positive, sell when negative
    
    Args:
        df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        period: Lookback period for momentum calculation (default: 10 days)
        threshold: Minimum momentum threshold to trigger signal (default: 2%)
    
    Returns:
        Series of signals: 1 (buy), -1 (sell), 0 (hold)
    """
    if len(df) < period:
        return pd.Series(0, index=df.index)
    
    df = df.copy()
    # Calculate momentum as percentage change over period
    returns = df['Close'].pct_change(period)
    
    signals = pd.Series(0, index=df.index)
    
    # Buy when momentum is positive and above threshold
    signals[returns > threshold] = 1
    
    # Sell when momentum is negative and below threshold
    signals[returns < -threshold] = -1
    
    # Remove signals before enough data
    signals.iloc[:period] = 0
    
    return signals

def mean_reversion_strategy(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.Series:
    """
    Mean Reversion Strategy (Bollinger Bands): Buy when price touches lower band, sell at upper band
    
    Args:
        df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        period: Period for moving average (default: 20 days)
        std_dev: Standard deviation multiplier for bands (default: 2.0)
    
    Returns:
        Series of signals: 1 (buy), -1 (sell), 0 (hold)
    """
    if len(df) < period:
        return pd.Series(0, index=df.index)
    
    df = df.copy()
    df['SMA'] = df['Close'].rolling(window=period).mean()
    df['STD'] = df['Close'].rolling(window=period).std()
    df['Upper'] = df['SMA'] + std_dev * df['STD']
    df['Lower'] = df['SMA'] - std_dev * df['STD']
    
    signals = pd.Series(0, index=df.index)
    
    # Buy when price touches or goes below lower band
    signals[df['Close'] <= df['Lower']] = 1
    
    # Sell when price touches or goes above upper band
    signals[df['Close'] >= df['Upper']] = -1
    
    # Remove signals before enough data
    signals.iloc[:period] = 0
    
    return signals

def buy_and_hold_strategy(df: pd.DataFrame) -> pd.Series:
    """
    Buy and Hold Strategy: Buy at the beginning, sell at the end
    
    Args:
        df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
    
    Returns:
        Series of signals: 1 (buy at start), -1 (sell at end), 0 (hold)
    """
    signals = pd.Series(0, index=df.index)
    
    if len(df) > 0:
        # Buy at the first available date
        signals.iloc[0] = 1
        # Sell at the last date (if we have more than 1 day)
        if len(df) > 1:
            signals.iloc[-1] = -1
    
    return signals

def rsi_strategy(df: pd.DataFrame, period: int = 14, oversold: float = 30, overbought: float = 70) -> pd.Series:
    """
    RSI Strategy: Buy when RSI is oversold, sell when overbought
    
    Args:
        df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        period: RSI calculation period (default: 14)
        oversold: RSI level for oversold condition (default: 30)
        overbought: RSI level for overbought condition (default: 70)
    
    Returns:
        Series of signals: 1 (buy), -1 (sell), 0 (hold)
    """
    if len(df) < period + 1:
        return pd.Series(0, index=df.index)
    
    df = df.copy()
    
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    signals = pd.Series(0, index=df.index)
    
    # Buy when RSI is oversold
    signals[rsi < oversold] = 1
    
    # Sell when RSI is overbought
    signals[rsi > overbought] = -1
    
    # Remove signals before enough data
    signals.iloc[:period] = 0
    
    return signals

# Strategy registry
BENCHMARK_STRATEGIES = {
    'SMA_CROSS': {
        'name': 'SMA交叉策略',
        'description': '20日均线上穿50日均线买入，下穿卖出',
        'function': sma_cross_strategy
    },
    'MOMENTUM': {
        'name': '动量策略',
        'description': '基于10日价格动量，涨幅>2%买入，跌幅>2%卖出',
        'function': momentum_strategy
    },
    'MEAN_REVERSION': {
        'name': '均值回归策略',
        'description': '基于布林带，触及下轨买入，触及上轨卖出',
        'function': mean_reversion_strategy
    },
    'BUY_AND_HOLD': {
        'name': '买入持有策略',
        'description': '第一天买入，最后一天卖出',
        'function': buy_and_hold_strategy
    },
    'RSI': {
        'name': 'RSI策略',
        'description': 'RSI<30买入，RSI>70卖出',
        'function': rsi_strategy
    }
}

def get_benchmark_strategy(strategy_id: str):
    """
    Get benchmark strategy function by ID
    
    Args:
        strategy_id: Strategy identifier (e.g., 'SMA_CROSS', 'MOMENTUM')
    
    Returns:
        Strategy function or None if not found
    """
    strategy_info = BENCHMARK_STRATEGIES.get(strategy_id.upper())
    if strategy_info:
        return strategy_info['function']
    return None

def list_benchmark_strategies() -> Dict[str, Dict[str, str]]:
    """
    List all available benchmark strategies
    
    Returns:
        Dictionary mapping strategy IDs to their metadata
    """
    return {
        strategy_id: {
            'name': info['name'],
            'description': info['description']
        }
        for strategy_id, info in BENCHMARK_STRATEGIES.items()
    }
