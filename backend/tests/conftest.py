"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import Base
from main import app

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    # Drop all tables first to ensure clean state
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass  # Ignore errors if tables don't exist

    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # If there's a schema prefix issue, try creating tables individually
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        for table in Base.metadata.sorted_tables:
            try:
                if table.name not in existing_tables:
                    table.create(bind=engine, checkfirst=True)
            except Exception:
                # Skip tables that fail to create
                continue

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up all data after test
        try:
            Base.metadata.drop_all(bind=engine)
        except Exception:
            pass

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override get_db dependency
    app.dependency_overrides[get_db] = override_get_db

    # Clean up any data that might have been created by init_db() during startup
    # The startup event calls init_db() which creates default AI models and portfolio
    # This pollutes the test database, breaking test isolation
    # Use safe deletion with table existence check
    try:
        from models import AIModelConfig, Portfolio
        # Check if table exists before querying
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if 'ai_model_configs' in existing_tables:
            db_session.query(AIModelConfig).delete()
            db_session.commit()

        if 'portfolios' in existing_tables:
            db_session.query(Portfolio).filter(Portfolio.id == 1).delete()
            db_session.commit()
    except Exception as e:
        # Silently ignore cleanup errors if tables don't exist yet
        pass

    with TestClient(app) as test_client:
        # Clean up again after TestClient initialization in case startup event ran
        try:
            from models import AIModelConfig, Portfolio
            from sqlalchemy import inspect
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            if 'ai_model_configs' in existing_tables:
                db_session.query(AIModelConfig).delete()

            if 'portfolios' in existing_tables:
                db_session.query(Portfolio).filter(Portfolio.id == 1).delete()

            if existing_tables:
                db_session.commit()
        except Exception:
            pass

        yield test_client

    app.dependency_overrides.clear()

    # Final cleanup after test
    try:
        from models import AIModelConfig, Portfolio
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if 'ai_model_configs' in existing_tables:
            db_session.query(AIModelConfig).delete()

        if 'portfolios' in existing_tables:
            db_session.query(Portfolio).filter(Portfolio.id == 1).delete()

        if existing_tables:
            db_session.commit()
    except Exception:
        pass

@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing"""
    return {
        "name": "Test Portfolio",
        "initial_cash": 100000.0
    }

@pytest.fixture
def default_portfolio(db_session):
    """Create a default portfolio for testing and return its ID"""
    from models import Portfolio
    # Check if portfolio with ID 1 exists
    portfolio = db_session.query(Portfolio).filter(Portfolio.id == 1).first()
    if not portfolio:
        # Create default portfolio
        portfolio = Portfolio(
            name="Test Portfolio",
            initial_cash=100000.0,
            current_cash=100000.0,
            total_value=100000.0,
            daily_pnl=0.0,
            daily_pnl_percent=0.0
        )
        db_session.add(portfolio)
        db_session.commit()
        db_session.refresh(portfolio)
    return portfolio.id

@pytest.fixture
def sample_order_data(default_portfolio):
    """Sample order data for testing"""
    return {
        "symbol": "AAPL",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 10,
        "portfolio_id": default_portfolio
    }

@pytest.fixture
def sample_position_data(default_portfolio):
    """Sample position data for testing"""
    return {
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": 150.0,
        "current_price": 155.0,
        "portfolio_id": default_portfolio
    }

@pytest.fixture
def sample_strategy_data(default_portfolio):
    """Sample strategy data for testing"""
    return {
        "name": "Test Strategy",
        "description": "A test strategy",
        "logic_code": "def strategy(data):\n    return 'BUY'",
        "target_portfolio_id": default_portfolio
    }

@pytest.fixture
def sample_ai_model_data():
    """Sample AI model config data for testing"""
    return {
        "name": "Test Gemini",
        "provider": "gemini",
        "api_key": "test_key_123",
        "model_name": "gemini-pro",
        "is_default": False
    }
