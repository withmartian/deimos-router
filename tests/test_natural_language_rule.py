"""Tests for NaturalLanguageRule."""

import pytest
from unittest.mock import Mock, patch
from deimos_router.rules import NaturalLanguageRule, Decision


class TestNaturalLanguageRule:
    """Test cases for NaturalLanguageRule."""
    
    def test_init(self):
        """Test rule initialization."""
        language_mappings = {
            'en': 'gpt-4o',
            'es': 'claude-3-sonnet',
            'fr': 'gpt-4o-mini'
        }
        
        rule = NaturalLanguageRule(
            name='natural_language_router',
            language_mappings=language_mappings,
            default='gpt-4o-mini'
        )
        
        assert rule.name == 'natural_language_router'
        assert rule.language_mappings == language_mappings
        assert rule.default == 'gpt-4o-mini'
        assert rule.llm_model == 'gpt-4o-mini'  # Default from config
    
    def test_init_with_custom_model(self):
        """Test rule initialization with custom LLM model."""
        language_mappings = {'en': 'gpt-4o', 'es': 'claude-3-sonnet'}
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings=language_mappings,
            llm_model='gpt-4o'
        )
        
        assert rule.llm_model == 'gpt-4o'
    
    def test_extract_text_content(self):
        """Test text content extraction from messages."""
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o'}
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Hello, how are you?'},
                {'role': 'assistant', 'content': 'I am doing well, thank you!'},
                {'role': 'user', 'content': 'What is the weather like?'}
            ]
        }
        
        text = rule._extract_text_content(request_data)
        expected = 'Hello, how are you?\nI am doing well, thank you!\nWhat is the weather like?'
        assert text == expected
    
    def test_extract_text_content_empty_messages(self):
        """Test text extraction with empty messages."""
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o'}
        )
        
        request_data = {'messages': []}
        text = rule._extract_text_content(request_data)
        assert text == ''
    
    def test_extract_text_content_no_messages(self):
        """Test text extraction with no messages key."""
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o'}
        )
        
        request_data = {}
        text = rule._extract_text_content(request_data)
        assert text == ''
    
    @patch('deimos_router.rules.natural_language_rule.config')
    @patch('deimos_router.rules.natural_language_rule.openai.OpenAI')
    def test_detect_language_llm_success(self, mock_openai, mock_config):
        """Test successful language detection via LLM."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        mock_config.get_default_model.return_value = 'gpt-4o-mini'
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = 'en'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'}
        )
        
        result = rule._detect_language_llm('Hello, how are you today?')
        assert result == 'en'
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o-mini'
        assert call_args[1]['max_tokens'] == 10
        assert call_args[1]['temperature'] == 0.1
    
    @patch('deimos_router.rules.natural_language_rule.config')
    def test_detect_language_llm_not_configured(self, mock_config):
        """Test language detection when config is not configured."""
        mock_config.is_configured.return_value = False
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o'}
        )
        
        result = rule._detect_language_llm('Hello, how are you?')
        assert result is None
    
    @patch('deimos_router.rules.natural_language_rule.config')
    @patch('deimos_router.rules.natural_language_rule.openai.OpenAI')
    def test_detect_language_llm_none_response(self, mock_openai, mock_config):
        """Test language detection when LLM returns 'None'."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = 'None'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'}
        )
        
        result = rule._detect_language_llm('Some unclear text')
        assert result is None
    
    @patch('deimos_router.rules.natural_language_rule.config')
    @patch('deimos_router.rules.natural_language_rule.openai.OpenAI')
    def test_detect_language_llm_invalid_response(self, mock_openai, mock_config):
        """Test language detection when LLM returns invalid language."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = 'de'  # German, not in our mappings
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'}
        )
        
        result = rule._detect_language_llm('Guten Tag, wie geht es Ihnen?')
        assert result is None
    
    @patch('deimos_router.rules.natural_language_rule.config')
    @patch('deimos_router.rules.natural_language_rule.openai.OpenAI')
    def test_detect_language_llm_exception(self, mock_openai, mock_config):
        """Test language detection when LLM call raises exception."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        
        # Mock OpenAI to raise exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception('API Error')
        mock_openai.return_value = mock_client
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'}
        )
        
        result = rule._detect_language_llm('Hello, how are you?')
        assert result is None
    
    @patch.object(NaturalLanguageRule, '_detect_language_llm')
    def test_evaluate_successful_detection(self, mock_detect):
        """Test evaluation with successful language detection."""
        mock_detect.return_value = 'es'
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Hola, ¿cómo estás?'}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'claude-3-sonnet'
    
    @patch.object(NaturalLanguageRule, '_detect_language_llm')
    def test_evaluate_no_detection(self, mock_detect):
        """Test evaluation when no language is detected."""
        mock_detect.return_value = None
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Some unclear text'}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-4o-mini'
    
    @patch.object(NaturalLanguageRule, '_detect_language_llm')
    def test_evaluate_unmapped_language(self, mock_detect):
        """Test evaluation when detected language is not in mappings."""
        mock_detect.return_value = 'de'  # German, not in mappings
        
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Guten Tag'}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-4o-mini'
    
    def test_evaluate_empty_text(self):
        """Test evaluation with empty text content."""
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {'messages': []}
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-4o-mini'
    
    def test_repr(self):
        """Test string representation."""
        rule = NaturalLanguageRule(
            name='test_rule',
            language_mappings={'en': 'gpt-4o', 'es': 'claude-3-sonnet', 'fr': 'gpt-4o-mini'}
        )
        
        repr_str = repr(rule)
        assert "NaturalLanguageRule(name='test_rule'" in repr_str
        assert 'en' in repr_str
        assert 'es' in repr_str
        assert 'fr' in repr_str
