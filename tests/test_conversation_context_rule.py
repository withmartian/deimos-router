"""Tests for ConversationContextRule."""

import pytest
from deimos_router.rules.conversation_context_rule import ConversationContextRule
from deimos_router.rules.base import Decision


class TestConversationContextRule:
    """Test cases for ConversationContextRule."""
    
    def test_init_valid_thresholds(self):
        """Test initialization with valid thresholds."""
        rule = ConversationContextRule(
            name="test_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="gpt-3.5-turbo",
            developing_model="gpt-4",
            deep_model="gpt-4-turbo"
        )
        
        assert rule.name == "test_rule"
        assert rule.new_threshold == 3
        assert rule.deep_threshold == 10
        assert rule.new_model == "gpt-3.5-turbo"
        assert rule.developing_model == "gpt-4"
        assert rule.deep_model == "gpt-4-turbo"
    
    def test_init_invalid_thresholds(self):
        """Test initialization with invalid thresholds."""
        # new_threshold >= deep_threshold
        with pytest.raises(ValueError, match="new_threshold must be less than deep_threshold"):
            ConversationContextRule(
                name="test_rule",
                new_threshold=10,
                deep_threshold=5,
                new_model="model1",
                developing_model="model2",
                deep_model="model3"
            )
        
        # Equal thresholds
        with pytest.raises(ValueError, match="new_threshold must be less than deep_threshold"):
            ConversationContextRule(
                name="test_rule",
                new_threshold=5,
                deep_threshold=5,
                new_model="model1",
                developing_model="model2",
                deep_model="model3"
            )
        
        # Negative thresholds
        with pytest.raises(ValueError, match="thresholds must be positive integers"):
            ConversationContextRule(
                name="test_rule",
                new_threshold=0,
                deep_threshold=5,
                new_model="model1",
                developing_model="model2",
                deep_model="model3"
            )
    
    def test_evaluate_new_conversation(self):
        """Test evaluation for new conversations."""
        rule = ConversationContextRule(
            name="context_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="gpt-3.5-turbo",
            developing_model="gpt-4",
            deep_model="gpt-4-turbo"
        )
        
        # Single message conversation
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-3.5-turbo"
        assert "new_conversation_1_messages" in decision.trigger
        assert decision.is_model()
    
    def test_evaluate_developing_conversation(self):
        """Test evaluation for developing conversations."""
        rule = ConversationContextRule(
            name="context_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="gpt-3.5-turbo",
            developing_model="gpt-4",
            deep_model="gpt-4-turbo"
        )
        
        # 5-message conversation
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"},
                {"role": "assistant", "content": "I'm doing well, thanks!"},
                {"role": "user", "content": "What can you help me with?"}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-4"
        assert "developing_conversation_5_messages" in decision.trigger
        assert decision.is_model()
    
    def test_evaluate_deep_conversation(self):
        """Test evaluation for deep conversations."""
        rule = ConversationContextRule(
            name="context_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="gpt-3.5-turbo",
            developing_model="gpt-4",
            deep_model="gpt-4-turbo"
        )
        
        # 12-message conversation
        messages = []
        for i in range(12):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": f"Message {i+1}"})
        
        request_data = {"messages": messages}
        
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-4-turbo"
        assert "deep_conversation_12_messages" in decision.trigger
        assert decision.is_model()
    
    def test_evaluate_empty_messages(self):
        """Test evaluation with empty messages."""
        rule = ConversationContextRule(
            name="context_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="gpt-3.5-turbo",
            developing_model="gpt-4",
            deep_model="gpt-4-turbo"
        )
        
        request_data = {"messages": []}
        
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-3.5-turbo"  # Should use new_model for 0 messages
        assert "new_conversation_0_messages" in decision.trigger
    
    def test_evaluate_with_system_messages(self):
        """Test evaluation with system messages included."""
        rule = ConversationContextRule(
            name="context_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="gpt-3.5-turbo",
            developing_model="gpt-4",
            deep_model="gpt-4-turbo"
        )
        
        request_data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]
        }
        
        decision = rule.evaluate(request_data)
        # Should count all messages including system
        assert decision.value == "gpt-4"  # 4 messages >= 3 threshold
        assert "developing_conversation_4_messages" in decision.trigger
    
    def test_analyze_conversation_context(self):
        """Test the conversation context analysis."""
        rule = ConversationContextRule(
            name="context_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="model1",
            developing_model="model2",
            deep_model="model3"
        )
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello there!"},
                {"role": "assistant", "content": "Hi! How can I help you today?"},
                {"role": "user", "content": "I need help with Python programming."}
            ]
        }
        
        context_info = rule._analyze_conversation_context(request_data)
        
        assert context_info['message_count'] == 3
        assert context_info['user_messages'] == 2
        assert context_info['assistant_messages'] == 1
        assert context_info['total_chars'] > 0
        assert context_info['avg_message_length'] > 0
    
    def test_get_thresholds(self):
        """Test getting current thresholds."""
        rule = ConversationContextRule(
            name="test_rule",
            new_threshold=5,
            deep_threshold=15,
            new_model="model1",
            developing_model="model2",
            deep_model="model3"
        )
        
        thresholds = rule.get_thresholds()
        assert thresholds == {'new_threshold': 5, 'deep_threshold': 15}
    
    def test_update_thresholds_valid(self):
        """Test updating thresholds with valid values."""
        rule = ConversationContextRule(
            name="test_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="model1",
            developing_model="model2",
            deep_model="model3"
        )
        
        # Update both thresholds
        rule.update_thresholds(new_threshold=5, deep_threshold=15)
        assert rule.new_threshold == 5
        assert rule.deep_threshold == 15
        
        # Update only one threshold
        rule.update_thresholds(new_threshold=2)
        assert rule.new_threshold == 2
        assert rule.deep_threshold == 15
        
        rule.update_thresholds(deep_threshold=20)
        assert rule.new_threshold == 2
        assert rule.deep_threshold == 20
    
    def test_update_thresholds_invalid(self):
        """Test updating thresholds with invalid values."""
        rule = ConversationContextRule(
            name="test_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="model1",
            developing_model="model2",
            deep_model="model3"
        )
        
        # new_threshold >= deep_threshold
        with pytest.raises(ValueError, match="new_threshold must be less than deep_threshold"):
            rule.update_thresholds(new_threshold=15, deep_threshold=10)
        
        # Negative threshold
        with pytest.raises(ValueError, match="thresholds must be positive integers"):
            rule.update_thresholds(new_threshold=0)
    
    def test_get_conversation_stage(self):
        """Test getting conversation stage."""
        rule = ConversationContextRule(
            name="test_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="model1",
            developing_model="model2",
            deep_model="model3"
        )
        
        # New conversation
        request_data = {"messages": [{"role": "user", "content": "Hello"}]}
        assert rule.get_conversation_stage(request_data) == "new"
        
        # Developing conversation
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(5)]
        request_data = {"messages": messages}
        assert rule.get_conversation_stage(request_data) == "developing"
        
        # Deep conversation
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(12)]
        request_data = {"messages": messages}
        assert rule.get_conversation_stage(request_data) == "deep"
    
    def test_repr(self):
        """Test string representation."""
        rule = ConversationContextRule(
            name="test_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model="model1",
            developing_model="model2",
            deep_model="model3"
        )
        
        repr_str = repr(rule)
        assert "ConversationContextRule" in repr_str
        assert "name='test_rule'" in repr_str
        assert "new_threshold=3" in repr_str
        assert "deep_threshold=10" in repr_str
    
    def test_evaluate_with_rule_models(self):
        """Test evaluation when models are other rules."""
        from deimos_router.rules.task_rule import TaskRule
        
        # Create sub-rules to use as models
        sub_rule1 = TaskRule("sub_rule1", {"task1": "gpt-3.5-turbo"})
        sub_rule2 = TaskRule("sub_rule2", {"task2": "gpt-4"})
        sub_rule3 = TaskRule("sub_rule3", {"task3": "gpt-4-turbo"})
        
        rule = ConversationContextRule(
            name="context_rule",
            new_threshold=3,
            deep_threshold=10,
            new_model=sub_rule1,
            developing_model=sub_rule2,
            deep_model=sub_rule3
        )
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
                {"role": "user", "content": "How are you?"},
                {"role": "assistant", "content": "Good!"},
                {"role": "user", "content": "What can you do?"}
            ]
        }
        
        decision = rule.evaluate(request_data)
        assert decision.is_rule()
        assert decision.get_rule() == sub_rule2  # Should use developing_model
        assert "developing_conversation_5_messages" in decision.trigger
