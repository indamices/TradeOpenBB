from typing import Dict
from .base_provider import BaseAIProvider
import json
import logging

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. Install with: pip install openai")

class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", base_url: str = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is not installed")
        super().__init__(api_key, model_name, base_url)
        
        # Initialize OpenAI client
        if base_url:
            # For custom endpoints (e.g., local models)
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.client = openai.OpenAI(api_key=api_key)
    
    async def generate_strategy(self, prompt: str) -> Dict[str, str]:
        """Generate strategy using OpenAI"""
        try:
            system_instruction = self.get_system_instruction()
            
            # Define response schema for structured output
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "strategy_response",
                    "strict": True,
                    "schema": {
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
            }
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                response_format=response_format,
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("No content generated")
            
            result = json.loads(result_text)
            return {
                "code": result.get("code", ""),
                "explanation": result.get("explanation", "")
            }
            
        except Exception as e:
            logger.error(f"OpenAI strategy generation failed: {str(e)}")
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
                "explanation": f"Error connecting to OpenAI. Returned default SMA Crossover strategy. Error: {str(e)}"
            }
    
    async def test_connection(self) -> bool:
        """Test OpenAI connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False
