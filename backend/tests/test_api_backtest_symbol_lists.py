"""
Tests for Backtest Symbol Lists API endpoints
"""
import pytest
from fastapi import status

class TestBacktestSymbolLists:
    """Test backtest symbol lists endpoints"""
    
    def test_get_symbol_lists_empty(self, client):
        """Test getting empty symbol lists"""
        response = client.get("/api/backtest/symbol-lists")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_create_symbol_list(self, client):
        """Test creating a symbol list"""
        response = client.post("/api/backtest/symbol-lists", json={
            "name": "Test List",
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test List"
        assert "id" in data
    
    def test_get_symbol_list(self, client):
        """Test getting a specific symbol list"""
        # Create a list
        create_response = client.post("/api/backtest/symbol-lists", json={
            "name": "Test List",
            "symbols": ["AAPL"]
        })
        list_id = create_response.json()["id"]
        
        # Get it
        response = client.get(f"/api/backtest/symbol-lists/{list_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == list_id
    
    def test_get_nonexistent_symbol_list(self, client):
        """Test getting non-existent symbol list"""
        response = client.get("/api/backtest/symbol-lists/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_symbol_list(self, client):
        """Test updating a symbol list"""
        # Create a list
        create_response = client.post("/api/backtest/symbol-lists", json={
            "name": "Test List",
            "symbols": ["AAPL"]
        })
        list_id = create_response.json()["id"]
        
        # Update it
        response = client.put(f"/api/backtest/symbol-lists/{list_id}", json={
            "name": "Updated List",
            "symbols": ["AAPL", "GOOGL"]
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated List"
    
    def test_delete_symbol_list(self, client):
        """Test deleting a symbol list"""
        # Create a list
        create_response = client.post("/api/backtest/symbol-lists", json={
            "name": "Test List",
            "symbols": ["AAPL"]
        })
        list_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/backtest/symbol-lists/{list_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        get_response = client.get(f"/api/backtest/symbol-lists/{list_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
