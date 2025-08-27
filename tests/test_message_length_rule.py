"""Tests for MessageLengthRule."""

import pytest
from src.deimos_router.rules import MessageLengthRule, Decision


class TestMessageLengthRule:
    """Test cases for MessageLengthRule."""
    
    def test_init_valid_thresholds(self):
        """Test initialization with valid thresholds."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        assert rule.name == "test_rule"
        assert rule.short_threshold == 100
        assert rule.long_threshold == 500
        assert rule.short_model == "gpt-3.5-turbo"
        assert rule.medium_model == "gpt-4"
        assert rule.long_model == "gpt-4-turbo"
    
    def test_init_invalid_thresholds(self):
        """Test initialization with invalid thresholds."""
        # short_threshold >= long_threshold
        with pytest.raises(ValueError, match="short_threshold must be less than long_threshold"):
            MessageLengthRule(
                name="test_rule",
                short_threshold=500,
                long_threshold=100,
                short_model="gpt-3.5-turbo",
                medium_model="gpt-4",
                long_model="gpt-4-turbo"
            )
        
        # Equal thresholds
        with pytest.raises(ValueError, match="short_threshold must be less than long_threshold"):
            MessageLengthRule(
                name="test_rule",
                short_threshold=100,
                long_threshold=100,
                short_model="gpt-3.5-turbo",
                medium_model="gpt-4",
                long_model="gpt-4-turbo"
            )
        
        # Negative thresholds
        with pytest.raises(ValueError, match="thresholds must be non-negative"):
            MessageLengthRule(
                name="test_rule",
                short_threshold=-10,
                long_threshold=100,
                short_model="gpt-3.5-turbo",
                medium_model="gpt-4",
                long_model="gpt-4-turbo"
            )
    
    def test_evaluate_short_message(self):
        """Test evaluation of short messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello"}  # 5 characters
            ]
        }
        
        decision = rule.evaluate(request_data)
        
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "short_message_5_chars"
    
    def test_evaluate_medium_message(self):
        """Test evaluation of medium messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Create a message with exactly 200 characters
        content = "a" * 200
        request_data = {
            "messages": [
                {"role": "user", "content": content}
            ]
        }
        
        decision = rule.evaluate(request_data)
        
        assert decision.value == "gpt-4"
        assert decision.trigger == "medium_message_200_chars"
    
    def test_evaluate_long_message(self):
        """Test evaluation of long messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Create a message with exactly 1000 characters
        content = "a" * 1000
        request_data = {
            "messages": [
                {"role": "user", "content": content}
            ]
        }
        
        decision = rule.evaluate(request_data)
        
        assert decision.value == "gpt-4-turbo"
        assert decision.trigger == "long_message_1000_chars"
    
    def test_evaluate_boundary_conditions(self):
        """Test evaluation at threshold boundaries."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Test exactly at short_threshold (should be medium)
        request_data = {
            "messages": [
                {"role": "user", "content": "a" * 100}
            ]
        }
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-4"
        assert decision.trigger == "medium_message_100_chars"
        
        # Test exactly at long_threshold (should be long)
        request_data = {
            "messages": [
                {"role": "user", "content": "a" * 500}
            ]
        }
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-4-turbo"
        assert decision.trigger == "long_message_500_chars"
        
        # Test one character before short_threshold (should be short)
        request_data = {
            "messages": [
                {"role": "user", "content": "a" * 99}
            ]
        }
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "short_message_99_chars"
    
    def test_evaluate_multiple_user_messages(self):
        """Test evaluation with multiple user messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        request_data = {
            "messages": [
                {"role": "user", "content": "a" * 50},  # 50 chars
                {"role": "assistant", "content": "Response"},  # Should be ignored
                {"role": "user", "content": "b" * 60}   # 60 chars
            ]
        }
        
        decision = rule.evaluate(request_data)
        
        # Total user content: 50 + 60 = 110 characters (medium)
        assert decision.value == "gpt-4"
        assert decision.trigger == "medium_message_111_chars"  # 110 + 1 newline
    
    def test_evaluate_empty_messages(self):
        """Test evaluation with empty or no messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # No messages
        request_data = {"messages": []}
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "short_message_0_chars"
        
        # Empty content
        request_data = {
            "messages": [
                {"role": "user", "content": ""}
            ]
        }
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "short_message_0_chars"
    
    def test_evaluate_non_user_messages_ignored(self):
        """Test that non-user messages are ignored in length calculation."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        request_data = {
            "messages": [
                {"role": "system", "content": "a" * 1000},  # Should be ignored
                {"role": "assistant", "content": "b" * 1000},  # Should be ignored
                {"role": "user", "content": "Hello"}  # Only this counts (5 chars)
            ]
        }
        
        decision = rule.evaluate(request_data)
        
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "short_message_5_chars"
    
    def test_get_thresholds(self):
        """Test getting current thresholds."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        thresholds = rule.get_thresholds()
        
        assert thresholds == {
            'short_threshold': 100,
            'long_threshold': 500
        }
    
    def test_update_thresholds_valid(self):
        """Test updating thresholds with valid values."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Update both thresholds
        rule.update_thresholds(short_threshold=200, long_threshold=800)
        assert rule.short_threshold == 200
        assert rule.long_threshold == 800
        
        # Update only short threshold
        rule.update_thresholds(short_threshold=150)
        assert rule.short_threshold == 150
        assert rule.long_threshold == 800
        
        # Update only long threshold
        rule.update_thresholds(long_threshold=1000)
        assert rule.short_threshold == 150
        assert rule.long_threshold == 1000
    
    def test_update_thresholds_invalid(self):
        """Test updating thresholds with invalid values."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # short_threshold >= long_threshold
        with pytest.raises(ValueError, match="short_threshold must be less than long_threshold"):
            rule.update_thresholds(short_threshold=600, long_threshold=500)
        
        # Negative threshold
        with pytest.raises(ValueError, match="thresholds must be non-negative"):
            rule.update_thresholds(short_threshold=-10)
        
        # Original values should be unchanged after failed update
        assert rule.short_threshold == 100
        assert rule.long_threshold == 500
    
    def test_repr(self):
        """Test string representation."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        expected = "MessageLengthRule(name='test_rule', short_threshold=100, long_threshold=500)"
        assert repr(rule) == expected
    
    def test_evaluate_with_rule_objects(self):
        """Test evaluation when models are Rule objects instead of strings."""
        from src.deimos_router.rules import TaskRule
        
        # Create nested rules
        short_rule = TaskRule("short_tasks", {"quick": "gpt-3.5-turbo"})
        medium_rule = TaskRule("medium_tasks", {"analysis": "gpt-4"})
        long_rule = TaskRule("long_tasks", {"complex": "gpt-4-turbo"})
        
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model=short_rule,
            medium_model=medium_rule,
            long_model=long_rule
        )
        
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello"}  # 5 characters (short)
            ]
        }
        
        decision = rule.evaluate(request_data)
        
        assert decision.value == short_rule
        assert decision.trigger == "short_message_5_chars"
