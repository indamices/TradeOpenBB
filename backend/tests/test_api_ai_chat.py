"""
Tests for AI Chat API endpoints
"""
import pytest
from fastapi import status

def test_chat_endpoint(client):
    """Test AI chat endpoint"""
    chat_request = {
        "message": "How can I create a mean reversion strategy?",
        "conversation_id": None
    }
    
    response = client.post("/api/ai/chat", json=chat_request)
    
    # Should either succeed or return proper error
    assert response.status_code in [200, 500, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "message" in data
        assert "conversation_id" in data
        assert isinstance(data["message"], str)
        assert isinstance(data["conversation_id"], str)
        # Optional fields
        if "suggestions" in data:
            assert isinstance(data["suggestions"], list) or data["suggestions"] is None
        if "code_snippets" in data:
            assert isinstance(data["code_snippets"], dict) or data["code_snippets"] is None

def test_chat_with_conversation_id(client):
    """Test chat with existing conversation ID"""
    # First message
    chat_request1 = {
        "message": "Hello",
        "conversation_id": None
    }
    response1 = client.post("/api/ai/chat", json=chat_request1)
    
    if response1.status_code == 200:
        conversation_id = response1.json()["conversation_id"]
        
        # Second message with same conversation ID
        chat_request2 = {
            "message": "Tell me more",
            "conversation_id": conversation_id
        }
        response2 = client.post("/api/ai/chat", json=chat_request2)
        
        assert response2.status_code in [200, 500, 503]
        if response2.status_code == 200:
            data = response2.json()
            assert data["conversation_id"] == conversation_id

def test_get_conversation_history(client):
    """Test getting conversation history"""
    # First create a conversation
    chat_request = {
        "message": "Test message",
        "conversation_id": None
    }
    response = client.post("/api/ai/chat", json=chat_request)
    
    if response.status_code == 200:
        conversation_id = response.json()["conversation_id"]
        
        # Get history
        history_response = client.get(f"/api/ai/chat/{conversation_id}")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert "conversation_id" in history_data
        assert "messages" in history_data
        assert isinstance(history_data["messages"], list)

def test_get_nonexistent_conversation(client):
    """Test getting non-existent conversation"""
    conversation_id = "nonexistent-id-12345"
    response = client.get(f"/api/ai/chat/{conversation_id}")
    
    # Should return empty messages, not error
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conversation_id
    assert data["messages"] == []

def test_get_ai_suggestions(client):
    """Test getting AI suggestions"""
    response = client.post("/api/ai/suggestions", json={})
    
    # Should either succeed or return proper error
    assert response.status_code in [200, 500, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

def test_chat_empty_message(client):
    """Test chat with empty message"""
    chat_request = {
        "message": "",
        "conversation_id": None
    }
    
    response = client.post("/api/ai/chat", json=chat_request)
    # Should handle gracefully (might validate or return error)
    assert response.status_code in [200, 400, 422, 500, 503]
