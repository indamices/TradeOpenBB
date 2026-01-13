from typing import Optional, Dict
from sqlalchemy.orm import Session
from .models import AIModelConfig, AIProvider
from .ai_providers.gemini_provider import GeminiProvider
from .ai_providers.openai_provider import OpenAIProvider
from .ai_providers.claude_provider import ClaudeProvider
from cryptography.fernet import Fernet
import os
import base64
import logging

logger = logging.getLogger(__name__)

# Encryption key for API keys (in production, use environment variable)
def get_encryption_key() -> bytes:
    """Get encryption key from environment or generate one"""
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        return base64.urlsafe_b64decode(key)
    else:
        # Generate a key (in production, this should be set in environment)
        logger.warning("Using default encryption key. Set ENCRYPTION_KEY in production!")
        return Fernet.generate_key()

# Initialize Fernet cipher
_cipher = Fernet(get_encryption_key())

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    try:
        encrypted = _cipher.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        return api_key  # Fallback to plain text (not recommended)

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key from storage"""
    try:
        decoded = base64.urlsafe_b64decode(encrypted_key.encode())
        decrypted = _cipher.decrypt(decoded)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        return encrypted_key  # Return as-is if decryption fails

def get_default_model(db: Session) -> Optional[AIModelConfig]:
    """Get default AI model configuration"""
    model = db.query(AIModelConfig).filter(
        AIModelConfig.is_default == True,
        AIModelConfig.is_active == True
    ).first()
    return model

def get_model_by_id(model_id: int, db: Session) -> Optional[AIModelConfig]:
    """Get AI model configuration by ID"""
    return db.query(AIModelConfig).filter(AIModelConfig.id == model_id).first()

def create_provider(model_config: AIModelConfig):
    """Create AI provider instance from configuration"""
    api_key = decrypt_api_key(model_config.api_key)
    
    if model_config.provider == AIProvider.GEMINI:
        return GeminiProvider(
            api_key=api_key,
            model_name=model_config.model_name,
            base_url=model_config.base_url
        )
    elif model_config.provider == AIProvider.OPENAI:
        return OpenAIProvider(
            api_key=api_key,
            model_name=model_config.model_name,
            base_url=model_config.base_url
        )
    elif model_config.provider == AIProvider.CLAUDE:
        return ClaudeProvider(
            api_key=api_key,
            model_name=model_config.model_name,
            base_url=model_config.base_url
        )
    elif model_config.provider == AIProvider.CUSTOM:
        # Custom provider (e.g., local model with OpenAI-compatible API)
        return OpenAIProvider(
            api_key=api_key,
            model_name=model_config.model_name,
            base_url=model_config.base_url or "http://localhost:8000/v1"
        )
    else:
        raise ValueError(f"Unsupported provider: {model_config.provider}")

async def generate_strategy(prompt: str, model_id: Optional[int], db: Session) -> Dict[str, str]:
    """
    Generate strategy code using AI
    
    Args:
        prompt: User's natural language description
        model_id: Optional model ID (if None, use default)
        db: Database session
    
    Returns:
        Dictionary with 'code' and 'explanation'
    """
    try:
        # Get model configuration
        if model_id:
            model_config = get_model_by_id(model_id, db)
        else:
            model_config = get_default_model(db)
        
        if not model_config:
            raise ValueError("No AI model configured. Please set up an AI model in settings.")
        
        if not model_config.is_active:
            raise ValueError(f"AI model '{model_config.name}' is not active.")
        
        # Create provider and generate strategy
        provider = create_provider(model_config)
        result = await provider.generate_strategy(prompt)
        
        return result
        
    except Exception as e:
        logger.error(f"Strategy generation failed: {str(e)}")
        raise

async def test_model_connection(model_id: int, db: Session) -> bool:
    """
    Test connection to AI model
    
    Args:
        model_id: Model ID to test
        db: Database session
    
    Returns:
        True if connection successful
    """
    try:
        model_config = get_model_by_id(model_id, db)
        if not model_config:
            raise ValueError("Model not found")
        
        provider = create_provider(model_config)
        result = await provider.test_connection()
        return result
        
    except Exception as e:
        logger.error(f"Model connection test failed: {str(e)}")
        raise
