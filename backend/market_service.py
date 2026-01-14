from datetime import datetime
from typing import Optional, List, Dict
import logging

try:
    from .schemas import MarketQuote
    from .openbb_service import openbb_service
except ImportError:
    from schemas import MarketQuote
    from openbb_service import openbb_service

logger = logging.getLogger(__name__)

async def get_realtime_quote(symbol: str) -> MarketQuote:
    """
    Get real-time market quote for a symbol
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
    
    Returns:
        MarketQuote object with current price and market data
    """
    try:
        quote_data = openbb_service.get_realtime_quote(symbol.upper())
        
        return MarketQuote(
            symbol=symbol.upper(),
            price=quote_data['price'],
            change=quote_data['change'],
            change_percent=quote_data['change_percent'],
            volume=quote_data['volume'],
            last_updated=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to get quote for {symbol}: {str(e)}")
        raise

async def get_historical_data(symbol: str, start_date: str, end_date: Optional[str] = None):
    """
    Get historical market data for a symbol
    
    Args:
        symbol: Stock symbol
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format (optional)
    
    Returns:
        DataFrame with historical OHLCV data
    """
    try:
        data = openbb_service.get_stock_data(symbol.upper(), start_date, end_date)
        return data
    except Exception as e:
        logger.error(f"Failed to get historical data for {symbol}: {str(e)}")
        raise

async def get_technical_indicators(symbol: str, indicators: list, period: int = 20):
    """
    Get technical indicators for a symbol
    
    Args:
        symbol: Stock symbol
        indicators: List of indicator names
        period: Period for calculations
    
    Returns:
        DataFrame with indicator values
    """
    try:
        data = openbb_service.get_technical_indicators(symbol.upper(), indicators, period)
        return data
    except Exception as e:
        logger.error(f"Failed to get technical indicators for {symbol}: {str(e)}")
        raise

async def get_multiple_quotes(symbols: List[str]) -> List[MarketQuote]:
    """
    Get real-time quotes for multiple symbols
    
    Args:
        symbols: List of stock symbols
    
    Returns:
        List of MarketQuote objects
    """
    quotes = []
    for symbol in symbols:
        try:
            quote = await get_realtime_quote(symbol.upper())
            quotes.append(quote)
        except Exception as e:
            logger.warning(f"Failed to get quote for {symbol}: {str(e)}")
            continue
    return quotes

async def get_market_overview() -> Dict:
    """
    Get market overview data
    
    Returns:
        Dictionary with market statistics
    """
    # For now, return a simple overview
    # In production, this would aggregate data from multiple sources
    try:
        # Get quotes for major indices/stocks
        major_symbols = ['SPY', 'QQQ', 'DIA', 'AAPL', 'MSFT', 'GOOGL']
        quotes = await get_multiple_quotes(major_symbols)
        
        # Calculate basic statistics
        up_count = sum(1 for q in quotes if q.change >= 0)
        down_count = len(quotes) - up_count
        total_volume = sum(q.volume for q in quotes)
        
        return {
            'total_symbols': len(quotes),
            'up_count': up_count,
            'down_count': down_count,
            'total_volume': total_volume,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get market overview: {str(e)}")
        raise
