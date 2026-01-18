"""
Alpha Vantage API service for fetching market data
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
import requests
import time
from cachetools import TTLCache
import os

logger = logging.getLogger(__name__)

# Get API key from environment
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "23QHIAUTJM0L72OE")
BASE_URL = "https://www.alphavantage.co/query"

# Cache configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
QUOTE_CACHE_TTL = 60 if ENVIRONMENT == "production" else 120
quote_cache = TTLCache(maxsize=500, ttl=QUOTE_CACHE_TTL)
data_cache = TTLCache(maxsize=200, ttl=86400)  # 24 hours

# Rate limiting: Alpha Vantage free tier allows 5 API calls per minute
_last_request_time = {}
_min_request_interval = 12.0  # 12 seconds = 5 requests per minute


class AlphaVantageService:
    """Service for interacting with Alpha Vantage API"""
    
    @staticmethod
    def _wait_for_rate_limit():
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        if 'last_request' in _last_request_time:
            time_since_last = current_time - _last_request_time['last_request']
            if time_since_last < _min_request_interval:
                wait_time = _min_request_interval - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
        _last_request_time['last_request'] = time.time()
    
    @staticmethod
    def get_stock_data(symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get historical stock data from Alpha Vantage
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (default: today)
        
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume
        """
        if not ALPHA_VANTAGE_API_KEY:
            raise ValueError("Alpha Vantage API key not configured. Set ALPHA_VANTAGE_API_KEY environment variable.")
        
        # Check cache first
        cache_key = f"{symbol}_{start_date}_{end_date or 'today'}"
        if cache_key in data_cache:
            logger.debug(f"Cache hit for {symbol} from Alpha Vantage")
            return data_cache[cache_key]
        
        # Wait for rate limit
        AlphaVantageService._wait_for_rate_limit()
        
        try:
            # Alpha Vantage TIME_SERIES_DAILY endpoint
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'  # Use 'full' for 20+ years of data, 'compact' for last 100 data points
            }
            
            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            if 'Note' in data:
                # Rate limit exceeded
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                raise ValueError(f"Alpha Vantage API rate limit exceeded. Please wait before trying again.")
            
            if 'Time Series (Daily)' not in data:
                raise ValueError(f"No data returned from Alpha Vantage for {symbol}")
            
            # Parse the data
            time_series = data['Time Series (Daily)']
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df.index.name = 'Date'
            
            # Rename columns
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by date
            df = df.sort_index()
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            if end_date:
                end_dt = pd.to_datetime(end_date)
            else:
                end_dt = pd.Timestamp.today()
            
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            
            if df.empty:
                logger.warning(f"No data found for {symbol} in date range {start_date} to {end_date}")
                return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Cache the result
            data_cache[cache_key] = df
            
            logger.info(f"Fetched {len(df)} days of data for {symbol} from Alpha Vantage")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Alpha Vantage for {symbol}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing Alpha Vantage data for {symbol}: {str(e)}")
            raise
    
    @staticmethod
    def get_realtime_quote(symbol: str) -> Dict:
        """
        Get real-time quote from Alpha Vantage
        
        Note: Alpha Vantage free tier only provides delayed quotes (15 minutes)
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dict with quote data
        """
        if not ALPHA_VANTAGE_API_KEY:
            raise ValueError("Alpha Vantage API key not configured.")
        
        # Check cache first
        cache_key = f"quote_{symbol}"
        if cache_key in quote_cache:
            logger.debug(f"Cache hit for quote {symbol} from Alpha Vantage")
            return quote_cache[cache_key]
        
        # Wait for rate limit
        AlphaVantageService._wait_for_rate_limit()
        
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for errors
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                raise ValueError("Alpha Vantage API rate limit exceeded.")
            
            if 'Global Quote' not in data or not data['Global Quote']:
                raise ValueError(f"No quote data returned from Alpha Vantage for {symbol}")
            
            quote = data['Global Quote']
            
            result = {
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': float(quote.get('10. change percent', '0%').rstrip('%')),
                'volume': int(quote.get('06. volume', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'open': float(quote.get('02. open', 0)),
                'previous_close': float(quote.get('08. previous close', 0))
            }
            
            # Cache the result
            quote_cache[cache_key] = result
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching quote from Alpha Vantage for {symbol}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing Alpha Vantage quote for {symbol}: {str(e)}")
            raise
    
    @staticmethod
    def is_available() -> bool:
        """Check if Alpha Vantage service is available"""
        return bool(ALPHA_VANTAGE_API_KEY)


# Create singleton instance
alpha_vantage_service = AlphaVantageService()
