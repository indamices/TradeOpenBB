"""
Tests for Portfolio API endpoints
"""
import pytest
from fastapi import status

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
    assert response.json()["status"] == "running"

def test_create_portfolio(client, sample_portfolio_data):
    """Test creating a portfolio"""
    response = client.post("/api/portfolio", json=sample_portfolio_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == sample_portfolio_data["name"]
    assert data["initial_cash"] == sample_portfolio_data["initial_cash"]
    assert "id" in data

def test_get_portfolio(client, sample_portfolio_data):
    """Test getting a portfolio"""
    # Create portfolio first
    create_response = client.post("/api/portfolio", json=sample_portfolio_data)
    assert create_response.status_code in [200, 201], f"Expected 200/201, got {create_response.status_code}: {create_response.text}"
    assert "id" in create_response.json(), f"Response missing 'id': {create_response.text}"
    portfolio_id = create_response.json()["id"]
    
    # Get portfolio
    response = client.get(f"/api/portfolio?portfolio_id={portfolio_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == portfolio_id
    assert data["name"] == sample_portfolio_data["name"]

def test_get_nonexistent_portfolio(client):
    """Test getting a non-existent portfolio"""
    response = client.get("/api/portfolio?portfolio_id=99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_portfolio(client, sample_portfolio_data):
    """Test updating a portfolio"""
    # Create portfolio
    create_response = client.post("/api/portfolio", json=sample_portfolio_data)
    assert create_response.status_code in [200, 201], f"Expected 200/201, got {create_response.status_code}: {create_response.text}"
    assert "id" in create_response.json(), f"Response missing 'id': {create_response.text}"
    portfolio_id = create_response.json()["id"]
    
    # Update portfolio
    update_data = {"name": "Updated Portfolio", "current_cash": 95000.0}
    response = client.put(f"/api/portfolio/{portfolio_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Portfolio"
    assert data["current_cash"] == 95000.0

def test_update_nonexistent_portfolio(client):
    """Test updating a non-existent portfolio"""
    update_data = {"name": "Updated Portfolio"}
    response = client.put("/api/portfolio/99999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_portfolio_validation(client):
    """Test portfolio creation with invalid data"""
    invalid_data = {"name": ""}  # Missing required fields
    response = client.post("/api/portfolio", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
