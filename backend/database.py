"""
Database configuration and session management
Supports both SQLite (default) and PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

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
    pass

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
    # Import here to avoid circular imports
    try:
        from . import models
        Base = models.Base
        Portfolio = models.Portfolio
    except ImportError:
        from models import Base, Portfolio
        Base.metadata.create_all(bind=engine)
    else:
        Base.metadata.create_all(bind=engine)
    
    # Create default portfolio if it doesn't exist
    db = SessionLocal()
    try:
        # Check if any portfolio exists
        existing_portfolio = db.query(Portfolio).first()
        if not existing_portfolio:
            # Create default portfolio
            default_portfolio = Portfolio(
                name="Default Portfolio",
                initial_cash=100000.0,
                current_cash=100000.0,
                total_value=100000.0
            )
            db.add(default_portfolio)
            db.commit()
            print("Created default portfolio")
        else:
            # Ensure portfolio with id=1 exists (for backward compatibility)
            portfolio_1 = db.query(Portfolio).filter(Portfolio.id == 1).first()
            if not portfolio_1:
                # If no portfolio with id=1, but others exist, create one
                default_portfolio = Portfolio(
                    id=1,
                    name="Default Portfolio",
                    initial_cash=100000.0,
                    current_cash=100000.0,
                    total_value=100000.0
                )
                db.add(default_portfolio)
                db.commit()
                print("Created portfolio with id=1")
    except Exception as e:
        print(f"Error creating default portfolio: {str(e)}")
        db.rollback()
    finally:
        db.close()
