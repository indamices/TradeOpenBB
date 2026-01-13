"""
Tests for Positions API endpoints
"""
import pytest
from fastapi import status

def test_get_positions_empty(client):
    """Test getting positions when none exist"""
    response = client.get("/api/positions")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_position(client, sample_position_data):
    """Test creating a position"""
    response = client.post("/api/positions", json=sample_position_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["symbol"] == sample_position_data["symbol"]
    assert data["quantity"] == sample_position_data["quantity"]
    assert "id" in data

def test_get_positions(client, sample_position_data):
    """Test getting all positions"""
    # Create a position
    client.post("/api/positions", json=sample_position_data)
    
    # Get all positions
    response = client.get("/api/positions")
    assert response.status_code == status.HTTP_200_OK
    positions = response.json()
    assert len(positions) == 1
    assert positions[0]["symbol"] == sample_position_data["symbol"]
