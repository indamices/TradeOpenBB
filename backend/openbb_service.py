from openbb_terminal.sdk import openbb
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class OpenBBService:
    """Service for interacting with OpenBB SDK"""
    
    @staticmethod
    def get_stock_data(symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get historical stock data using OpenBB
        
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
            
            # Use OpenBB to load stock data
            data = openbb.stocks.load(symbol=symbol, start_date=start_date, end_date=end_date)
            
            if data is None or data.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
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
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            raise
    
    @staticmethod
    def get_realtime_quote(symbol: str) -> Dict:
        """
        Get real-time quote using OpenBB
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dictionary with quote information
        """
        try:
            # Use OpenBB to get quote
            quote_data = openbb.stocks.quote(symbol)
            
            if quote_data is None or quote_data.empty:
                # Fallback: use latest close price from historical data
                data = openbb.stocks.load(symbol=symbol, start_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'))
                if data is not None and not data.empty:
                    latest = data.iloc[-1]
                    return {
                        'price': float(latest.get('Close', latest.get('close', 0))),
                        'change': 0.0,
                        'change_percent': 0.0,
                        'volume': int(latest.get('Volume', latest.get('volume', 0)))
                    }
                raise ValueError(f"No quote data found for {symbol}")
            
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
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            # Fallback to yfinance if OpenBB fails
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    prev_close = float(info.get('previousClose', current_price))
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
                    
                    return {
                        'price': current_price,
                        'change': change,
                        'change_percent': change_percent,
                        'volume': int(hist['Volume'].iloc[-1])
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback quote fetch also failed: {str(fallback_error)}")
                raise ValueError(f"Failed to get quote for {symbol}")
    
    @staticmethod
    def get_technical_indicators(symbol: str, indicators: List[str], period: int = 20) -> pd.DataFrame:
        """
        Get technical indicators using OpenBB
        
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
            data = openbb.stocks.load(symbol=symbol, start_date=start_date, end_date=end_date)
            
            if data is None or data.empty:
                raise ValueError(f"No data found for {symbol}")
            
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
