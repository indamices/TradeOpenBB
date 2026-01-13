"""
Tests for error handling and edge cases
"""
import pytest
from fastapi import status

def test_invalid_json(client):
    """Test handling of invalid JSON"""
    response = client.post(
        "/api/portfolio",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_missing_required_fields(client):
    """Test handling of missing required fields"""
    incomplete_data = {"name": "Test"}  # Missing initial_cash
    response = client.post("/api/portfolio", json=incomplete_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_invalid_field_types(client):
    """Test handling of invalid field types"""
    invalid_data = {
        "name": "Test",
        "initial_cash": "not a number"  # Should be float
    }
    response = client.post("/api/portfolio", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_negative_cash(client):
    """Test handling of negative cash values"""
    invalid_data = {
        "name": "Test",
        "initial_cash": -1000.0  # Should be > 0
    }
    response = client.post("/api/portfolio", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_very_large_numbers(client):
    """Test handling of very large numbers"""
    large_data = {
        "name": "Test",
        "initial_cash": 1e20  # Very large number
    }
    response = client.post("/api/portfolio", json=large_data)
    # Should either succeed or return proper error
    assert response.status_code in [201, 422, 400]

def test_empty_strings(client):
    """Test handling of empty strings"""
    empty_data = {
        "name": "",
        "initial_cash": 1000.0
    }
    response = client.post("/api/portfolio", json=empty_data)
    # Should either accept or reject with proper error
    assert response.status_code in [201, 422, 400]

def test_sql_injection_attempt(client):
    """Test handling of potential SQL injection"""
    malicious_data = {
        "name": "'; DROP TABLE portfolios; --",
        "initial_cash": 1000.0
    }
    response = client.post("/api/portfolio", json=malicious_data)
    # Should handle safely (either accept as string or reject)
    assert response.status_code in [201, 422, 400]
    # If accepted, should be stored as string, not executed
    if response.status_code == 201:
        portfolio_id = response.json()["id"]
        get_response = client.get(f"/api/portfolio?portfolio_id={portfolio_id}")
        assert get_response.status_code == status.HTTP_200_OK

def test_unicode_characters(client):
    """Test handling of unicode characters"""
    unicode_data = {
        "name": "测试组合 🚀",
        "initial_cash": 1000.0
    }
    response = client.post("/api/portfolio", json=unicode_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "测试组合 🚀"
