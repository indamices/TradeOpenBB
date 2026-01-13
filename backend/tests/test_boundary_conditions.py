"""
Boundary condition tests
"""
import pytest
from fastapi import status
from decimal import Decimal

def test_portfolio_zero_cash(client):
    """Test portfolio with zero initial cash"""
    data = {"name": "Zero Cash", "initial_cash": 0.0}
    response = client.post("/api/portfolio", json=data)
    # Should either accept or reject with proper validation
    assert response.status_code in [201, 422]

def test_portfolio_very_large_cash(client):
    """Test portfolio with very large cash amount"""
    data = {"name": "Large Cash", "initial_cash": 1e15}
    response = client.post("/api/portfolio", json=data)
    assert response.status_code in [201, 422, 400]

def test_order_zero_quantity(client, sample_order_data):
    """Test order with zero quantity"""
    order_data = sample_order_data.copy()
    order_data["quantity"] = 0
    response = client.post("/api/orders", json=order_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_order_negative_quantity(client, sample_order_data):
    """Test order with negative quantity"""
    order_data = sample_order_data.copy()
    order_data["quantity"] = -10
    response = client.post("/api/orders", json=order_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_order_very_large_quantity(client, sample_order_data):
    """Test order with very large quantity"""
    order_data = sample_order_data.copy()
    order_data["quantity"] = 999999999
    response = client.post("/api/orders", json=order_data)
    # Should either accept or reject
    assert response.status_code in [201, 422, 400]

def test_position_zero_price(client, sample_position_data):
    """Test position with zero price"""
    position_data = sample_position_data.copy()
    position_data["current_price"] = 0.0
    response = client.post("/api/positions", json=position_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_position_negative_price(client, sample_position_data):
    """Test position with negative price"""
    position_data = sample_position_data.copy()
    position_data["current_price"] = -10.0
    response = client.post("/api/positions", json=position_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_very_long_symbol_name(client, sample_order_data):
    """Test order with very long symbol name"""
    order_data = sample_order_data.copy()
    order_data["symbol"] = "A" * 100  # Very long symbol
    response = client.post("/api/orders", json=order_data)
    # Should either accept or reject with proper error
    assert response.status_code in [201, 422, 400]

def test_empty_symbol(client, sample_order_data):
    """Test order with empty symbol"""
    order_data = sample_order_data.copy()
    order_data["symbol"] = ""
    response = client.post("/api/orders", json=order_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_special_characters_in_name(client):
    """Test portfolio name with special characters"""
    data = {"name": "Test!@#$%^&*()", "initial_cash": 1000.0}
    response = client.post("/api/portfolio", json=data)
    # Should handle special characters
    assert response.status_code in [201, 422]

def test_unicode_in_name(client):
    """Test portfolio name with unicode characters"""
    data = {"name": "测试组合 🚀 中文", "initial_cash": 1000.0}
    response = client.post("/api/portfolio", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    if response.status_code == 201:
        assert response.json()["name"] == "测试组合 🚀 中文"

def test_very_long_portfolio_name(client):
    """Test portfolio with very long name"""
    data = {"name": "A" * 1000, "initial_cash": 1000.0}
    response = client.post("/api/portfolio", json=data)
    # Should either accept or reject
    assert response.status_code in [201, 422, 400]

def test_float_precision(client):
    """Test float precision handling"""
    data = {"name": "Precision Test", "initial_cash": 0.12345678901234567890}
    response = client.post("/api/portfolio", json=data)
    assert response.status_code in [201, 422]

def test_nonexistent_portfolio_id_large(client):
    """Test getting portfolio with very large ID"""
    response = client.get("/api/portfolio?portfolio_id=999999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_negative_portfolio_id(client):
    """Test getting portfolio with negative ID"""
    response = client.get("/api/portfolio?portfolio_id=-1")
    # Should return 404 or 422
    assert response.status_code in [404, 422]

def test_order_with_nonexistent_portfolio(client, sample_order_data):
    """Test order with non-existent portfolio"""
    order_data = sample_order_data.copy()
    order_data["portfolio_id"] = 99999
    response = client.post("/api/orders", json=order_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_position_with_nonexistent_portfolio(client, sample_position_data):
    """Test position with non-existent portfolio"""
    position_data = sample_position_data.copy()
    position_data["portfolio_id"] = 99999
    response = client.post("/api/positions", json=position_data)
    # Should either fail validation or return error
    assert response.status_code in [404, 422, 400]

def test_strategy_with_empty_code(client, sample_strategy_data):
    """Test strategy with empty code"""
    strategy_data = sample_strategy_data.copy()
    strategy_data["logic_code"] = ""
    response = client.post("/api/strategies", json=strategy_data)
    # Should either accept or reject
    assert response.status_code in [201, 422]

def test_strategy_with_very_long_code(client, sample_strategy_data):
    """Test strategy with very long code"""
    strategy_data = sample_strategy_data.copy()
    strategy_data["logic_code"] = "def strategy(data):\n" + "    pass\n" * 10000
    response = client.post("/api/strategies", json=strategy_data)
    # Should either accept or reject
    assert response.status_code in [201, 422, 400]
