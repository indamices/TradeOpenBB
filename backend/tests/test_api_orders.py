"""
Tests for Orders API endpoints
"""
import pytest
from fastapi import status

def test_get_orders_empty(client):
    """Test getting orders when none exist"""
    response = client.get("/api/orders")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_order(client, sample_order_data):
    """Test creating an order"""
    response = client.post("/api/orders", json=sample_order_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["symbol"] == sample_order_data["symbol"]
    assert data["side"] == sample_order_data["side"]
    assert data["quantity"] == sample_order_data["quantity"]
    assert "id" in data
    assert "created_at" in data

def test_get_orders(client, sample_order_data):
    """Test getting all orders"""
    # Create an order
    client.post("/api/orders", json=sample_order_data)
    
    # Get all orders
    response = client.get("/api/orders")
    assert response.status_code == status.HTTP_200_OK
    orders = response.json()
    assert len(orders) == 1
    assert orders[0]["symbol"] == sample_order_data["symbol"]

def test_order_validation(client):
    """Test order creation with invalid data"""
    invalid_data = {"symbol": ""}  # Missing required fields
    response = client.post("/api/orders", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_order_side_enum(client):
    """Test order with valid side enum"""
    order_data = {
        "symbol": "AAPL",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 10,
        "price": 150.0
    }
    response = client.post("/api/orders", json=order_data)
    assert response.status_code == status.HTTP_201_CREATED

def test_order_invalid_side_enum(client):
    """Test order with invalid side enum"""
    order_data = {
        "symbol": "AAPL",
        "side": "INVALID",
        "type": "MARKET",
        "quantity": 10,
        "price": 150.0
    }
    response = client.post("/api/orders", json=order_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
