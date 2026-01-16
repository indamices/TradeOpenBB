"""
Tests for database functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from database import get_db, init_db, engine
from models import Portfolio, Base

def test_database_connection(db_session):
    """Test database connection"""
    assert db_session is not None

def test_database_init(db_session):
    """Test database initialization"""
    # Tables should be created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "portfolios" in tables or "portfolio" in tables.lower()

def test_create_portfolio_in_db(db_session):
    """Test creating portfolio in database"""
    portfolio = Portfolio(
        name="Test Portfolio",
        initial_cash=100000.0,
        current_cash=100000.0,
        total_value=100000.0
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    
    assert portfolio.id is not None
    assert portfolio.name == "Test Portfolio"

def test_init_db_creates_default_portfolio(db_session):
    """Test that init_db creates default portfolio if it doesn't exist"""
    # Drop all tables first
    Base.metadata.drop_all(bind=engine)
    
    # Reinitialize
    init_db()
    
    # Check that default portfolio exists
    from database import SessionLocal
    db = SessionLocal()
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.id == 1).first()
        assert portfolio is not None
        assert portfolio.id == 1
        assert portfolio.name == "Default Portfolio"
    finally:
        db.close()

def test_init_db_handles_existing_portfolio(db_session):
    """Test that init_db doesn't create duplicate default portfolio"""
    # Create default portfolio manually
    default_portfolio = Portfolio(
        id=1,
        name="Existing Default Portfolio",
        initial_cash=50000.0,
        current_cash=50000.0,
        total_value=50000.0
    )
    db_session.add(default_portfolio)
    db_session.commit()
    
    # Call init_db - should not create duplicate
    init_db()
    
    # Verify only one portfolio with id=1 exists
    from database import SessionLocal
    db = SessionLocal()
    try:
        portfolios = db.query(Portfolio).filter(Portfolio.id == 1).all()
        assert len(portfolios) == 1
        assert portfolios[0].name == "Existing Default Portfolio"
    finally:
        db.close()
