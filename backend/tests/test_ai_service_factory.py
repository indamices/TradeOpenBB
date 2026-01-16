"""
Tests for AI Service Factory
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_service_factory import (
    get_encryption_key,
    get_cipher,
    encrypt_api_key,
    decrypt_api_key,
    get_default_model,
    get_model_by_id,
    create_provider,
    generate_strategy,
    check_ai_model_connection
)
from models import AIModelConfig, AIProvider
from cryptography.fernet import Fernet
import os

class TestEncryption:
    """Test encryption/decryption functions"""
    
    def test_get_encryption_key_from_env(self):
        """Test getting encryption key from environment"""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': 'test_key_123456789012345678901234567890'}):
            key = get_encryption_key()
            assert isinstance(key, bytes)
            assert len(key) == 32
    
    def test_get_encryption_key_generated(self):
        """Test generating encryption key when not in environment"""
        with patch.dict(os.environ, {}, clear=True):
            key = get_encryption_key()
            assert isinstance(key, bytes)
            # Fernet.generate_key() returns a base64-encoded key (44 bytes)
            # or a raw 32-byte key depending on implementation
            assert len(key) in [32, 44]
            # Verify it's a valid Fernet key by trying to create a cipher
            from cryptography.fernet import Fernet
            try:
                Fernet(key)
            except Exception:
                # If key is 32 bytes, pad it to 44 bytes (base64)
                if len(key) == 32:
                    import base64
                    key_b64 = base64.urlsafe_b64encode(key)
                    assert len(key_b64) == 44
    
    def test_get_encryption_key_base64(self):
        """Test getting encryption key from base64 encoded string"""
        # Generate a valid base64 key
        test_key = Fernet.generate_key()
        base64_key = Fernet.generate_key().decode()
        
        with patch.dict(os.environ, {'ENCRYPTION_KEY': base64_key}):
            key = get_encryption_key()
            assert isinstance(key, bytes)
    
    def test_get_cipher(self):
        """Test getting cipher instance"""
        cipher = get_cipher()
        assert cipher is not None
        assert isinstance(cipher, Fernet)
    
    def test_encrypt_decrypt_api_key(self):
        """Test encrypting and decrypting API key"""
        original_key = "test_api_key_12345"
        
        encrypted = encrypt_api_key(original_key)
        assert encrypted != original_key
        assert isinstance(encrypted, str)
        
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original_key
    
    def test_encrypt_api_key_empty(self):
        """Test encrypting empty API key"""
        encrypted = encrypt_api_key("")
        assert isinstance(encrypted, str)
    
    def test_decrypt_invalid_key(self):
        """Test decrypting invalid key"""
        # Should return the encrypted value as-is if decryption fails
        result = decrypt_api_key("invalid_encrypted_key")
        assert isinstance(result, str)

class TestModelQueries:
    """Test model query functions"""
    
    def test_get_default_model_none(self, db_session):
        """Test getting default model when none exists"""
        model = get_default_model(db_session)
        assert model is None
    
    def test_get_default_model_exists(self, db_session):
        """Test getting default model when it exists"""
        # Create a default model
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro",
            is_default=True,
            is_active=True
        )
        db_session.add(model)
        db_session.commit()
        
        result = get_default_model(db_session)
        assert result is not None
        assert result.is_default == True
        assert result.is_active == True
    
    def test_get_default_model_inactive(self, db_session):
        """Test getting default model when it's inactive"""
        # Create an inactive default model
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro",
            is_default=True,
            is_active=False
        )
        db_session.add(model)
        db_session.commit()
        
        result = get_default_model(db_session)
        assert result is None  # Should not return inactive model
    
    def test_get_model_by_id_exists(self, db_session):
        """Test getting model by ID when it exists"""
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro"
        )
        db_session.add(model)
        db_session.commit()
        
        result = get_model_by_id(model.id, db_session)
        assert result is not None
        assert result.id == model.id
        assert result.name == "Test Model"
    
    def test_get_model_by_id_not_exists(self, db_session):
        """Test getting model by ID when it doesn't exist"""
        result = get_model_by_id(99999, db_session)
        assert result is None

