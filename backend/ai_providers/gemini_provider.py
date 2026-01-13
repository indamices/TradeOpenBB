from typing import Dict
from .base_provider import BaseAIProvider
import os
import json
import logging

logger = logging.getLogger(__name__)

try:
    from google.genai import Client, types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google GenAI library not available. Install with: pip install google-genai")

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp", base_url: str = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenAI library is not installed")
        super().__init__(api_key, model_name, base_url)
        self.client = Client(api_key=api_key)
    
    async def generate_strategy(self, prompt: str) -> Dict[str, str]:
        """Generate strategy using Gemini"""
        try:
            system_instruction = self.get_system_instruction()
            
            # Use the generate_content method
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The executable Python code for the strategy."
                            },
                            "explanation": {
                                "type": "string",
                                "description": "A brief explanation of the strategy logic."
                            }
                        },
                        "required": ["code", "explanation"]
                    }
                }
            )
            
            result_text = response.text
            if not result_text:
                raise ValueError("No content generated")
            
            result = json.loads(result_text)
            return {
                "code": result.get("code", ""),
                "explanation": result.get("explanation", "")
            }
            
        except Exception as e:
            logger.error(f"Gemini strategy generation failed: {str(e)}")
            # Fallback to default strategy
            return {
                "code": """import pandas as pd
import numpy as np

def strategy_logic(df: pd.DataFrame) -> pd.Series:
    # Default SMA Crossover strategy
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    signals = pd.Series(0, index=df.index)
    signals[df['SMA_20'] > df['SMA_50']] = 1
    signals[df['SMA_20'] < df['SMA_50']] = -1
    
    return signals""",
                "explanation": f"Error connecting to Gemini. Returned default SMA Crossover strategy. Error: {str(e)}"
            }
    
    async def test_connection(self) -> bool:
        """Test Gemini connection"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Test",
                config={"max_output_tokens": 10}
            )
            return response.text is not None
        except Exception as e:
            logger.error(f"Gemini connection test failed: {str(e)}")
            return False
