"""Tests for the explain feature."""

import pytest
from src.deimos_router.router import Router, register_router, clear_routers
from src.deimos_router.rules.task_rule import TaskRule
from src.deimos_router.rules.code_rule import CodeRule
from src.deimos_router.rules.base import ExplanationEntry
from src.deimos_router.rules import register_rule, clear_rules
from src.deimos_router.chat import chat


class TestExplainFeature:
    """Test cases for the explain feature."""
    
    def setup_method(self):
        """Set up test fixtures."""
        clear_routers()
        clear_rules()
    
    def teardown_method(self):
        """Clean up after tests."""
        clear_routers()
        clear_rules()
    
    def test_explanation_entry_creation(self):
        """Test ExplanationEntry creation and serialization."""
        entry = ExplanationEntry(
            rule_type="TaskRule",
            rule_name="test-rule",
            rule_trigger="creative writing",
            decision="gpt-4"
        )
        
        assert entry.rule_type == "TaskRule"
        assert entry.rule_name == "test-rule"
        assert entry.rule_trigger == "creative writing"
        assert entry.decision == "gpt-4"
        
        # Test serialization
        entry_dict = entry.to_dict()
        expected = {
            "rule_type": "TaskRule",
            "rule_name": "test-rule",
            "rule_trigger": "creative writing",
            "decision": "gpt-4"
        }
        assert entry_dict == expected
    
    def test_explanation_entry_with_none_trigger(self):
        """Test ExplanationEntry with None trigger."""
        entry = ExplanationEntry(
            rule_type="TaskRule",
            rule_name="test-rule",
            rule_trigger=None,
            decision="gpt-4"
        )
        
        assert entry.rule_trigger == "None"
        
        entry_dict = entry.to_dict()
        assert entry_dict["rule_trigger"] == "None"
    
    def test_task_rule_with_explanation(self):
        """Test TaskRule provides trigger information."""
        task_rule = TaskRule("test-task-rule", {
            "creative writing": "gpt-4",
            "code review": "gpt-4o"
        })
        
        # Test matching task
        request_data = {"task": "creative writing"}
        decision = task_rule.evaluate(request_data)
        
        assert decision.value == "gpt-4"
        assert decision.trigger == "creative writing"
        
        # Test non-matching task
        request_data = {"task": "unknown"}
        decision = task_rule.evaluate(request_data)
        
        assert decision.value is None
        assert decision.trigger == "unknown"
        
        # Test no task
        request_data = {}
        decision = task_rule.evaluate(request_data)
        
        assert decision.value is None
        assert decision.trigger is None
    
    def test_code_rule_with_explanation(self):
        """Test CodeRule provides trigger information."""
        code_rule = CodeRule("test-code-rule", 
                           code="gpt-4o", 
                           not_code="gpt-3.5-turbo")
        
        # Test code detection
        request_data = {
            "messages": [{"role": "user", "content": "def hello():\n    print('Hello')"}]
        }
        decision = code_rule.evaluate(request_data)
        
        assert decision.value == "gpt-4o"
        assert decision.trigger == "code_detected"
        
        # Test no code detection
        request_data = {
            "messages": [{"role": "user", "content": "What is the weather like?"}]
        }
        decision = code_rule.evaluate(request_data)
        
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "no_code_detected"
        
        # Test empty content
        request_data = {"messages": []}
        decision = code_rule.evaluate(request_data)
        
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "no_content"
    
    def test_router_select_model_with_explanation(self):
        """Test router's select_model_with_explanation method."""
        # Create rules
        task_rule = TaskRule("task-rule", {"creative writing": "gpt-4"})
        code_rule = CodeRule("code-rule", code="gpt-4o", not_code="gpt-3.5-turbo")
        
        # Create router
        router = Router(
            name="test-router",
            rules=[task_rule, code_rule],
            default="gpt-3.5-turbo"
        )
        
        # Test task rule match
        request_data = {
            "messages": [{"role": "user", "content": "Write a story"}],
            "task": "creative writing"
        }
        
        model, explanation = router.select_model_with_explanation(request_data)
        
        assert model == "gpt-4"
        assert len(explanation) == 1
        assert explanation[0].rule_type == "TaskRule"
        assert explanation[0].rule_name == "task-rule"
        assert explanation[0].rule_trigger == "creative writing"
        assert explanation[0].decision == "gpt-4"
    
    def test_router_explanation_accumulation(self):
        """Test that explanations accumulate through multiple rules."""
        # Create rules
        task_rule = TaskRule("task-rule", {"debugging": "claude-3-sonnet"})
        code_rule = CodeRule("code-rule", code="gpt-4o", not_code="gpt-3.5-turbo")
        
        # Create router
        router = Router(
            name="test-router",
            rules=[task_rule, code_rule],
            default="gpt-3.5-turbo"
        )
        
        # Test case where task rule doesn't match, but code rule does
        request_data = {
            "messages": [{"role": "user", "content": "def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"}],
            "task": "unknown_task"
        }
        
        model, explanation = router.select_model_with_explanation(request_data)
        
        assert model == "gpt-4o"
        assert len(explanation) == 2
        
        # First rule (task rule) - no match
        assert explanation[0].rule_type == "TaskRule"
        assert explanation[0].rule_name == "task-rule"
        assert explanation[0].rule_trigger == "unknown_task"
        assert explanation[0].decision == "no_match"
        
        # Second rule (code rule) - match
        assert explanation[1].rule_type == "CodeRule"
        assert explanation[1].rule_name == "code-rule"
        assert explanation[1].rule_trigger == "code_detected"
        assert explanation[1].decision == "gpt-4o"
    
    def test_router_default_explanation(self):
        """Test explanation when falling back to default."""
        # Create router with no rules and specific models list
        router = Router(
            name="test-router",
            rules=[],
            models=["gpt-3.5-turbo"],  # Specify exact models to avoid randomness
            default="gpt-3.5-turbo"
        )
        
        request_data = {"messages": [{"role": "user", "content": "Hello"}]}
        
        model, explanation = router.select_model_with_explanation(request_data)
        
        assert model == "gpt-3.5-turbo"
        assert len(explanation) == 1
        assert explanation[0].rule_type == "default"
        assert explanation[0].rule_name == "default"
        assert explanation[0].rule_trigger == "None"
        assert explanation[0].decision == "gpt-3.5-turbo"
    
    def test_chat_api_explain_parameter(self):
        """Test that chat API accepts explain parameter."""
        # Create and register a simple router
        task_rule = TaskRule("chat-task-rule", {"test": "gpt-4"})
        register_rule(task_rule)
        
        router = Router(
            name="chat-test-router",
            rules=[task_rule],
            default="gpt-3.5-turbo"
        )
        register_router(router)
        
        # Test that the create method accepts explain parameter
        # Note: This would normally make an API call, but we're just testing the interface
        try:
            # This should not raise an error about unexpected parameters
            messages = [{"role": "user", "content": "Test message"}]
            
            # The method signature should accept explain parameter
            import inspect
            sig = inspect.signature(chat.completions.create)
            assert 'explain' in sig.parameters
            
            # Parameter should have correct default
            explain_param = sig.parameters['explain']
            assert explain_param.default is False
            
        except Exception as e:
            pytest.fail(f"Chat API should accept explain parameter: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
