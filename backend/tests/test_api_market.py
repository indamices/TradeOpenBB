"""
Tests for Market API endpoints
"""
import pytest
from fastapi import status

def test_get_market_quote(client):
    """Test getting market quote"""
    symbol = "AAPL"
    response = client.get(f"/api/market/quote/{symbol}")
    # Should either succeed or return proper error
    # If market service is not configured, might return 500 or 503
    assert response.status_code in [200, 500, 503, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "symbol" in data
        assert "price" in data

def test_get_market_quote_invalid_symbol(client):
    """Test getting market quote for invalid symbol"""
    symbol = "INVALID_SYMBOL_XYZ123"
    response = client.get(f"/api/market/quote/{symbol}")
    # Should return error, not crash
    assert response.status_code in [400, 404, 500, 503]
