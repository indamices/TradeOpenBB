"""
Tests for Stock Pool API endpoints
"""
import pytest
from fastapi import status

class TestStockPools:
    """Test stock pool endpoints"""
    
    def test_get_stock_pools_empty(self, client):
        """Test getting empty stock pools list"""
        response = client.get("/api/stock-pools")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_create_stock_pool(self, client):
        """Test creating a stock pool"""
        response = client.post("/api/stock-pools", json={
            "name": "Test Pool",
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Pool"
        assert "id" in data
    
    def test_get_stock_pool(self, client):
        """Test getting a specific stock pool"""
        # First create a pool
        create_response = client.post("/api/stock-pools", json={
            "name": "Test Pool",
            "symbols": ["AAPL", "GOOGL"]
        })
        assert create_response.status_code == status.HTTP_201_CREATED
        pool_id = create_response.json()["id"]
        
        # Get the pool
        response = client.get(f"/api/stock-pools/{pool_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == pool_id
    
    def test_get_nonexistent_stock_pool(self, client):
        """Test getting non-existent stock pool"""
        response = client.get("/api/stock-pools/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_stock_pool(self, client):
        """Test updating a stock pool"""
        # Create a pool
        create_response = client.post("/api/stock-pools", json={
            "name": "Test Pool",
            "symbols": ["AAPL"]
        })
        pool_id = create_response.json()["id"]
        
        # Update it
        response = client.put(f"/api/stock-pools/{pool_id}", json={
            "name": "Updated Pool",
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Pool"
    
    def test_delete_stock_pool(self, client):
        """Test deleting a stock pool"""
        # Create a pool
        create_response = client.post("/api/stock-pools", json={
            "name": "Test Pool",
            "symbols": ["AAPL"]
        })
        pool_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/stock-pools/{pool_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        get_response = client.get(f"/api/stock-pools/{pool_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
