"""
Data service for fetching historical market data with caching
Implements multi-level cache strategy:
L1: Memory cache (TTLCache)
L2: Database cache (persistent storage)
L3: API calls (with rate limiting)
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from .cache_service import CacheService
from .rate_limiter import rate_limiter

try:
    from ..models import MarketData, DataSyncLog
    from ..openbb_service import openbb_service
    from ..database import SessionLocal
except ImportError:
    from models import MarketData, DataSyncLog
    from openbb_service import openbb_service
    from database import SessionLocal

logger = logging.getLogger(__name__)


class DataService:
    """Service for fetching and managing market data with caching"""
    
    def __init__(self, db: Optional[Session] = None, source_id: Optional[int] = None):
        self.db = db or SessionLocal()
        self.source_id = source_id  # Optional: specific data source to use
        self.test_source_id = None  # For testing purposes
    
    def close(self):
        """Close database session if it was created here"""
        if self.db and hasattr(self.db, 'close'):
            self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get historical data with multi-level caching
        
        Priority:
        1. L1 cache (memory)
        2. L2 cache (database)
        3. API call (with rate limiting)
        
        Args:
            symbol: Stock symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            use_cache: Whether to use cache (default: True)
        
        Returns:
            DataFrame with historical OHLCV data
        """
        symbol = symbol.upper()
        
        # 1. Check L1 cache
        if use_cache:
            cached_data = CacheService.get_historical(symbol, start_date, end_date)
            if cached_data is not None:
                logger.debug(f"L1 cache hit for {symbol} ({start_date} to {end_date})")
                return cached_data
        
        # 2. Check database (L2 cache)
        db_data = self._get_from_database(symbol, start_date, end_date)
        
        if db_data is not None and not db_data.empty:
            # Check data completeness
            missing_ranges = self._find_missing_dates(db_data, start_date, end_date)
            
            if not missing_ranges:
                # Data is complete
                logger.debug(f"L2 cache complete for {symbol} ({start_date} to {end_date})")
                # Update L1 cache
                CacheService.set_historical(symbol, start_date, end_date, db_data)
                return db_data
            else:
                # Incremental fetch missing data
                logger.info(f"L2 cache partial for {symbol}, fetching {len(missing_ranges)} missing ranges")
                for missing_start, missing_end in missing_ranges:
                    try:
                        new_data = await self._fetch_from_api(symbol, missing_start, missing_end)
                        if new_data is not None and not new_data.empty:
                            self._save_to_database(symbol, new_data)
                            # Merge with existing data
                            db_data = pd.concat([db_data, new_data]).sort_index().drop_duplicates()
                    except Exception as e:
                        logger.error(f"Failed to fetch missing data for {symbol} ({missing_start} to {missing_end}): {e}")
                        continue
                
                # Update L1 cache with merged data
                CacheService.set_historical(symbol, start_date, end_date, db_data)
                return db_data
        
        # 3. Fetch from API if database has no data
        logger.info(f"Fetching {symbol} data from API ({start_date} to {end_date})")
        api_data = await self._fetch_from_api(symbol, start_date, end_date)
        
        if api_data is not None and not api_data.empty:
            # Save to database
            self._save_to_database(symbol, api_data)
            # Update L1 cache
            CacheService.set_historical(symbol, start_date, end_date, api_data)
            return api_data
        
        # Return empty DataFrame if all fails
        logger.warning(f"No data available for {symbol} ({start_date} to {end_date})")
        return pd.DataFrame()
    
    def _get_from_database(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Get historical data from database"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            records = self.db.query(MarketData).filter(
                and_(
                    MarketData.symbol == symbol,
                    MarketData.date >= start,
                    MarketData.date <= end
                )
            ).order_by(MarketData.date).all()
            
            if not records:
                return None
            
            # Convert to DataFrame
            data = {
                'Open': [r.open for r in records],
                'High': [r.high for r in records],
                'Low': [r.low for r in records],
                'Close': [r.close for r in records],
                'Volume': [r.volume for r in records]
            }
            dates = [r.date for r in records]
            
            df = pd.DataFrame(data, index=pd.DatetimeIndex(dates))
            return df
            
        except Exception as e:
            logger.error(f"Error fetching from database for {symbol}: {e}")
            return None
    
    def _find_missing_dates(self, df: pd.DataFrame, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """Find missing date ranges in the DataFrame"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if df.empty:
                return [(start_date, end_date)]
            
            # Get all dates in range (excluding weekends)
            all_dates = pd.bdate_range(start=start, end=end)
            df_dates = set(df.index.date)
            
            missing_dates = [d.date() for d in all_dates if d.date() not in df_dates]
            
            if not missing_dates:
                return []
            
            # Group consecutive missing dates into ranges
            missing_ranges = []
            range_start = missing_dates[0]
            
            for i in range(1, len(missing_dates)):
                if (missing_dates[i] - missing_dates[i-1]).days > 1:
                    # Gap found, close current range
                    missing_ranges.append((
                        range_start.isoformat(),
                        missing_dates[i-1].isoformat()
                    ))
                    range_start = missing_dates[i]
            
            # Add final range
            missing_ranges.append((
                range_start.isoformat(),
                missing_dates[-1].isoformat()
            ))
            
            return missing_ranges
            
        except Exception as e:
            logger.error(f"Error finding missing dates: {e}")
            return [(start_date, end_date)]
    
    async def _fetch_from_api(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch data from API with rate limiting and data source selection"""
        try:
            # Use rate limiter for API calls
            await rate_limiter.wait_if_needed()
            
            # Determine which data source to use
            source_to_use = self.test_source_id or self.source_id
            
            if source_to_use:
                # Use specific data source
                try:
                    from models import DataSourceConfig
                    db_source = self.db.query(DataSourceConfig).filter(
                        DataSourceConfig.id == source_to_use,
                        DataSourceConfig.is_active == True
                    ).first()
                    
                    if db_source and db_source.provider:
                        logger.info(f"Using data source: {db_source.name} (provider: {db_source.provider})")
                        # For now, support openbb and yfinance providers
                        # Future: Add support for other providers based on db_source.provider
                        if db_source.provider.lower() in ['openbb', 'yfinance']:
                            data = openbb_service.get_stock_data(symbol, start_date, end_date)
                            if data is not None and not data.empty:
                                return data
                except Exception as e:
                    logger.warning(f"Failed to use specified data source {source_to_use}: {e}")
            
            # Fallback: Try active data sources by priority
            try:
                from models import DataSourceConfig
                active_sources = self.db.query(DataSourceConfig).filter(
                    DataSourceConfig.is_active == True
                ).order_by(DataSourceConfig.priority.desc(), DataSourceConfig.is_default.desc()).all()
                
                for db_source in active_sources:
                    try:
                        logger.info(f"Trying data source: {db_source.name} (provider: {db_source.provider})")
                        if db_source.provider and db_source.provider.lower() in ['openbb', 'yfinance']:
                            data = openbb_service.get_stock_data(symbol, start_date, end_date)
                            if data is not None and not data.empty:
                                logger.info(f"Successfully fetched data using {db_source.name}")
                                return data
                    except Exception as e:
                        logger.warning(f"Data source {db_source.name} failed: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error querying data sources: {e}")
            
            # Final fallback: Use openbb_service directly
            logger.info(f"Using default openbb_service for {symbol}")
            data = openbb_service.get_stock_data(symbol, start_date, end_date)
            
            if data is not None and not data.empty:
                return data
            else:
                logger.warning(f"No data returned from API for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from API for {symbol}: {e}")
            return None
    
    def _save_to_database(self, symbol: str, df: pd.DataFrame):
        """Save DataFrame to database"""
        try:
            if df.empty:
                return
            
            # Convert DataFrame to MarketData records
            records = []
            for date_idx, row in df.iterrows():
                # Handle different date formats
                if isinstance(date_idx, pd.Timestamp):
                    date_val = date_idx.date()
                elif isinstance(date_idx, date):
                    date_val = date_idx
                else:
                    date_val = pd.to_datetime(date_idx).date()
                
                # Check if record already exists
                existing = self.db.query(MarketData).filter(
                    and_(
                        MarketData.symbol == symbol,
                        MarketData.date == date_val
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    existing.open = float(row['Open'])
                    existing.high = float(row['High'])
                    existing.low = float(row['Low'])
                    existing.close = float(row['Close'])
                    existing.volume = int(row['Volume'])
                    existing.updated_at = datetime.now()
                else:
                    # Create new record
                    record = MarketData(
                        symbol=symbol,
                        date=date_val,
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume'])
                    )
                    records.append(record)
            
            # Bulk insert new records
            if records:
                self.db.add_all(records)
            
            # Commit changes
            self.db.commit()
            logger.info(f"Saved {len(records)} new records for {symbol} to database")
            
        except Exception as e:
            logger.error(f"Error saving to database for {symbol}: {e}")
            self.db.rollback()
            raise
    
    async def batch_fetch_historical_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Batch fetch historical data for multiple symbols with rate limiting
        
        Args:
            symbols: List of stock symbols
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        async def fetch_func(symbol: str):
            return await self.get_historical_data(symbol, start_date, end_date)
        
        results = await rate_limiter.batch_fetch(symbols, fetch_func)
        
        # Build result dictionary
        result_dict = {}
        for symbol, data in zip(symbols, results):
            if isinstance(data, Exception):
                logger.error(f"Failed to fetch {symbol}: {data}")
                result_dict[symbol] = pd.DataFrame()
            else:
                result_dict[symbol] = data
        
        return result_dict