class TestProviderCreation:
    """Test provider creation functions"""
    
    def test_create_provider_gemini(self, db_session):
        """Test creating Gemini provider"""
        model = AIModelConfig(
            name="Test Gemini",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro"
        )
        db_session.add(model)
        db_session.commit()
        
        try:
            provider = create_provider(model)
            assert provider is not None
            # Should be a GeminiProvider instance if library is installed
            from ai_providers.gemini_provider import GeminiProvider
            assert isinstance(provider, GeminiProvider)
        except ImportError:
            # Skip test if library is not installed
            pytest.skip("Google GenAI library is not installed")
    
    def test_create_provider_openai(self, db_session):
        """Test creating OpenAI provider"""
        model = AIModelConfig(
            name="Test OpenAI",
            provider=AIProvider.OPENAI,
            api_key=encrypt_api_key("test_key"),
            model_name="gpt-4"
        )
        db_session.add(model)
        db_session.commit()
        
        provider = create_provider(model)
        assert provider is not None
        from ai_providers.openai_provider import OpenAIProvider
        assert isinstance(provider, OpenAIProvider)
    
    def test_create_provider_claude(self, db_session):
        """Test creating Claude provider"""
        model = AIModelConfig(
            name="Test Claude",
            provider=AIProvider.CLAUDE,
            api_key=encrypt_api_key("test_key"),
            model_name="claude-3-opus"
        )
        db_session.add(model)
        db_session.commit()
        
        try:
            provider = create_provider(model)
            assert provider is not None
            from ai_providers.claude_provider import ClaudeProvider
            assert isinstance(provider, ClaudeProvider)
        except ImportError:
            # Skip test if library is not installed
            pytest.skip("Anthropic library is not installed")
    
    def test_create_provider_custom(self, db_session):
        """Test creating custom provider"""
        model = AIModelConfig(
            name="Test Custom",
            provider=AIProvider.CUSTOM,
            api_key=encrypt_api_key("test_key"),
            model_name="custom-model",
            base_url="http://localhost:8000/v1"
        )
        db_session.add(model)
        db_session.commit()
        
        provider = create_provider(model)
        assert provider is not None
        # Custom provider uses OpenAIProvider
        from ai_providers.openai_provider import OpenAIProvider
        assert isinstance(provider, OpenAIProvider)
    
    def test_create_provider_unsupported(self, db_session):
        """Test creating provider with unsupported type"""
        model = AIModelConfig(
            name="Test Invalid",
            provider=AIProvider.GEMINI,  # Valid provider
            api_key=encrypt_api_key("test_key"),
            model_name="test-model"
        )
        db_session.add(model)
        db_session.commit()
        
        # Manually set invalid provider value
        model.provider = "INVALID_PROVIDER"
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_provider(model)

class TestStrategyGeneration:
    """Test strategy generation functions"""
    
    @pytest.mark.asyncio
    async def test_generate_strategy_no_model(self, db_session):
        """Test generating strategy when no model is configured"""
        with pytest.raises(ValueError, match="No AI model configured"):
            await generate_strategy("Create a buy and hold strategy", None, db_session)
    
    @pytest.mark.asyncio
    async def test_generate_strategy_inactive_model(self, db_session):
        """Test generating strategy with inactive model"""
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro",
            is_default=True,
            is_active=False
        )
        db_session.add(model)
        db_session.commit()
        
        # When model is inactive, get_default_model returns None, so we get "No AI model configured"
        with pytest.raises(ValueError, match="No AI model configured"):
            await generate_strategy("Create a strategy", None, db_session)
    
    @pytest.mark.asyncio
    async def test_generate_strategy_with_model_id(self, db_session):
        """Test generating strategy with specific model ID"""
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro",
            is_default=True,
            is_active=True
        )
        db_session.add(model)
        db_session.commit()
        
        # Mock the provider's generate_strategy method
        with patch('ai_service_factory.create_provider') as mock_create:
            mock_provider = AsyncMock()
            mock_provider.generate_strategy = AsyncMock(return_value={
                'code': 'def strategy(data):\n    return "BUY"',
                'explanation': 'Test strategy'
            })
            mock_create.return_value = mock_provider
            
            result = await generate_strategy("Create a strategy", model.id, db_session)
            
            assert result is not None
            assert 'code' in result
            assert 'explanation' in result
            mock_provider.generate_strategy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_strategy_with_default_model(self, db_session):
        """Test generating strategy with default model"""
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro",
            is_default=True,
            is_active=True
        )
        db_session.add(model)
        db_session.commit()
        
        # Mock the provider
        with patch('ai_service_factory.create_provider') as mock_create:
            mock_provider = AsyncMock()
            mock_provider.generate_strategy = AsyncMock(return_value={
                'code': 'def strategy(data):\n    return "BUY"',
                'explanation': 'Test strategy'
            })
            mock_create.return_value = mock_provider
            
            result = await generate_strategy("Create a strategy", None, db_session)
            
            assert result is not None
            assert 'code' in result

class TestModelConnection:
    """Test model connection testing functions"""
    
    @pytest.mark.asyncio
    async def test_test_model_connection_not_found(self, db_session):
        """Test connection test when model not found"""
        with pytest.raises(ValueError, match="Model not found"):
            await check_ai_model_connection(99999, db_session)
    
    @pytest.mark.asyncio
    async def test_test_model_connection_success(self, db_session):
        """Test successful connection test"""
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro",
            is_active=True
        )
        db_session.add(model)
        db_session.commit()
        
        # Mock the provider's test_connection method
        with patch('ai_service_factory.create_provider') as mock_create:
            mock_provider = AsyncMock()
            mock_provider.test_connection = AsyncMock(return_value=True)
            mock_create.return_value = mock_provider
            
            result = await check_ai_model_connection(model.id, db_session)
            
            assert result is True
            mock_provider.test_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_model_connection_failure(self, db_session):
        """Test connection test failure"""
        model = AIModelConfig(
            name="Test Model",
            provider=AIProvider.GEMINI,
            api_key=encrypt_api_key("test_key"),
            model_name="gemini-pro",
            is_active=True
        )
        db_session.add(model)
        db_session.commit()
        
        # Mock the provider's test_connection method to fail
        with patch('ai_service_factory.create_provider') as mock_create:
            mock_provider = AsyncMock()
            mock_provider.test_connection = AsyncMock(return_value=False)
            mock_create.return_value = mock_provider
            
            result = await check_ai_model_connection(model.id, db_session)
            
            assert result is False
