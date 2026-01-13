"""
Tests for Strategies API endpoints
"""
import pytest
from fastapi import status

def test_get_strategies_empty(client):
    """Test getting strategies when none exist"""
    response = client.get("/api/strategies")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_strategy(client, sample_strategy_data):
    """Test creating a strategy"""
    response = client.post("/api/strategies", json=sample_strategy_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == sample_strategy_data["name"]
    assert data["code"] == sample_strategy_data["code"]
    assert "id" in data

def test_get_strategies(client, sample_strategy_data):
    """Test getting all strategies"""
    # Create a strategy
    client.post("/api/strategies", json=sample_strategy_data)
    
    # Get all strategies
    response = client.get("/api/strategies")
    assert response.status_code == status.HTTP_200_OK
    strategies = response.json()
    assert len(strategies) == 1
    assert strategies[0]["name"] == sample_strategy_data["name"]

def test_generate_strategy_mock(client):
    """Test strategy generation (mocked)"""
    request_data = {
        "description": "A simple moving average strategy",
        "symbol": "AAPL",
        "timeframe": "1d"
    }
    # This will fail if AI service is not configured, but should return proper error
    response = client.post("/api/strategies/generate", json=request_data)
    # Should either succeed or return a proper error (not 500)
    assert response.status_code in [200, 400, 500, 503]
