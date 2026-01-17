from typing import Optional, Dict
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
import os
import base64
import logging

try:
    from .models import AIModelConfig, AIProvider
    from .ai_providers.gemini_provider import GeminiProvider
    from .ai_providers.openai_provider import OpenAIProvider
    from .ai_providers.claude_provider import ClaudeProvider
except ImportError:
    from models import AIModelConfig, AIProvider
    from ai_providers.gemini_provider import GeminiProvider
    from ai_providers.openai_provider import OpenAIProvider
    from ai_providers.claude_provider import ClaudeProvider

logger = logging.getLogger(__name__)

# Encryption key for API keys (in production, use environment variable)
def get_encryption_key() -> bytes:
    """Get encryption key from environment or generate one"""
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        try:
            # Try to decode if it's base64 encoded
            decoded = base64.urlsafe_b64decode(key)
            if len(decoded) == 32:
                return decoded
        except Exception:
            pass
        
        # If decoding fails or key is not base64, try to use it directly
        # If it's a string, encode it and pad/truncate to 32 bytes
        if isinstance(key, str):
            key_bytes = key.encode('utf-8')
            # Pad or truncate to 32 bytes
            if len(key_bytes) < 32:
                key_bytes = key_bytes.ljust(32, b'0')
            elif len(key_bytes) > 32:
                key_bytes = key_bytes[:32]
            return key_bytes
        elif len(key) == 32:
            return key
    
    # Generate a key if not provided
    logger.warning("Using default encryption key. Set ENCRYPTION_KEY in production!")
    return Fernet.generate_key()

# Initialize Fernet cipher (lazy initialization to handle errors)
_cipher = None

def get_cipher():
    """Get or create Fernet cipher instance"""
    global _cipher
    if _cipher is None:
        try:
            key = get_encryption_key()
            # Ensure key is 32 bytes (Fernet requirement)
            if len(key) != 32:
                # If key is base64 encoded (44 chars), decode it
                if len(key) == 44:
                    try:
                        key = base64.urlsafe_b64decode(key)
                    except Exception:
                        pass
                # If still not 32 bytes, pad or truncate
                if len(key) != 32:
                    if len(key) < 32:
                        key = key.ljust(32, b'0')
                    else:
                        key = key[:32]
            _cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize cipher: {str(e)}")
            # Generate a new key as fallback
            _cipher = Fernet(Fernet.generate_key())
    return _cipher

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    try:
        cipher = get_cipher()
        encrypted = cipher.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        return api_key  # Fallback to plain text (not recommended)

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key from storage"""
    try:
        cipher = get_cipher()
        decoded = base64.urlsafe_b64decode(encrypted_key.encode())
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        return encrypted_key  # Return as-is if decryption fails

def get_default_model(db: Session) -> Optional[AIModelConfig]:
    """Get default AI model configuration (prefers active model over default)"""
    # First try to get active model (this is the current model in use)
    model = db.query(AIModelConfig).filter(
        AIModelConfig.is_active == True
    ).first()
    
    # If no active model, fallback to default model (but only if it's also active)
    if not model:
        model = db.query(AIModelConfig).filter(
            AIModelConfig.is_default == True,
            AIModelConfig.is_active == True
        ).first()
    
    # If still no model, return None (no models configured)
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

async def chat_with_ai(message: str, model_id: Optional[int], db: Session, conversation_history: list = None) -> str:
    """
    Chat with AI (for general conversation)
    
    Args:
        message: User's message
        model_id: Optional model ID (if None, use default)
        db: Database session
        conversation_history: List of previous messages
    
    Returns:
        AI's response as plain text
    """
    try:
        # Get model configuration
        if model_id:
            model_config = get_model_by_id(model_id, db)
        else:
            model_config = get_default_model(db)
        
        if not model_config:
            return "I'm sorry, but no AI model is configured. Please set up an AI model in settings to use the chat feature."
        
        if not model_config.is_active:
            return f"I'm sorry, but the AI model '{model_config.name}' is not active. Please activate it in settings."
        
        # Create provider and chat
        provider = create_provider(model_config)
        response = await provider.chat(message, conversation_history)
        
        return response
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}", exc_info=True)
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or check your AI model configuration."

async def check_ai_model_connection(model_id: int, db: Session) -> bool:
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
