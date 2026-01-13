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
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing"""
    return {
        "name": "Test Portfolio",
        "initial_cash": 100000.0,
        "current_cash": 100000.0,
        "total_value": 100000.0
    }

@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "symbol": "AAPL",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 10,
        "price": 150.0
    }

@pytest.fixture
def sample_position_data():
    """Sample position data for testing"""
    return {
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": 150.0,
        "current_price": 155.0
    }

@pytest.fixture
def sample_strategy_data():
    """Sample strategy data for testing"""
    return {
        "name": "Test Strategy",
        "description": "A test strategy",
        "code": "def strategy(data):\n    return 'BUY'",
        "parameters": {}
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
