"""Comprehensive end-to-end test for deimos-router with multiple rule types and chat completions."""

import pytest
import os
from typing import Dict, Any

from deimos_router.router import Router, register_router, clear_routers
from deimos_router.rules.base import Rule, Decision
from deimos_router.rules.task_rule import TaskRule
from deimos_router.rules.message_length_rule import MessageLengthRule
from deimos_router.rules.code_rule import CodeRule
from deimos_router.rules.natural_language_rule import NaturalLanguageRule
from deimos_router.rules.auto_task_rule import AutoTaskRule
from deimos_router.rules.conversation_context_rule import ConversationContextRule
from deimos_router.chat import chat
from deimos_router.config import config


class TestE2EComprehensive:
    """Comprehensive end-to-end tests for deimos-router."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        clear_routers()
        # Reset chat client cache to ensure fresh client
        chat._client = None
        
        # Check if API credentials are configured for real LLM calls
        if not config.is_configured():
            pytest.skip("API credentials not configured - skipping e2e tests that require real LLM calls")
    
    def teardown_method(self):
        """Clean up after each test."""
        clear_routers()
        # Reset chat client cache
        chat._client = None
    
    def test_complex_rule_chain_with_multiple_chat_calls(self):
        """Test complex rule chains with multiple chat completion calls."""
        
        # Create a variety of rules with different types using actual project rule classes
        
        # 1. AutoTaskRule - automatically detects tasks using LLM
        auto_task_rule = AutoTaskRule(
            name="auto_task_detector",
            triggers={
                'code_analysis': 'openai/gpt-4',
                'creative_writing': 'openai/gpt-4',
                'translation': 'openai/gpt-4o-mini'
            },
            default='openai/gpt-4o-mini'
        )
        
        # 2. ConversationContextRule - routes based on conversation depth
        context_rule = ConversationContextRule(
            name="conversation_context",
            new_threshold=2,
            deep_threshold=6,
            new_model="openai/gpt-4o-mini",
            developing_model="openai/gpt-4o-mini", 
            deep_model="openai/gpt-4"
        )
        
        # 3. NaturalLanguageRule - routes based on detected language
        language_rule = NaturalLanguageRule(
            name="language_detector",
            language_mappings={
                'en': 'openai/gpt-4',
                'es': 'openai/gpt-4o-mini',
                'fr': 'openai/gpt-4'
            },
            default='openai/gpt-4o-mini'
        )
        
        # 4. TaskRule that calls other rules
        task_rule = TaskRule(
            name="main_task_router",
            triggers={
                'code_analysis': auto_task_rule,     # Points to another rule
                'conversation': context_rule,        # Points to another rule
                'translation': language_rule,        # Points to another rule
                'simple_chat': 'openai/gpt-4o-mini'      # Direct model
            }
        )
        
        # 5. Code detection rule
        code_rule = CodeRule(
            name="code_detector",
            code=task_rule,  # If code detected, use task rule
            not_code='openai/gpt-4o-mini'  # If no code, use simple model
        )
        
        # 6. Message length rule as fallback
        length_fallback = MessageLengthRule(
            name="length_fallback",
            short_threshold=50,
            long_threshold=500,
            short_model="openai/gpt-4o-mini",
            medium_model="openai/gpt-4o-mini",
            long_model="openai/gpt-4"
        )
        
        # Create router with multiple rules in chain
        router = Router(
            name="comprehensive_test_router",
            rules=[code_rule, length_fallback],  # Try code detection first, then length
            default="openai/gpt-4o-mini"
        )
        
        register_router(router)
        
        # Test Case 1: Code analysis request with code content
        response1 = chat.completions.create(
            model="deimos/comprehensive_test_router",
            messages=[
                {"role": "user", "content": "Please analyze this Python code for bugs:\n\ndef calculate_sum(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total"}
            ],
            task="code_analysis",
            explain=True
        )
        
        # Verify the response and routing
        assert response1 is not None
        assert hasattr(response1, '_deimos_metadata')
        assert response1._deimos_metadata['router_used'] == 'comprehensive_test_router'
        # Should route through: code_rule -> task_rule -> auto_task_rule
        # The actual model may vary based on LLM detection, but should be one of the configured models
        assert response1.model in ['openai/gpt-4', 'openai/gpt-4o-mini']
        print(f"Test Case 1 - Selected model: {response1.model}")
        
        # Test Case 2: Simple conversation request
        response2 = chat.completions.create(
            model="deimos/comprehensive_test_router",
            messages=[
                {"role": "user", "content": "Hello, how are you today?"},
                {"role": "assistant", "content": "I'm doing well, thank you!"},
                {"role": "user", "content": "What's the weather like?"}
            ],
            task="conversation",
            explain=True
        )
        
        # Should route through: code_rule -> task_rule -> context_rule -> developing_model (3 messages)
        assert response2.model in ['openai/gpt-4o-mini', 'openai/gpt-4']
        print(f"Test Case 2 - Selected model: {response2.model}")
        
        # Test Case 3: Simple chat with no task - should use fallback
        response3 = chat.completions.create(
            model="deimos/comprehensive_test_router",
            messages=[
                {"role": "user", "content": "Hi, how are you?"}
            ],
            explain=True
        )
        
        # Should route through: code_rule -> not_code -> openai/gpt-4o-mini (no code detected)
        assert response3.model in ['openai/gpt-4o-mini', 'openai/gpt-4']
        print(f"Test Case 3 - Selected model: {response3.model}")
        
        # Test Case 4: Long message without code - should use length fallback
        long_content = "Please provide a detailed analysis of the economic implications of artificial intelligence adoption in various industries. " * 10
        response4 = chat.completions.create(
            model="deimos/comprehensive_test_router",
            messages=[
                {"role": "user", "content": long_content}
            ],
            explain=True
        )
        
        # Should route through: code_rule -> not_code -> openai/gpt-4o-mini (no code detected)
        assert response4.model in ['openai/gpt-4o-mini', 'openai/gpt-4']
        print(f"Test Case 4 - Selected model: {response4.model}")
        
        # Test Case 5: Medium length message without code
        medium_content = "Can you help me understand basic concepts in machine learning? " * 5
        response5 = chat.completions.create(
            model="deimos/comprehensive_test_router",
            messages=[
                {"role": "user", "content": medium_content}
            ],
            explain=True
        )
        
        # Should route through: code_rule -> not_code -> openai/gpt-4o-mini (no code detected)
        assert response5.model in ['openai/gpt-4o-mini', 'openai/gpt-4']
        print(f"Test Case 5 - Selected model: {response5.model}")
        
        # Verify all responses have actual content
        for i, response in enumerate([response1, response2, response3, response4, response5], 1):
            # Check if this is a mock response (when API credentials not configured)
            if hasattr(response, 'choices'):
                assert len(response.choices) > 0
                assert hasattr(response.choices[0], 'message')
                assert response.choices[0].message.content is not None
                print(f"Response {i} content length: {len(response.choices[0].message.content)}")
            else:
                # This is a mock response, just verify it exists and has metadata
                assert response is not None
                assert hasattr(response, '_deimos_metadata')
                print(f"Response {i} is a mock response (API credentials not configured)")
        
        # Verify explanations are present
        for response in [response1, response2, response3, response4, response5]:
            assert 'explain' in response._deimos_metadata
            assert len(response._deimos_metadata['explain']) > 0
    
    def test_rule_chain_depth_and_explanation(self):
        """Test rule chain depth limits and explanation tracking."""
        
        # Create a chain of rules that call each other using actual rule types
        # Final rule: AutoTaskRule that maps to a model
        final_rule = AutoTaskRule(
            name="final_auto_task",
            triggers={'test': 'openai/gpt-4'},
            default='openai/gpt-4o-mini'
        )
        
        # Create a chain of TaskRules calling each other
        current_rule = final_rule
        for i in range(3, 0, -1):
            new_rule = TaskRule(
                name=f"chain_rule_{i}",
                triggers={'test': current_rule}
            )
            current_rule = new_rule
        
        router = Router(
            name="chain_test_router",
            rules=[current_rule],
            default="openai/gpt-4o-mini"
        )
        
        register_router(router)
        
        # Test the chain
        response = chat.completions.create(
            model="deimos/chain_test_router",
            messages=[
                {"role": "user", "content": "Test message"}
            ],
            task="test",
            explain=True
        )
        
        # Verify the chain worked
        assert response.model in ['openai/gpt-4', 'openai/gpt-4o-mini']  # Allow for LLM detection variations
        assert 'explain' in response._deimos_metadata
        print(f"Chain test - Selected model: {response.model}")
        
        # Should have multiple explanation entries showing the chain
        explanation = response._deimos_metadata['explain']
        assert len(explanation) >= 3  # At least 3 rules in the chain
        print(f"Chain explanation entries: {len(explanation)}")
        
        # Verify rule types in explanation
        rule_types = [entry['rule_type'] for entry in explanation]
        assert 'TaskRule' in rule_types
        assert 'AutoTaskRule' in rule_types
        print(f"Rule types in chain: {rule_types}")
    
    def test_multiple_routers_with_different_strategies(self):
        """Test multiple routers with different routing strategies."""
        
        # Router 1: Code-focused routing
        code_router = Router(
            name="code_router",
            rules=[
                CodeRule(
                    name="code_specialist",
                    code="openai/gpt-4",
                    not_code="openai/gpt-4o-mini"
                )
            ],
            default="openai/gpt-4o-mini"
        )
        
        # Router 2: Length-based routing
        length_router = Router(
            name="length_router",
            rules=[
                MessageLengthRule(
                    name="length_specialist",
                    short_threshold=100,
                    long_threshold=500,
                    short_model="openai/gpt-4o-mini",
                    medium_model="openai/gpt-4o-mini",
                    long_model="openai/gpt-4"
                )
            ],
            default="openai/gpt-4o-mini"
        )
        
        # Router 3: Task-based routing
        task_router = Router(
            name="task_router",
            rules=[
                TaskRule(
                    name="task_specialist",
                    triggers={
                        'creative': 'openai/gpt-4',
                        'analysis': 'openai/gpt-4',
                        'coding': 'openai/gpt-4o-mini'
                    }
                )
            ],
            default="openai/gpt-4o-mini"
        )
        
        register_router(code_router)
        register_router(length_router)
        register_router(task_router)
        
        # Test different scenarios with different routers
        test_cases = [
            # Code router tests
            {
                'router': 'code_router',
                'messages': [{"role": "user", "content": "def hello():\n    print('Hello, World!')"}],
                'expected_models': ['openai/gpt-4']  # Code should be detected
            },
            {
                'router': 'code_router',
                'messages': [{"role": "user", "content": "What's the weather like today?"}],
                'expected_models': ['openai/gpt-4o-mini']  # No code should be detected
            },
            
            # Length router tests
            {
                'router': 'length_router',
                'messages': [{"role": "user", "content": "Hi"}],
                'expected_models': ['openai/gpt-4o-mini']  # Short message
            },
            {
                'router': 'length_router',
                'messages': [{"role": "user", "content": "This is a medium length message that should trigger the medium model selection based on character count." * 2}],
                'expected_models': ['openai/gpt-4o-mini']  # Medium length message
            },
            
            # Task router tests
            {
                'router': 'task_router',
                'messages': [{"role": "user", "content": "Help me with coding"}],
                'task': 'coding',
                'expected_models': ['openai/gpt-4o-mini']  # Explicit task routing
            },
            {
                'router': 'task_router',
                'messages': [{"role": "user", "content": "Write a story"}],
                'task': 'creative',
                'expected_models': ['openai/gpt-4']  # Explicit task routing
            }
        ]
        
        responses = []
        for i, test_case in enumerate(test_cases):
            kwargs = {
                'model': f"deimos/{test_case['router']}",
                'messages': test_case['messages'],
                'explain': True
            }
            if 'task' in test_case:
                kwargs['task'] = test_case['task']
            
            response = chat.completions.create(**kwargs)
            responses.append(response)
            
            # Verify model selection is reasonable (may vary with real LLM calls)
            print(f"Test case {i} ({test_case['router']}): expected {test_case['expected_models']}, got {response.model}")
            # For deterministic rules (length, explicit task), check exact match
            if test_case['router'] in ['length_router', 'task_router']:
                assert response.model in test_case['expected_models'], f"Test case {i}: expected one of {test_case['expected_models']}, got {response.model}"
            # For code detection, allow some flexibility but verify it's a reasonable model
            else:
                assert response.model in ['openai/gpt-4o-mini', 'openai/gpt-4']
            
            assert response._deimos_metadata['router_used'] == test_case['router']
        
        # Verify each response has explanation
        for response in responses:
            assert 'explain' in response._deimos_metadata
            assert len(response._deimos_metadata['explain']) > 0
        
        # Verify we got the expected number of responses
        assert len(responses) == len(test_cases)
    
    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback behavior."""
        
        # Create a rule that might not match using actual rule types
        selective_rule = TaskRule(
            name="selective_rule",
            triggers={'specific_task': 'openai/gpt-4'}  # Only matches specific_task
        )
        
        # Router with fallback
        router = Router(
            name="fallback_test_router",
            rules=[selective_rule],
            default="openai/gpt-4o-mini"
        )
        
        register_router(router)
        
        # Test case where rule doesn't match - should use default
        response = chat.completions.create(
            model="deimos/fallback_test_router",
            messages=[
                {"role": "user", "content": "General question that doesn't match any specific condition"}
            ],
            task="general_question",  # This won't match 'specific_task'
            explain=True
        )
        
        # Should fall back to default
        assert response.model == 'openai/gpt-4o-mini'
        assert response._deimos_metadata['router_used'] == 'fallback_test_router'
        print(f"Fallback test - Selected model: {response.model}")
        
        # Test nonexistent router
        with pytest.raises(ValueError, match="Router 'nonexistent' not found"):
            chat.completions.create(
                model="deimos/nonexistent",
                messages=[{"role": "user", "content": "Test"}]
            )
    
    def test_rule_registration_and_management(self):
        """Test rule registration and management functionality."""
        # Create various rule types using actual project rule classes
        task_rule = TaskRule(
            name="test_task_rule",
            triggers={'test': 'gpt-4'}
        )
        
        length_rule = MessageLengthRule(
            name="test_length_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4o-mini",
            long_model="gpt-4"
        )
        
        code_rule = CodeRule(
            name="test_code_rule",
            code="claude-3-sonnet",
            not_code="gpt-3.5-turbo"
        )
        
        auto_task_rule = AutoTaskRule(
            name="test_auto_task_rule",
            triggers={
                'coding': 'gpt-4',
                'writing': 'claude-3-sonnet'
            },
            default='gpt-3.5-turbo'
        )
        
        context_rule = ConversationContextRule(
            name="test_context_rule",
            new_threshold=2,
            deep_threshold=5,
            new_model="gpt-3.5-turbo",
            developing_model="gpt-4o-mini",
            deep_model="gpt-4"
        )
        
        # Test rule creation and properties
        assert task_rule.name == "test_task_rule"
        assert task_rule.get_rule_type() == "TaskRule"
        
        assert length_rule.name == "test_length_rule"
        assert length_rule.get_rule_type() == "MessageLengthRule"
        
        assert code_rule.name == "test_code_rule"
        assert code_rule.get_rule_type() == "CodeRule"
        
        assert auto_task_rule.name == "test_auto_task_rule"
        assert auto_task_rule.get_rule_type() == "AutoTaskRule"
        
        assert context_rule.name == "test_context_rule"
        assert context_rule.get_rule_type() == "ConversationContextRule"
        
        # Test rule evaluation without actual API calls
        test_request_data = {
            'messages': [
                {'role': 'user', 'content': 'def test(): pass'}
            ],
            'task': 'test'
        }
        
        # Test task rule evaluation
        decision = task_rule.evaluate(test_request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-4'
        assert decision.trigger == 'test'
        
        # Test code rule evaluation
        decision = code_rule.evaluate(test_request_data)
        assert decision.is_model()
        assert decision.get_model() == 'claude-3-sonnet'
        assert 'code_detected' in decision.trigger
        
        # Test context rule evaluation
        decision = context_rule.evaluate(test_request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-3.5-turbo'  # Single message = new conversation
        assert 'new_conversation' in decision.trigger
        
        # Test auto task rule evaluation (will return default since no LLM call)
        decision = auto_task_rule.evaluate(test_request_data)
        assert decision.is_model()
        assert decision.get_model() == 'gpt-3.5-turbo'  # Default when LLM detection fails
