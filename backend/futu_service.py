"""
Futu OpenAPI service for fetching market data
富途牛牛API服务 - 用于获取市场数据
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import os

logger = logging.getLogger(__name__)

# Try to import futu library
try:
    import futu as ft
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False
    logger.warning("Futu library not available. Install with: pip install futu")

# Configuration
FUTU_HOST = os.getenv("FUTU_HOST", "127.0.0.1")
FUTU_PORT = int(os.getenv("FUTU_PORT", "11111"))
FUTU_MARKET = os.getenv("FUTU_MARKET", "US")  # US, HK, CN


class FutuService:
    """Service for interacting with Futu OpenAPI"""
    
    def __init__(self, host: str = FUTU_HOST, port: int = FUTU_PORT):
        """
        Initialize Futu service
        
        Args:
            host: OpenD host (default: 127.0.0.1)
            port: OpenD port (default: 11111)
        """
        self.host = host
        self.port = port
        self.quote_ctx: Optional[ft.OpenQuoteContext] = None
        self.market = FUTU_MARKET
    
    def _ensure_connected(self):
        """Ensure connection to OpenD is established"""
        if not FUTU_AVAILABLE:
            raise ValueError("Futu library not available. Install with: pip install futu")

        if self.quote_ctx is None:
            try:
                self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
                logger.info(f"Connected to Futu OpenD at {self.host}:{self.port}")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to connect to Futu OpenD: {error_msg}")

                # Provide helpful error messages
                if "11111" in error_msg or "Connection" in error_msg:
                    raise ValueError(
                        f"Cannot connect to Futu OpenD at {self.host}:{self.port}. "
                        f"Please ensure Futu OpenD (OpenD) is running. "
                        f"Download from: https://openapi.futunn.com/download "
                        f"Start with: 'opend --time_zone Asia/Shanghai'"
                    )
                else:
                    raise ValueError(f"Failed to connect to Futu OpenD: {error_msg}")
    
    def _get_market(self, symbol: str):
        """Determine market from symbol"""
        # Simple heuristic: if symbol ends with numbers, it's likely HK or CN
        # For US, symbols are usually letters
        if not FUTU_AVAILABLE:
            # Return string representation if futu not available
            if symbol.endswith('.HK'):
                return 'HK'
            elif symbol.endswith('.SH') or symbol.endswith('.SZ'):
                return 'SH' if symbol.endswith('.SH') else 'SZ'
            else:
                return 'US'
        
        if symbol.endswith('.HK'):
            return ft.Market.HK
        elif symbol.endswith('.SH') or symbol.endswith('.SZ'):
            return ft.Market.SH if symbol.endswith('.SH') else ft.Market.SZ
        else:
            return ft.Market.US
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical stock data from Futu
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL' for US, '00700.HK' for HK)
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (default: today)
        
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume
        """
        if not FUTU_AVAILABLE:
            raise ValueError("Futu library not available. Install with: pip install futu")
        
        self._ensure_connected()
        
        try:
            # Determine market
            market = self._get_market(symbol)
            
            # Prepare dates
            start_dt = pd.to_datetime(start_date)
            if end_date:
                end_dt = pd.to_datetime(end_date)
            else:
                end_dt = pd.Timestamp.today()
            
            # Convert dates to Futu format (YYYY-MM-DD)
            start_str = start_dt.strftime('%Y-%m-%d')
            end_str = end_dt.strftime('%Y-%m-%d')
            
            # Get historical kline data
            ret, data, page_req_key = self.quote_ctx.request_history_kline(
                code=symbol,
                start=start_str,
                end=end_str,
                ktype=ft.KLType.K_DAY,  # Daily kline
                autype=ft.AuType.QFQ,  # Forward adjustment
                fields=[ft.KL_FIELD.ALL],
                max_count=1000  # Maximum records per request
            )
            
            if ret != ft.RET_OK:
                raise ValueError(f"Futu API error: {data}")
            
            if data is None or data.empty:
                logger.warning(f"No data returned from Futu for {symbol}")
                return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Convert to our format
            df = data.copy()
            
            # Rename columns if needed
            # Futu returns: time_key, open, high, low, close, volume, turnover, etc.
            column_mapping = {
                'time_key': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure Date is datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
            
            # Select only needed columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            available_columns = [col for col in required_columns if col in df.columns]
            df = df[available_columns]
            
            # Sort by date
            df = df.sort_index()
            
            logger.info(f"Fetched {len(df)} days of data for {symbol} from Futu")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from Futu for {symbol}: {str(e)}")
            raise
    
    def get_realtime_quote(self, symbol: str) -> Dict:
        """
        Get real-time quote from Futu
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dict with quote data
        """
        if not FUTU_AVAILABLE:
            raise ValueError("Futu library not available.")
        
        self._ensure_connected()
        
        try:
            market = self._get_market(symbol)
            
            # Get market snapshot
            ret, data = self.quote_ctx.get_market_snapshot([symbol])
            
            if ret != ft.RET_OK:
                raise ValueError(f"Futu API error: {data}")
            
            if data is None or data.empty:
                raise ValueError(f"No quote data returned from Futu for {symbol}")
            
            # Extract quote data
            row = data.iloc[0]
            
            result = {
                'price': float(row.get('last_price', 0)),
                'change': float(row.get('change_val', 0)),
                'change_percent': float(row.get('change_rate', 0)) * 100,  # Convert to percentage
                'volume': int(row.get('volume', 0)),
                'high': float(row.get('high_price', 0)),
                'low': float(row.get('low_price', 0)),
                'open': float(row.get('open_price', 0)),
                'previous_close': float(row.get('prev_close_price', 0))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching quote from Futu for {symbol}: {str(e)}")
            raise
    
    def get_capital_flow(
        self,
        symbol: str,
        period: str = "day"  # day, week, month, year
    ) -> Dict:
        """
        Get capital flow data from Futu
        
        Args:
            symbol: Stock symbol
            period: Time period (day, week, month, year)
        
        Returns:
            Dict with capital flow data
        """
        if not FUTU_AVAILABLE:
            raise ValueError("Futu library not available.")
        
        self._ensure_connected()
        
        try:
            market = self._get_market(symbol)

            # Map period to Futu's period type (handle different API versions)
            period_map = {}

            # Check if CapitalFlowPeriod exists and has required attributes
            if hasattr(ft, 'CapitalFlowPeriod'):
                if hasattr(ft.CapitalFlowPeriod, 'DAY'):
                    period_map['day'] = ft.CapitalFlowPeriod.DAY
                if hasattr(ft.CapitalFlowPeriod, 'WEEK'):
                    period_map['week'] = ft.CapitalFlowPeriod.WEEK
                if hasattr(ft.CapitalFlowPeriod, 'MONTH'):
                    period_map['month'] = ft.CapitalFlowPeriod.MONTH
                if hasattr(ft.CapitalFlowPeriod, 'YEAR'):
                    period_map['year'] = ft.CapitalFlowPeriod.YEAR

            # Fallback: try QueryType if CapitalFlowPeriod not available or incomplete
            if len(period_map) < 4 and hasattr(ft, 'QueryType'):
                period_map['day'] = ft.QueryType.DAY
                if hasattr(ft.QueryType, 'WEEK'):
                    period_map['week'] = ft.QueryType.WEEK
                else:
                    period_map['week'] = ft.QueryType.DAY
                if hasattr(ft.QueryType, 'MONTH'):
                    period_map['month'] = ft.QueryType.MONTH
                else:
                    period_map['month'] = ft.QueryType.DAY
                if hasattr(ft.QueryType, 'YEAR'):
                    period_map['year'] = ft.QueryType.YEAR
                else:
                    period_map['year'] = ft.QueryType.DAY

            if not period_map:
                raise ValueError("Cannot determine Futu period types")

            futu_period = period_map.get(period, period_map.get('day'))
            
            # Get capital flow
            ret, data = self.quote_ctx.get_capital_flow(symbol, futu_period)
            
            if ret != ft.RET_OK:
                raise ValueError(f"Futu API error: {data}")
            
            if data is None or data.empty:
                return {
                    'in_flow': 0,
                    'out_flow': 0,
                    'net_flow': 0,
                    'large_in': 0,
                    'large_out': 0,
                    'medium_in': 0,
                    'medium_out': 0,
                    'small_in': 0,
                    'small_out': 0
                }
            
            # Extract capital flow data (last row contains latest data)
            latest = data.iloc[-1]
            
            result = {
                'in_flow': float(latest.get('in_flow', 0)),
                'out_flow': float(latest.get('out_flow', 0)),
                'net_flow': float(latest.get('net_flow', 0)),
                'large_in': float(latest.get('large_in', 0)),
                'large_out': float(latest.get('large_out', 0)),
                'medium_in': float(latest.get('medium_in', 0)),
                'medium_out': float(latest.get('medium_out', 0)),
                'small_in': float(latest.get('small_in', 0)),
                'small_out': float(latest.get('small_out', 0))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching capital flow from Futu for {symbol}: {str(e)}")
            raise
    
    def close(self):
        """Close connection to OpenD"""
        if self.quote_ctx:
            try:
                self.quote_ctx.close()
                logger.info("Closed Futu OpenD connection")
            except Exception as e:
                logger.warning(f"Error closing Futu connection: {str(e)}")
            finally:
                self.quote_ctx = None
    
    def __enter__(self):
        """Context manager entry"""
        self._ensure_connected()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def is_available(self) -> bool:
        """Check if Futu service is available and connected"""
        if not FUTU_AVAILABLE:
            return False
        try:
            self._ensure_connected()
            return self.quote_ctx is not None
        except Exception:
            return False
    
    @staticmethod
    def is_available_static() -> bool:
        """Static method to check if Futu library is available"""
        return FUTU_AVAILABLE


# Create singleton instance (lazy initialization)
futu_service: Optional[FutuService] = None

def get_futu_service() -> Optional[FutuService]:
    """Get Futu service instance"""
    global futu_service
    if futu_service is None and FUTU_AVAILABLE:
        try:
            futu_service = FutuService()
        except Exception as e:
            logger.warning(f"Failed to initialize Futu service: {str(e)}")
            return None
    return futu_service
