import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging
import time
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Cache for market data (10 second TTL to reduce API calls and rate limiting)
quote_cache = TTLCache(maxsize=500, ttl=10)
data_cache = TTLCache(maxsize=200, ttl=60)  # Historical data cached longer

# Rate limiting: track last request time per symbol
_last_request_time = {}
_min_request_interval = 0.5  # Minimum 0.5 seconds between requests for same symbol

# Try to import OpenBB, but make it optional
try:
    from openbb_terminal.sdk import openbb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    logger.warning("OpenBB Terminal not available. Using yfinance as fallback.")

class OpenBBService:
    """Service for interacting with OpenBB SDK or yfinance"""
    
    @staticmethod
    def get_stock_data(symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get historical stock data using OpenBB or yfinance
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (default: today)
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Try OpenBB first if available
            if OPENBB_AVAILABLE:
                try:
                    data = openbb.stocks.load(symbol=symbol, start_date=start_date, end_date=end_date)
                    if data is not None and not data.empty:
                        # Ensure required columns exist
                        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        missing_columns = [col for col in required_columns if col not in data.columns]
                        
                        if missing_columns:
                            # Try to map common column names
                            column_mapping = {
                                'open': 'Open',
                                'high': 'High',
                                'low': 'Low',
                                'close': 'Close',
                                'volume': 'Volume'
                            }
                            for old_col, new_col in column_mapping.items():
                                if old_col in data.columns.str.lower():
                                    data[new_col] = data[old_col]
                        
                        # Select only required columns
                        available_columns = [col for col in required_columns if col in data.columns]
                        data = data[available_columns]
                        return data
                except Exception as e:
                    logger.warning(f"OpenBB failed for {symbol}, falling back to yfinance: {str(e)}")
            
            # Fallback to yfinance with retry
            import yfinance as yf
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(retry_delay * attempt)
                    
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(start=start_date, end=end_date)
                    
                    if not data.empty:
                        break
                except Exception as e:
                    error_msg = str(e).lower()
                    if "rate limit" in error_msg or "too many requests" in error_msg or "429" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited for {symbol} data, retrying after {wait_time}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise ValueError(f"Too Many Requests. Rate limited. Try after a while.")
                    else:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        raise
            
            if data is None or data.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Rename columns to match expected format
            data = data.rename(columns={
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            # Select only required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            available_columns = [col for col in required_columns if col in data.columns]
            data = data[available_columns]
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            raise
    
    @staticmethod
    def get_realtime_quote(symbol: str) -> Dict:
        """
        Get real-time quote using OpenBB or yfinance
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dictionary with quote information
        """
        try:
            # Try OpenBB first if available
            if OPENBB_AVAILABLE:
                try:
                    quote_data = openbb.stocks.quote(symbol)
                    
                    if quote_data is not None and not quote_data.empty:
                        # Parse quote data (format may vary)
                        if isinstance(quote_data, pd.DataFrame):
                            quote = quote_data.iloc[0].to_dict()
                        else:
                            quote = quote_data
                        
                        # Extract price information
                        price = float(quote.get('Price', quote.get('price', quote.get('Last Price', 0))))
                        change = float(quote.get('Change', quote.get('change', 0)))
                        change_percent = float(quote.get('Change %', quote.get('change_percent', 0)))
                        volume = int(quote.get('Volume', quote.get('volume', 0)))
                        
                        return {
                            'price': price,
                            'change': change,
                            'change_percent': change_percent,
                            'volume': volume
                        }
                except Exception as e:
                    logger.warning(f"OpenBB quote failed for {symbol}, using yfinance: {str(e)}")
            
            # Check cache first
            cache_key = f"quote:{symbol}"
            if cache_key in quote_cache:
                return quote_cache[cache_key]
            
            # Rate limiting: ensure minimum interval between requests for same symbol
            current_time = time.time()
            if symbol in _last_request_time:
                time_since_last = current_time - _last_request_time[symbol]
                if time_since_last < _min_request_interval:
                    wait_time = _min_request_interval - time_since_last
                    time.sleep(wait_time)
            _last_request_time[symbol] = time.time()
            
            # Use yfinance as primary/fallback with retry logic
            import yfinance as yf
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # Add delay between requests to avoid rate limiting
                    if attempt > 0:
                        time.sleep(retry_delay * attempt)
                    
                    info = ticker.info
                    hist = ticker.history(period="1d")
                    
                    if hist.empty:
                        if attempt < max_retries - 1:
                            continue  # Retry
                        raise ValueError(f"No quote data found for {symbol}")
                    
                    current_price = float(hist['Close'].iloc[-1])
                    prev_close = float(info.get('previousClose', current_price))
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
                    
                    result = {
                        'price': current_price,
                        'change': change,
                        'change_percent': change_percent,
                        'volume': int(hist['Volume'].iloc[-1])
                    }
                    
                    # Cache the result
                    quote_cache[cache_key] = result
                    return result
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    # Check for rate limiting
                    if "rate limit" in error_msg or "too many requests" in error_msg or "429" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Rate limited for {symbol}, retrying after {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Rate limit exceeded for {symbol} after {max_retries} attempts")
                            raise ValueError(f"Too Many Requests. Rate limited. Try after a while.")
                    else:
                        if attempt < max_retries - 1:
                            logger.warning(f"Error fetching quote for {symbol} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
                            raise ValueError(f"Failed to get quote for {symbol}: {str(e)}")
            
            # Should not reach here, but just in case
            raise ValueError(f"Failed to get quote for {symbol} after {max_retries} attempts")
            
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.error(f"Unexpected error fetching quote for {symbol}: {str(e)}")
            raise ValueError(f"Failed to get quote for {symbol}: {str(e)}")
    
    @staticmethod
    def get_technical_indicators(symbol: str, indicators: List[str], period: int = 20) -> pd.DataFrame:
        """
        Get technical indicators using OpenBB or yfinance
        
        Args:
            symbol: Stock symbol
            indicators: List of indicator names (e.g., ['sma', 'rsi', 'macd'])
            period: Period for indicators
        
        Returns:
            DataFrame with indicator values
        """
        try:
            # Get historical data first
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=period * 2)).strftime('%Y-%m-%d')
            
            # Try OpenBB first if available
            data = None
            if OPENBB_AVAILABLE:
                try:
                    data = openbb.stocks.load(symbol=symbol, start_date=start_date, end_date=end_date)
                except Exception as e:
                    logger.warning(f"OpenBB failed for {symbol}, using yfinance: {str(e)}")
            
            # Fallback to yfinance with retry
            if data is None or data.empty:
                import yfinance as yf
                max_retries = 3
                retry_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            time.sleep(retry_delay * attempt)
                        
                        ticker = yf.Ticker(symbol)
                        data = ticker.history(start=start_date, end=end_date)
                        
                        if not data.empty:
                            break
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "rate limit" in error_msg or "too many requests" in error_msg or "429" in error_msg:
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (2 ** attempt)
                                logger.warning(f"Rate limited for {symbol} historical data, retrying after {wait_time}s")
                                time.sleep(wait_time)
                                continue
                            else:
                                raise ValueError(f"Too Many Requests. Rate limited. Try after a while.")
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                            raise
                
                if data is None or data.empty:
                    raise ValueError(f"No data found for symbol {symbol}")
                
                # Rename columns
                data = data.rename(columns={
                    'Open': 'Open',
                    'High': 'High',
                    'Low': 'Low',
                    'Close': 'Close',
                    'Volume': 'Volume'
                })
            
            if data is None or data.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            result = pd.DataFrame(index=data.index)
            
            # Calculate indicators
            for indicator in indicators:
                try:
                    if indicator.lower() == 'sma':
                        result['SMA'] = data['Close'].rolling(window=period).mean()
                    elif indicator.lower() == 'ema':
                        result['EMA'] = data['Close'].ewm(span=period).mean()
                    elif indicator.lower() == 'rsi':
                        # RSI calculation
                        delta = data['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                        rs = gain / loss
                        result['RSI'] = 100 - (100 / (1 + rs))
                    elif indicator.lower() == 'macd':
                        ema12 = data['Close'].ewm(span=12).mean()
                        ema26 = data['Close'].ewm(span=26).mean()
                        result['MACD'] = ema12 - ema26
                        result['MACD_Signal'] = result['MACD'].ewm(span=9).mean()
                    elif indicator.lower() == 'bb':
                        # Bollinger Bands
                        sma = data['Close'].rolling(window=period).mean()
                        std = data['Close'].rolling(window=period).std()
                        result['BB_Upper'] = sma + (std * 2)
                        result['BB_Lower'] = sma - (std * 2)
                        result['BB_Middle'] = sma
                except Exception as e:
                    logger.warning(f"Failed to calculate {indicator} for {symbol}: {str(e)}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {str(e)}")
            raise

# Create singleton instance
openbb_service = OpenBBService()
