"""
Task scheduler for background data synchronization
Uses APScheduler for scheduling tasks
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import APScheduler, but make it optional
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not available. Task scheduling disabled.")


class TaskScheduler:
    """Task scheduler for background jobs"""
    
    def __init__(self):
        if APSCHEDULER_AVAILABLE:
            self.scheduler = AsyncIOScheduler()
            self._setup_jobs()
        else:
            self.scheduler = None
            logger.warning("Task scheduler not initialized: APScheduler not available")
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        if not APSCHEDULER_AVAILABLE:
            return
        
        # Daily data sync at 2 AM (avoid trading hours)
        self.scheduler.add_job(
            self._daily_data_sync,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_data_sync',
            name='Daily Market Data Sync',
            replace_existing=True
        )
        
        # Stock info sync at 3 AM (after data sync)
        self.scheduler.add_job(
            self._daily_stock_info_sync,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_stock_info_sync',
            name='Daily Stock Info Sync',
            replace_existing=True
        )
        
        logger.info("Task scheduler jobs configured")
    
    async def _daily_data_sync(self):
        """Daily data synchronization task"""
        try:
            logger.info("Starting scheduled daily data sync")
            from .data_sync_service import DataSyncService
            
            async with DataSyncService() as sync_service:
                await sync_service.daily_sync()
            
            logger.info("Scheduled daily data sync completed")
            
        except Exception as e:
            logger.error(f"Scheduled daily data sync failed: {e}", exc_info=True)
    
    async def _daily_stock_info_sync(self):
        """Daily stock info synchronization task"""
        try:
            logger.info("Starting scheduled daily stock info sync")
            from .data_sync_service import DataSyncService
            from ..database import SessionLocal
            from ..models import StockPool
            
            db = SessionLocal()
            try:
                # Get all symbols from stock pools
                pools = db.query(StockPool).all()
                symbols = set()
                for pool in pools:
                    if pool.symbols:
                        symbols.update(pool.symbols)
                
                if symbols:
                    async with DataSyncService(db=db) as sync_service:
                        await sync_service.sync_stock_info(list(symbols))
                
                logger.info("Scheduled daily stock info sync completed")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Scheduled daily stock info sync failed: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        if self.scheduler:
            self.scheduler.start()
            logger.info("Task scheduler started")
        else:
            logger.warning("Task scheduler not available")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Task scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        if self.scheduler:
            return self.scheduler.running
        return False


# Global scheduler instance
scheduler = TaskScheduler()
