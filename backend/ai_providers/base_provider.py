from abc import ABC, abstractmethod
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Unified system instruction template for strategy generation
SYSTEM_INSTRUCTION_TEMPLATE = """
You are an expert Quantitative Analyst and Python developer specialized in algorithmic trading.
Your task is to generate Python strategy code compatible with the OpenBB backtesting engine (Pandas-based).

The strategy function signature should be:
def strategy_logic(df: pd.DataFrame) -> pd.Series:

The input 'df' is a pandas DataFrame containing columns: ['Open', 'High', 'Low', 'Close', 'Volume'].
The DataFrame is indexed by date (DatetimeIndex).

The output should be a pandas Series of signals:
- 1 (Buy signal)
- -1 (Sell signal)  
- 0 (Hold/No signal)

Requirements:
1. Use vectorized operations (avoid loops for performance)
2. Import necessary libraries: pandas as pd, numpy as np
3. You can use technical indicators from pandas/numpy (e.g., rolling means, RSI calculations)
4. The strategy should be compatible with OpenBB data format
5. Ensure the function returns a Series with the same index as the input DataFrame

Example structure:
import pandas as pd
import numpy as np

def strategy_logic(df: pd.DataFrame) -> pd.Series:
    # Calculate indicators
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # Generate signals
    signals = pd.Series(0, index=df.index)
    signals[df['SMA_20'] > df['SMA_50']] = 1  # Buy when short MA crosses above long MA
    signals[df['SMA_20'] < df['SMA_50']] = -1  # Sell when short MA crosses below long MA
    
    return signals
"""

class BaseAIProvider(ABC):
    """Base class for AI providers"""
    
    def __init__(self, api_key: str, model_name: str, base_url: str = None):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
    
    @abstractmethod
    async def generate_strategy(self, prompt: str) -> Dict[str, str]:
        """
        Generate strategy code from natural language prompt
        
        Args:
            prompt: User's natural language description of the strategy
        
        Returns:
            Dictionary with 'code' and 'explanation' keys
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to AI service
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    async def chat(self, message: str, conversation_history: list = None) -> str:
        """
        Chat with AI (for general conversation, not strategy generation)
        
        Args:
            message: User's message
            conversation_history: List of previous messages in format [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            AI's response as plain text
        """
        # Default implementation - can be overridden by providers
        # For now, use generate_strategy but extract just the explanation
        result = await self.generate_strategy(message)
        return result.get("explanation", result.get("code", ""))
    
    def get_system_instruction(self) -> str:
        """Get system instruction for strategy generation"""
        return SYSTEM_INSTRUCTION_TEMPLATE
    
    def get_chat_system_instruction(self) -> str:
        """Get system instruction for chat (more conversational)"""
        return """You are a helpful AI assistant specialized in algorithmic trading and quantitative finance. 
You help users understand trading strategies, explain market concepts, and provide guidance on strategy development.
Be conversational, clear, and helpful. When users ask about strategies, you can provide code examples when appropriate."""