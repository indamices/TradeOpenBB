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
    
    def test_extract_strategies_success(self, client, db_session):
        """Test successfully extracting strategies from a message with valid strategy code"""
        # Create a conversation
        conversation = Conversation(conversation_id="test-conv-2")
        db_session.add(conversation)
        db_session.commit()
        
        # Create a message with strategy code
        strategy_code = """
def strategy_logic(data):
    \"\"\"
    Simple moving average crossover strategy
    \"\"\"
    import pandas as pd
    
    # Calculate SMA
    data['sma_short'] = data['close'].rolling(window=5).mean()
    data['sma_long'] = data['close'].rolling(window=20).mean()
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['sma_short'] > data['sma_long'], 'signal'] = 1
    data.loc[data['sma_short'] < data['sma_long'], 'signal'] = -1
    
    return data
"""
        
        message = ConversationMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content="Here's a simple moving average crossover strategy:",
            code_snippets={"python": strategy_code}
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Extract strategies
        response = client.post(
            f"/api/ai/conversations/{conversation.conversation_id}/extract-strategies?message_id={message.id}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify extracted strategy
        strategy = data[0]
        assert "id" in strategy
        assert "name" in strategy
        assert "logic_code" in strategy
        assert "conversation_id" in strategy
        assert strategy["conversation_id"] == conversation.conversation_id
        assert strategy["message_id"] == message.id
        assert "def strategy_logic" in strategy["logic_code"]
        
        # Verify strategy was saved to database
        db_strategy = db_session.query(ChatStrategy).filter(
            ChatStrategy.id == strategy["id"]
        ).first()
        assert db_strategy is not None
        assert db_strategy.logic_code == strategy["logic_code"]
    
    def test_extract_strategies_no_code(self, client, db_session):
        """Test extracting strategies from a message without strategy code"""
        # Create a conversation
        conversation = Conversation(conversation_id="test-conv-3")
        db_session.add(conversation)
        db_session.commit()
        
        # Create a message without strategy code
        message = ConversationMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content="This is a regular message without any code.",
            code_snippets=None
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Try to extract strategies
        response = client.post(
            f"/api/ai/conversations/{conversation.conversation_id}/extract-strategies?message_id={message.id}"
        )
        
        # Should return 400 (no strategy code found)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No strategy code found" in response.json()["detail"]
    
    def test_extract_strategies_invalid_code(self, client, db_session):
        """Test extracting strategies from a message with invalid code (no strategy_logic)"""
        # Create a conversation
        conversation = Conversation(conversation_id="test-conv-4")
        db_session.add(conversation)
        db_session.commit()
        
        # Create a message with invalid code (no strategy_logic function)
        invalid_code = """
def some_function():
    return "hello"
"""
        
        message = ConversationMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content="Here's some code:",
            code_snippets={"python": invalid_code}
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Try to extract strategies
        response = client.post(
            f"/api/ai/conversations/{conversation.conversation_id}/extract-strategies?message_id={message.id}"
        )
        
        # Should return 400 (no strategy code found)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No strategy code found" in response.json()["detail"]
    
    def test_extract_strategies_multiple_strategies(self, client, db_session):
        """Test extracting multiple strategies from a message"""
        # Create a conversation
        conversation = Conversation(conversation_id="test-conv-5")
        db_session.add(conversation)
        db_session.commit()
        
        # Create a message with multiple strategy code blocks
        strategy_code_1 = """
def strategy_logic(data):
    \"\"\"Strategy 1: SMA Crossover\"\"\"
    data['sma_short'] = data['close'].rolling(window=5).mean()
    data['sma_long'] = data['close'].rolling(window=20).mean()
    data['signal'] = 0
    data.loc[data['sma_short'] > data['sma_long'], 'signal'] = 1
    return data
"""
        
        strategy_code_2 = """
def strategy_logic(data):
    \"\"\"Strategy 2: RSI Strategy\"\"\"
    import pandas as pd
    data['rsi'] = calculate_rsi(data['close'], 14)
    data['signal'] = 0
    data.loc[data['rsi'] < 30, 'signal'] = 1
    data.loc[data['rsi'] > 70, 'signal'] = -1
    return data
"""
        
        message_content = f"""
Here are two strategies:

Strategy 1:
```python
{strategy_code_1}
```

Strategy 2:
```python
{strategy_code_2}
```
"""
        
        message = ConversationMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content=message_content,
            code_snippets={"python": strategy_code_1}  # Only first one in code_snippets
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Extract strategies
        response = client.post(
            f"/api/ai/conversations/{conversation.conversation_id}/extract-strategies?message_id={message.id}"
        )
        
        # Should extract at least one strategy (from code_snippets)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least one strategy should be extracted
    
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
