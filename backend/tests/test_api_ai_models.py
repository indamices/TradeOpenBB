"""
Tests for AI Models API endpoints
"""
import pytest
from fastapi import status

def test_get_ai_models_empty(client):
    """Test getting AI models when none exist"""
    response = client.get("/api/ai-models")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_ai_model(client, sample_ai_model_data):
    """Test creating an AI model config"""
    response = client.post("/api/ai-models", json=sample_ai_model_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == sample_ai_model_data["name"]
    assert data["provider"] == sample_ai_model_data["provider"]
    assert "id" in data
    # API key should be encrypted/hidden
    assert "api_key" not in data or data.get("api_key") != sample_ai_model_data["api_key"]

def test_get_ai_models(client, sample_ai_model_data):
    """Test getting all AI models"""
    # Create a model
    client.post("/api/ai-models", json=sample_ai_model_data)
    
    # Get all models
    response = client.get("/api/ai-models")
    assert response.status_code == status.HTTP_200_OK
    models = response.json()
    assert len(models) == 1
    assert models[0]["name"] == sample_ai_model_data["name"]

def test_update_ai_model(client, sample_ai_model_data):
    """Test updating an AI model"""
    # Create model
    create_response = client.post("/api/ai-models", json=sample_ai_model_data)
    model_id = create_response.json()["id"]
    
    # Update model
    update_data = {"name": "Updated Model"}
    response = client.put(f"/api/ai-models/{model_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Model"

def test_delete_ai_model(client, sample_ai_model_data):
    """Test deleting an AI model"""
    # Create model
    create_response = client.post("/api/ai-models", json=sample_ai_model_data)
    model_id = create_response.json()["id"]
    
    # Delete model
    response = client.delete(f"/api/ai-models/{model_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify deleted
    get_response = client.get("/api/ai-models")
    assert len(get_response.json()) == 0

def test_set_default_ai_model(client, sample_ai_model_data):
    """Test setting default AI model"""
    # Create model
    create_response = client.post("/api/ai-models", json=sample_ai_model_data)
    model_id = create_response.json()["id"]
    
    # Set as default
    response = client.put(f"/api/ai-models/{model_id}/set-default")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_default"] == True
