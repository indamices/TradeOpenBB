"""
Tests for database functionality
"""
import pytest
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
