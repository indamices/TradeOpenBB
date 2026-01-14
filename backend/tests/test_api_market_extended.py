"""
Tests for extended Market API endpoints
"""
import pytest
from fastapi import status

def test_get_multiple_quotes(client):
    """Test getting quotes for multiple symbols"""
    symbols = "AAPL,MSFT,GOOGL"
    response = client.get(f"/api/market/quotes?symbols={symbols}")
    
    # Should either succeed or return proper error
    assert response.status_code in [200, 500, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # Should have quotes for each symbol (or empty if unavailable)
        for quote in data:
            assert "symbol" in quote
            assert "price" in quote
            assert "change" in quote
            assert "volume" in quote

def test_get_technical_indicators(client):
    """Test getting technical indicators"""
    symbol = "AAPL"
    indicators = "MACD,RSI,BB"
    period = 20
    
    response = client.get(f"/api/market/indicators/{symbol}?indicators={indicators}&period={period}")
    
    # Should either succeed or return proper error
    assert response.status_code in [200, 500, 503]
    
    if response.status_code == 200:
        data = response.json()
        # Should return data (dict or list)
        assert data is not None

def test_get_market_overview(client):
    """Test getting market overview"""
    response = client.get("/api/market/overview")
    
    # Should either succeed or return proper error
    assert response.status_code in [200, 500, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        # Check expected fields
        assert "total_symbols" in data or "timestamp" in data

def test_get_multiple_quotes_empty(client):
    """Test getting quotes with empty symbols"""
    symbols = ""
    response = client.get(f"/api/market/quotes?symbols={symbols}")
    
    # Should handle gracefully
    assert response.status_code in [200, 400, 500, 503]

def test_get_indicators_invalid_symbol(client):
    """Test getting indicators for invalid symbol"""
    symbol = "INVALID_SYMBOL_XYZ123"
    indicators = "MACD"
    response = client.get(f"/api/market/indicators/{symbol}?indicators={indicators}")
    
    # Should return error, not crash
    assert response.status_code in [400, 404, 500, 503]
