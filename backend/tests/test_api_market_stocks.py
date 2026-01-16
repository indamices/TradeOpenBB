"""
Tests for Market Stocks API endpoints
"""
import pytest
from fastapi import status

class TestMarketStocks:
    """Test market stocks endpoints"""
    
    def test_search_stocks_empty(self, client):
        """Test searching stocks with empty query"""
        response = client.get("/api/market/stocks/search")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_search_stocks_with_query(self, client):
        """Test searching stocks with query"""
        response = client.get("/api/market/stocks/search?q=AAPL")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_search_stocks_with_limit(self, client):
        """Test searching stocks with limit"""
        response = client.get("/api/market/stocks/search?limit=10")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) <= 10
    
    def test_get_stock_info_not_found(self, client):
        """Test getting stock info that doesn't exist"""
        response = client.get("/api/market/stocks/INVALID123/info")
        assert response.status_code == status.HTTP_404_NOT_FOUND
