"""
Tests for Chat Strategy API endpoints
"""
import pytest
from fastapi import status
from models import Conversation, ConversationMessage, ChatStrategy

class TestChatStrategies:
    """Test chat strategy endpoints"""
    
    def test_extract_strategies_no_message(self, client, db_session):
        """Test extracting strategies when message doesn't exist"""
        # Create a conversation
        conversation = Conversation(conversation_id="test-conv-1")
        db_session.add(conversation)
        db_session.commit()
        
        # The endpoint expects message_id as query parameter, not in body
        response = client.post(
            f"/api/ai/conversations/{conversation.conversation_id}/extract-strategies?message_id=99999"
        )
        # Should return 404 (message not found) or 422 (validation error)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_get_chat_strategies_empty(self, client, db_session):
        """Test getting chat strategies when none exist"""
        # Create a conversation
        conversation = Conversation(conversation_id="test-conv-1")
        db_session.add(conversation)
        db_session.commit()
        
        response = client.get(f"/api/ai/conversations/{conversation.conversation_id}/strategies")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_save_chat_strategy_not_found(self, client):
        """Test saving non-existent chat strategy"""
        response = client.post(
            "/api/ai/chat-strategies/99999/save",
            json={
                "name": "Test Strategy",
                "target_portfolio_id": 1
            }
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_chat_strategy_not_found(self, client):
        """Test deleting non-existent chat strategy"""
        response = client.delete("/api/ai/chat-strategies/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
