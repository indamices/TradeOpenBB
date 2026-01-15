"""
Data synchronization service for background data updates
- Daily sync: Update latest trading day data
- Incremental sync: Only fetch missing data
- Full sync: Initial or manual trigger
"""
from datetime import datetime, date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

try:
    from ..models import MarketData, DataSyncLog, StockInfo, StockPool
    from ..database import SessionLocal
    from ..openbb_service import openbb_service
    from .data_service import DataService
except ImportError:
    from models import MarketData, DataSyncLog, StockInfo, StockPool
    from database import SessionLocal
    from openbb_service import openbb_service
    from services.data_service import DataService

logger = logging.getLogger(__name__)


class DataSyncService:
    """Background data synchronization service"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
    
    def close(self):
        """Close database session if it was created here"""
        if self.db and hasattr(self.db, 'close'):
            self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def daily_sync(self, symbols: Optional[List[str]] = None):
        """
        Daily sync: Update latest trading day data
        
        Args:
            symbols: List of symbols to sync. If None, sync all symbols from stock pools.
        """
        try:
            # Get symbols to sync
            if symbols is None:
                symbols = await self._get_all_active_symbols()
            
            if not symbols:
                logger.info("No symbols to sync")
                return
            
            # Get date range (last 2 days to ensure we catch latest data)
            today = datetime.now().date()
            start_date = (today - timedelta(days=2)).isoformat()
            end_date = today.isoformat()
            
            logger.info(f"Starting daily sync for {len(symbols)} symbols")
            
            success_count = 0
            fail_count = 0
            
            async with DataService(db=self.db) as data_service:
                for symbol in symbols:
                    try:
                        # Check if sync is needed
                        last_date = self._get_last_sync_date(symbol)
                        if last_date and last_date >= (today - timedelta(days=1)):
                            logger.debug(f"Skipping {symbol}: already synced (last: {last_date})")
                            continue
                        
                        # Fetch missing data
                        data = await data_service.get_historical_data(
                            symbol=symbol,
                            start_date=start_date,
                            end_date=end_date,
                            use_cache=False  # Force fresh fetch
                        )
                        
                        if data is not None and not data.empty:
                            # Log sync
                            await self._log_sync(
                                symbol=symbol,
                                sync_type='historical',
                                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                                records_count=len(data),
                                status='success'
                            )
                            success_count += 1
                            logger.info(f"Synced {symbol}: {len(data)} records")
                        else:
                            await self._log_sync(
                                symbol=symbol,
                                sync_type='historical',
                                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                                records_count=0,
                                status='failed',
                                error_message='No data returned'
                            )
                            fail_count += 1
                            logger.warning(f"No data for {symbol}")
                            
                    except Exception as e:
                        logger.error(f"Failed to sync {symbol}: {e}")
                        await self._log_sync(
                            symbol=symbol,
                            sync_type='historical',
                            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                            end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                            records_count=0,
                            status='failed',
                            error_message=str(e)
                        )
                        fail_count += 1
                        continue
            
            logger.info(f"Daily sync completed: {success_count} success, {fail_count} failed")
            
        except Exception as e:
            logger.error(f"Daily sync failed: {e}", exc_info=True)
            raise
    
    async def sync_stock_info(self, symbols: List[str]):
        """
        Sync stock basic information (low frequency, once per day)
        
        Args:
            symbols: List of symbols to sync
        """
        try:
            import yfinance as yf
            
            logger.info(f"Syncing stock info for {len(symbols)} symbols")
            
            success_count = 0
            fail_count = 0
            
            # Import rate_limiter
            try:
                from .rate_limiter import rate_limiter
            except ImportError:
                from services.rate_limiter import rate_limiter
            
            for symbol in symbols:
                try:
                    await rate_limiter.wait_if_needed()
                    
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    if not info:
                        logger.warning(f"No info available for {symbol}")
                        fail_count += 1
                        continue
                    
                    # Extract relevant fields
                    stock_info = StockInfo(
                        symbol=symbol.upper(),
                        name=info.get('longName') or info.get('shortName'),
                        exchange=info.get('exchange'),
                        sector=info.get('sector'),
                        industry=info.get('industry'),
                        market_cap=info.get('marketCap'),
                        pe_ratio=info.get('trailingPE'),
                        updated_at=datetime.now()
                    )
                    
                    # Check if exists
                    existing = self.db.query(StockInfo).filter(
                        StockInfo.symbol == symbol.upper()
                    ).first()
                    
                    if existing:
                        # Update existing
                        for field in ['name', 'exchange', 'sector', 'industry', 'market_cap', 'pe_ratio', 'updated_at']:
                            setattr(existing, field, getattr(stock_info, field))
                    else:
                        # Create new
                        self.db.add(stock_info)
                    
                    self.db.commit()
                    success_count += 1
                    logger.debug(f"Synced stock info for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Failed to sync stock info for {symbol}: {e}")
                    fail_count += 1
                    self.db.rollback()
                    continue
            
            logger.info(f"Stock info sync completed: {success_count} success, {fail_count} failed")
            
        except Exception as e:
            logger.error(f"Stock info sync failed: {e}", exc_info=True)
            raise
    
    def _get_last_sync_date(self, symbol: str) -> Optional[date]:
        """Get last sync date for a symbol"""
        try:
            last_record = self.db.query(MarketData).filter(
                MarketData.symbol == symbol.upper()
            ).order_by(MarketData.date.desc()).first()
            
            if last_record:
                return last_record.date
            return None
            
        except Exception as e:
            logger.error(f"Error getting last sync date for {symbol}: {e}")
            return None
    
    async def _get_all_active_symbols(self) -> List[str]:
        """Get all symbols from active stock pools"""
        try:
            pools = self.db.query(StockPool).all()
            symbols = set()
            
            for pool in pools:
                if pool.symbols:
                    symbols.update(pool.symbols)
            
            return list(symbols)
            
        except Exception as e:
            logger.error(f"Error getting active symbols: {e}")
            return []
    
    async def _log_sync(
        self,
        symbol: str,
        sync_type: str,
        start_date: date,
        end_date: date,
        records_count: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log synchronization operation"""
        try:
            log = DataSyncLog(
                symbol=symbol.upper(),
                sync_type=sync_type,
                start_date=start_date,
                end_date=end_date,
                records_count=records_count,
                status=status,
                error_message=error_message
            )
            self.db.add(log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging sync: {e}")
            self.db.rollback()


# Import rate_limiter from rate_limiter module
try:
    from .rate_limiter import rate_limiter
except ImportError:
    try:
        from services.rate_limiter import rate_limiter
    except ImportError:
        from backend.services.rate_limiter import rate_limiter
