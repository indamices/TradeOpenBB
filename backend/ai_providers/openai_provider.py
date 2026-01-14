from typing import Dict

try:
    from .base_provider import BaseAIProvider
except ImportError:
    from base_provider import BaseAIProvider
import json
import logging
import re

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
        """Generate strategy using OpenAI or OpenAI-compatible API"""
        try:
            system_instruction = self.get_system_instruction()
            
            # Build prompt that requests JSON format (for compatibility with GLM and other OpenAI-compatible APIs)
            user_prompt = f"""{prompt}

Please respond with a JSON object containing two fields:
- "code": The executable Python code for the strategy (as a string)
- "explanation": A brief explanation of the strategy logic (as a string)

Example format:
{{
  "code": "import pandas as pd\\nimport numpy as np\\n\\ndef strategy_logic(df: pd.DataFrame) -> pd.Series:\\n    # Your strategy code here\\n    return signals",
  "explanation": "This strategy uses..."
}}"""
            
            # Try with response_format first (for OpenAI), fallback to plain request (for compatible APIs)
            try:
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
            except Exception as format_error:
                # If response_format is not supported (e.g., GLM), try without it
                logger.debug(f"Response format not supported, trying without it: {str(format_error)}")
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7
                )
            
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("No content generated")
            
            # Try to extract JSON from the response (handle cases where response is wrapped in markdown)
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as json_error:
                # If JSON parsing fails, try to extract JSON object from the text
                json_match = re.search(r'\{[^{}]*"code"[^{}]*"explanation"[^{}]*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError(f"Failed to parse JSON response: {str(json_error)}. Response: {result_text[:200]}")
            
            return {
                "code": result.get("code", ""),
                "explanation": result.get("explanation", "")
            }
            
        except Exception as e:
            logger.error(f"OpenAI strategy generation failed: {str(e)}", exc_info=True)
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
                "explanation": f"Error connecting to AI model. Returned default SMA Crossover strategy. Error: {str(e)}"
            }
    
    async def test_connection(self) -> bool:
        """Test OpenAI or OpenAI-compatible API connection"""
        try:
            # Simple test request - try with max_tokens first, fallback without it
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
            except Exception:
                # Some APIs don't support max_tokens parameter
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Hi"}]
                )
            
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}", exc_info=True)
            raise  # Re-raise to provide better error message
