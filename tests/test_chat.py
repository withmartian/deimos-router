"""Tests for the chat completions API."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from openai.types.chat import ChatCompletion

from deimos_router.chat import ChatCompletions, Chat, chat
from deimos_router.router import Router, register_router, clear_routers


class TestChatCompletions:
    """Test cases for the ChatCompletions class."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_routers()
        # Reset the global chat instance's client
        chat.completions._client = None
    
    @patch('deimos_router.chat.config')
    @patch('deimos_router.chat.openai.OpenAI')
    def test_get_client_initialization(self, mock_openai, mock_config):
        """Test OpenAI client initialization with credentials."""
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://test-api.com'
        }
        
        completions = ChatCompletions()
        client = completions._get_client()
        
        mock_openai.assert_called_once_with(
            api_key='test-key',
            base_url='https://test-api.com'
        )
        
        # Second call should return the same client (cached)
        client2 = completions._get_client()
        assert client is client2
        assert mock_openai.call_count == 1
    
    @patch('deimos_router.chat.config')
    @patch('deimos_router.chat.openai.OpenAI')
    def test_direct_model_call(self, mock_openai, mock_config):
        """Test direct model call (not using router)."""
        # Setup mocks
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://test-api.com'
        }
        
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock(spec=ChatCompletion)
        mock_response.model = 'gpt-3.5-turbo'
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the call
        completions = ChatCompletions()
        messages = [{"role": "user", "content": "Hello"}]
        
        response = completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        # Verify the call was made correctly
        mock_client.chat.completions.create.assert_called_once_with(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        assert response is mock_response
        assert response.model == 'gpt-3.5-turbo'
        # Should not have routing metadata for direct calls
        assert not hasattr(response, '_deimos_metadata')
    
    @patch('deimos_router.chat.config')
    @patch('deimos_router.chat.openai.OpenAI')
    def test_router_model_call(self, mock_openai, mock_config):
        """Test router-based model call."""
        # Setup mocks
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://test-api.com'
        }
        
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock(spec=ChatCompletion)
        mock_response.model = 'gpt-4o-mini'  # This will be the selected model
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create and register a router
        router = Router("my-router", models=["gpt-3.5-turbo", "gpt-4o-mini"])
        register_router(router)
        
        # Mock the router's select_model to return a specific model
        with patch.object(router, 'select_model', return_value='gpt-4o-mini'):
            completions = ChatCompletions()
            messages = [{"role": "user", "content": "Hello"}]
            
            response = completions.create(
                messages=messages,
                model="deimos/my-router",
                temperature=0.7
            )
        
        # Verify the call was made with the selected model
        mock_client.chat.completions.create.assert_called_once_with(
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        assert response is mock_response
        assert response.model == 'gpt-4o-mini'
        
        # Should have routing metadata
        assert hasattr(response, '_deimos_metadata')
        metadata = response._deimos_metadata
        assert metadata['router_used'] == 'my-router'
        assert metadata['selected_model'] == 'gpt-4o-mini'
        assert metadata['available_models'] == ["gpt-3.5-turbo", "gpt-4o-mini"]
    
    def test_router_not_found_error(self):
        """Test error when router is not found."""
        completions = ChatCompletions()
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(ValueError, match="Router 'nonexistent' not found"):
            completions.create(
                messages=messages,
                model="deimos/nonexistent"
            )
    
    @patch('deimos_router.chat.config')
    def test_config_not_configured_error(self, mock_config):
        """Test error when configuration is not set up."""
        mock_config.get_credentials.side_effect = ValueError("API credentials not configured")
        
        completions = ChatCompletions()
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(ValueError, match="API credentials not configured"):
            completions.create(
                messages=messages,
                model="gpt-3.5-turbo"
            )


class TestChatNamespace:
    """Test cases for the Chat namespace."""
    
    def test_chat_namespace_structure(self):
        """Test that the chat namespace has the correct structure."""
        chat_instance = Chat()
        
        assert hasattr(chat_instance, 'completions')
        assert isinstance(chat_instance.completions, ChatCompletions)
    
    def test_global_chat_instance(self):
        """Test that the global chat instance is properly configured."""
        assert hasattr(chat, 'completions')
        assert isinstance(chat.completions, ChatCompletions)


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def setup_method(self):
        """Setup for each test."""
        clear_routers()
        chat.completions._client = None
    
    @patch('deimos_router.chat.config')
    @patch('deimos_router.chat.openai.OpenAI')
    def test_complete_router_workflow(self, mock_openai, mock_config):
        """Test the complete workflow from router creation to API call."""
        # Setup configuration
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://test-api.com'
        }
        
        # Setup OpenAI client mock
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock(spec=ChatCompletion)
        mock_response.model = 'gpt-3.5-turbo'
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create and register router
        router = Router("test-router", models=["gpt-3.5-turbo", "gpt-4o-mini"])
        register_router(router)
        
        # Make API call through router
        messages = [{"role": "user", "content": "Hello, world!"}]
        
        response = chat.completions.create(
            messages=messages,
            model="deimos/test-router",
            temperature=0.5,
            max_tokens=100
        )
        
        # Verify the call was made
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        
        assert call_args[1]['messages'] == messages
        assert call_args[1]['model'] in ["gpt-3.5-turbo", "gpt-4o-mini"]
        assert call_args[1]['temperature'] == 0.5
        assert call_args[1]['max_tokens'] == 100
        
        # Verify response has routing metadata
        assert hasattr(response, '_deimos_metadata')
        metadata = response._deimos_metadata
        assert metadata['router_used'] == 'test-router'
        assert metadata['selected_model'] in ["gpt-3.5-turbo", "gpt-4o-mini"]
    
    @patch('deimos_router.chat.config')
    @patch('deimos_router.chat.openai.OpenAI')
    def test_complete_direct_model_workflow(self, mock_openai, mock_config):
        """Test the complete workflow for direct model calls."""
        # Setup configuration
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://test-api.com'
        }
        
        # Setup OpenAI client mock
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock(spec=ChatCompletion)
        mock_response.model = 'gpt-4'
        mock_client.chat.completions.create.return_value = mock_response
        
        # Make direct API call
        messages = [{"role": "user", "content": "Hello, world!"}]
        
        response = chat.completions.create(
            messages=messages,
            model="gpt-4",
            temperature=0.3
        )
        
        # Verify the call was made correctly
        mock_client.chat.completions.create.assert_called_once_with(
            messages=messages,
            model="gpt-4",
            temperature=0.3
        )
        
        # Verify response does not have routing metadata
        assert not hasattr(response, '_deimos_metadata')
        assert response.model == 'gpt-4'
