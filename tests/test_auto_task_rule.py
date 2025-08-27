"""Tests for AutoTaskRule."""

import pytest
from unittest.mock import Mock, patch
from deimos_router.rules import AutoTaskRule, Decision


class TestAutoTaskRule:
    """Test cases for AutoTaskRule."""
    
    def test_init(self):
        """Test rule initialization."""
        task_mappings = {
            'writing': 'gpt-4o',
            'coding': 'claude-3-sonnet',
            'analysis': 'gpt-4o-mini'
        }
        
        rule = AutoTaskRule(
            name='auto_task_router',
            task_mappings=task_mappings,
            default='gpt-4o-mini'
        )
        
        assert rule.name == 'auto_task_router'
        assert rule.task_mappings == task_mappings
        assert rule.default == 'gpt-4o-mini'
        assert rule.llm_model == 'gpt-4o-mini'  # Default from config
    
    def test_init_with_custom_model(self):
        """Test rule initialization with custom LLM model."""
        task_mappings = {'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'}
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings=task_mappings,
            llm_model='gpt-4o'
        )
        
        assert rule.llm_model == 'gpt-4o'
    
    def test_extract_text_content(self):
        """Test text content extraction from messages."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o'}
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Write a blog post about AI'},
                {'role': 'assistant', 'content': 'I can help you with that!'},
                {'role': 'user', 'content': 'Make it engaging and informative'}
            ]
        }
        
        text = rule._extract_text_content(request_data)
        expected = 'Write a blog post about AI\nI can help you with that!\nMake it engaging and informative'
        assert text == expected
    
    def test_extract_text_content_empty_messages(self):
        """Test text extraction with empty messages."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o'}
        )
        
        request_data = {'messages': []}
        text = rule._extract_text_content(request_data)
        assert text == ''
    
    def test_extract_text_content_no_messages(self):
        """Test text extraction with no messages key."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o'}
        )
        
        request_data = {}
        text = rule._extract_text_content(request_data)
        assert text == ''
    
    @patch('deimos_router.rules.auto_task_rule.config')
    @patch('deimos_router.rules.auto_task_rule.openai.OpenAI')
    def test_detect_task_llm_success(self, mock_openai, mock_config):
        """Test successful task detection via LLM."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        mock_config.get_default_model.return_value = 'gpt-4o-mini'
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = 'writing'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'}
        )
        
        result = rule._detect_task_llm('Write a blog post about machine learning')
        assert result == 'writing'
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o-mini'
        assert call_args[1]['max_tokens'] == 20
        assert call_args[1]['temperature'] == 0.1
    
    @patch('deimos_router.rules.auto_task_rule.config')
    def test_detect_task_llm_not_configured(self, mock_config):
        """Test task detection when config is not configured."""
        mock_config.is_configured.return_value = False
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o'}
        )
        
        result = rule._detect_task_llm('Write a blog post')
        assert result is None
    
    @patch('deimos_router.rules.auto_task_rule.config')
    @patch('deimos_router.rules.auto_task_rule.openai.OpenAI')
    def test_detect_task_llm_none_response(self, mock_openai, mock_config):
        """Test task detection when LLM returns 'none'."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = 'none'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'}
        )
        
        result = rule._detect_task_llm('Some unclear request')
        assert result is None
    
    @patch('deimos_router.rules.auto_task_rule.config')
    @patch('deimos_router.rules.auto_task_rule.openai.OpenAI')
    def test_detect_task_llm_invalid_response(self, mock_openai, mock_config):
        """Test task detection when LLM returns invalid task."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        
        # Mock OpenAI response
        mock_message = Mock()
        mock_message.content = 'translation'  # Not in our mappings
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'}
        )
        
        result = rule._detect_task_llm('Translate this text to French')
        assert result is None
    
    @patch('deimos_router.rules.auto_task_rule.config')
    @patch('deimos_router.rules.auto_task_rule.openai.OpenAI')
    def test_detect_task_llm_case_insensitive(self, mock_openai, mock_config):
        """Test task detection is case insensitive."""
        # Mock config
        mock_config.is_configured.return_value = True
        mock_config.get_credentials.return_value = {
            'api_key': 'test-key',
            'api_url': 'https://api.openai.com/v1'
        }
        
        # Mock OpenAI response with uppercase
        mock_message = Mock()
        mock_message.content = 'WRITING'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'}
        )
        
        result = rule._detect_task_llm('Write a story')
        assert result == 'writing'  # Should match despite case difference
    
    @patch('deimos_router.rules.auto_task_rule.config')
    @patch('deimos_router.rules.auto_task_rule.openai.OpenAI')
    def test_detect_task_llm_exception(self, mock_openai, mock_config):
        """Test task detection when LLM call raises exception."""
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
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'}
        )
        
        result = rule._detect_task_llm('Write a blog post')
        assert result is None
    
    @patch.object(AutoTaskRule, '_detect_task_llm')
    def test_evaluate_successful_detection(self, mock_detect):
        """Test evaluation with successful task detection."""
        mock_detect.return_value = 'coding'
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Help me debug this Python function'}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'claude-3-sonnet'
    
    @patch.object(AutoTaskRule, '_detect_task_llm')
    def test_evaluate_no_detection(self, mock_detect):
        """Test evaluation when no task is detected."""
        mock_detect.return_value = None
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Some unclear request'}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-4o-mini'
    
    @patch.object(AutoTaskRule, '_detect_task_llm')
    def test_evaluate_unmapped_task(self, mock_detect):
        """Test evaluation when detected task is not in mappings."""
        mock_detect.return_value = 'translation'  # Not in mappings
        
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {
            'messages': [
                {'role': 'user', 'content': 'Translate this to French'}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-4o-mini'
    
    def test_evaluate_empty_text(self):
        """Test evaluation with empty text content."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'},
            default='gpt-4o-mini'
        )
        
        request_data = {'messages': []}
        
        decision = rule.evaluate(request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-4o-mini'
    
    def test_add_task_mapping(self):
        """Test adding a new task mapping."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o'}
        )
        
        rule.add_task_mapping('coding', 'claude-3-sonnet')
        assert 'coding' in rule.task_mappings
        assert rule.task_mappings['coding'] == 'claude-3-sonnet'
    
    def test_remove_task_mapping(self):
        """Test removing a task mapping."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet'}
        )
        
        rule.remove_task_mapping('coding')
        assert 'coding' not in rule.task_mappings
        assert 'writing' in rule.task_mappings
    
    def test_remove_nonexistent_task_mapping(self):
        """Test removing a task mapping that doesn't exist."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o'}
        )
        
        # Should not raise an error
        rule.remove_task_mapping('nonexistent')
        assert 'writing' in rule.task_mappings
    
    def test_repr(self):
        """Test string representation."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={'writing': 'gpt-4o', 'coding': 'claude-3-sonnet', 'analysis': 'gpt-4o-mini'}
        )
        
        repr_str = repr(rule)
        assert "AutoTaskRule(name='test_rule'" in repr_str
        assert 'writing' in repr_str
        assert 'coding' in repr_str
        assert 'analysis' in repr_str
    
    def test_common_tasks_detection_scenarios(self):
        """Test scenarios with common LLM tasks."""
        rule = AutoTaskRule(
            name='test_rule',
            task_mappings={
                'writing': 'gpt-4o',
                'coding': 'claude-3-sonnet',
                'analysis': 'gpt-4o-mini',
                'summarization': 'gpt-4o-mini',
                'translation': 'claude-3-haiku'
            }
        )
        
        # Test that the rule is properly configured for common tasks
        assert len(rule.task_mappings) == 5
        assert 'writing' in rule.task_mappings
        assert 'coding' in rule.task_mappings
        assert 'analysis' in rule.task_mappings
        assert 'summarization' in rule.task_mappings
        assert 'translation' in rule.task_mappings
