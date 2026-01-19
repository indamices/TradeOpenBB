"""
Integration tests for complete workflows
"""
import pytest
from fastapi import status

def test_portfolio_workflow(client, sample_portfolio_data):
    """Test complete portfolio workflow"""
    # Create portfolio
    create_response = client.post("/api/portfolio", json=sample_portfolio_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    assert "id" in create_response.json(), f"Response missing 'id': {create_response.text}"
    portfolio_id = create_response.json()["id"]
    
    # Create position
    position_data = {
        "portfolio_id": portfolio_id,
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": 150.0,
        "current_price": 155.0
    }
    position_response = client.post("/api/positions", json=position_data)
    assert position_response.status_code == status.HTTP_201_CREATED
    
    # Create order
    order_data = {
        "portfolio_id": portfolio_id,
        "symbol": "AAPL",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 5,
        "price": 150.0
    }
    order_response = client.post("/api/orders", json=order_data)
    assert order_response.status_code == status.HTTP_201_CREATED
    
    # Get portfolio and verify
    portfolio_response = client.get(f"/api/portfolio?portfolio_id={portfolio_id}")
    assert portfolio_response.status_code == status.HTTP_200_OK
    
    # Get positions
    positions_response = client.get(f"/api/positions?portfolio_id={portfolio_id}")
    assert positions_response.status_code == status.HTTP_200_OK
    # 分页端点返回 (列表, 总数)
    positions, total = positions_response.json()
    assert len(positions) > 0
    
    # Get orders
    orders_response = client.get(f"/api/orders?portfolio_id={portfolio_id}")
    assert orders_response.status_code == status.HTTP_200_OK
    assert len(orders_response.json()) > 0

def test_strategy_workflow(client, sample_strategy_data):
    """Test strategy creation and retrieval"""
    # Create strategy
    create_response = client.post("/api/strategies", json=sample_strategy_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    assert "id" in create_response.json(), f"Response missing 'id': {create_response.text}"
    strategy_id = create_response.json()["id"]

    # Get all strategies
    strategies_response = client.get("/api/strategies")
    assert strategies_response.status_code == status.HTTP_200_OK
    # 分页端点返回 (列表, 总数)
    strategies, total = strategies_response.json()
    assert any(s["id"] == strategy_id for s in strategies)

def test_ai_model_workflow(client, sample_ai_model_data):
    """Test AI model configuration workflow"""
    # Create model
    create_response = client.post("/api/ai-models", json=sample_ai_model_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    assert "id" in create_response.json(), f"Response missing 'id': {create_response.text}"
    model_id = create_response.json()["id"]
    
    # Set as default
    default_response = client.put(f"/api/ai-models/{model_id}/set-default")
    assert default_response.status_code == status.HTTP_200_OK
    assert default_response.json()["is_default"] == True
    
    # Update model
    update_data = {"name": "Updated Name"}
    update_response = client.put(f"/api/ai-models/{model_id}", json=update_data)
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["name"] == "Updated Name"
    
    # Delete model
    delete_response = client.delete(f"/api/ai-models/{model_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
