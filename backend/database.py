"""
Database configuration and session management
Supports both SQLite (default) and PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Support both PostgreSQL and SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

# If no DATABASE_URL or it's empty, use SQLite
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./smartquant.db"
elif DATABASE_URL.startswith("sqlite"):
    # SQLite URL is already set
    pass
else:
    # PostgreSQL URL
    # Fix for Render: If using internal connection string (dpg-xxxxx-a), convert to external
    # Internal format: postgresql://user:pass@dpg-xxxxx-a/dbname
    # External format: postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com/dbname
    import re
    # Check if it's a Render internal connection string (contains dpg-xxxxx-a without domain)
    pattern = r'postgresql://([^@]+)@(dpg-[a-z0-9]+-a)(?:/|$)'
    match = re.search(pattern, DATABASE_URL)
    if match and '.render.com' not in DATABASE_URL and '.oregon-postgres' not in DATABASE_URL:
        # It's an internal connection string, try to convert to external
        # Extract credentials and database name
        credentials = match.group(1)
        hostname = match.group(2)
        # Try to extract database name
        db_match = re.search(r'@dpg-[a-z0-9]+-a(?:/|$)(.*?)(?:$|\?)', DATABASE_URL)
        db_name = db_match.group(1) if db_match else 'smartquant_db'
        # Construct external connection string
        external_url = f"postgresql://{credentials}@{hostname}.oregon-postgres.render.com/{db_name}"
        logger.warning(f"Detected Render internal connection string, attempting to use external format")
        logger.warning(f"Original: {DATABASE_URL[:50]}...")
        logger.warning(f"Using: {external_url[:50]}...")
        logger.warning("If connection still fails, manually set DATABASE_URL in Render Dashboard using External Connection String")
        DATABASE_URL = external_url

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=False
    )
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and create default data"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Import here to avoid circular imports
    try:
        from . import models
        Base = models.Base
        Portfolio = models.Portfolio
    except ImportError:
        from models import Base, Portfolio
    
    # Create all tables (including new ones)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/updated successfully")
    
    # Create default portfolio with id=1 if it doesn't exist
    db = SessionLocal()
    try:
        # Check if portfolio with id=1 exists
        portfolio_1 = db.query(Portfolio).filter(Portfolio.id == 1).first()
        if not portfolio_1:
            # Create default portfolio with id=1
            default_portfolio = Portfolio(
                id=1,  # Explicitly set id=1
                name="Default Portfolio",
                initial_cash=100000.0,
                current_cash=100000.0,
                total_value=100000.0,
                daily_pnl=0.0,
                daily_pnl_percent=0.0
            )
            db.add(default_portfolio)
            db.commit()
            db.refresh(default_portfolio)
            logger.info(f"Created default portfolio with ID: {default_portfolio.id}")
        else:
            logger.info(f"Default portfolio (ID=1) already exists")
    except Exception as e:
        logger.error(f"Error creating default portfolio: {str(e)}", exc_info=True)
        db.rollback()
        raise  # Re-raise to prevent app from starting with invalid state
    finally:
        db.close()
