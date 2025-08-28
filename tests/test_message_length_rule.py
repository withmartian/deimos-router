"""Tests for MessageLengthRule."""

import pytest
import tiktoken
from src.deimos_router.rules import MessageLengthRule, Decision


class TestMessageLengthRule:
    """Test cases for MessageLengthRule."""
    
    @staticmethod
    def _count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
        """Helper function to count tokens for testing."""
        if not text:
            return 0
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    
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
        
        content = "Hello"
        request_data = {
            "messages": [
                {"role": "user", "content": content}
            ]
        }
        
        decision = rule.evaluate(request_data)
        expected_tokens = self._count_tokens(content)
        
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == f"short_message_{expected_tokens}_tokens"
    
    def test_evaluate_medium_message(self):
        """Test evaluation of medium messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=30,  # Lower threshold for testing
            long_threshold=100,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Create a message that will result in medium token count
        content = "This is a medium length message that should have enough tokens to be classified as medium length. " * 2
        request_data = {
            "messages": [
                {"role": "user", "content": content}
            ]
        }
        
        decision = rule.evaluate(request_data)
        expected_tokens = self._count_tokens(content)
        
        assert decision.value == "gpt-4"
        assert decision.trigger == f"medium_message_{expected_tokens}_tokens"
        assert 30 <= expected_tokens < 100  # Verify it's actually in medium range
    
    def test_evaluate_long_message(self):
        """Test evaluation of long messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=30,
            long_threshold=100,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Create a message that will result in long token count
        content = "This is a very long message that should have many tokens to be classified as a long message. " * 10
        request_data = {
            "messages": [
                {"role": "user", "content": content}
            ]
        }
        
        decision = rule.evaluate(request_data)
        expected_tokens = self._count_tokens(content)
        
        assert decision.value == "gpt-4-turbo"
        assert decision.trigger == f"long_message_{expected_tokens}_tokens"
        assert expected_tokens >= 100  # Verify it's actually in long range
    
    def test_evaluate_boundary_conditions(self):
        """Test evaluation at threshold boundaries."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=10,  # Use smaller thresholds for predictable testing
            long_threshold=20,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Test exactly at short_threshold (should be medium)
        # Create content that results in exactly 10 tokens
        content_10_tokens = "word " * 10  # Should be around 10 tokens
        actual_tokens = self._count_tokens(content_10_tokens)
        
        # Adjust content to get exactly the threshold we want
        if actual_tokens < 10:
            content_10_tokens += "extra words to reach threshold"
        elif actual_tokens > 10:
            content_10_tokens = "word " * 8  # Try fewer words
        
        actual_tokens = self._count_tokens(content_10_tokens)
        
        request_data = {
            "messages": [
                {"role": "user", "content": content_10_tokens}
            ]
        }
        decision = rule.evaluate(request_data)
        
        if actual_tokens >= 10:
            assert decision.value in ["gpt-4", "gpt-4-turbo"]  # Medium or long
        else:
            assert decision.value == "gpt-3.5-turbo"  # Short
        
        assert decision.trigger == f"{'short' if actual_tokens < 10 else ('medium' if actual_tokens < 20 else 'long')}_message_{actual_tokens}_tokens"
    
    def test_evaluate_multiple_user_messages(self):
        """Test evaluation with multiple user messages."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=10,
            long_threshold=50,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        content1 = "First message"
        content2 = "Second message"
        request_data = {
            "messages": [
                {"role": "user", "content": content1},
                {"role": "assistant", "content": "Response"},  # Should be ignored
                {"role": "user", "content": content2}
            ]
        }
        
        decision = rule.evaluate(request_data)
        
        # Calculate expected tokens for combined user content
        combined_content = content1 + "\n" + content2
        expected_tokens = self._count_tokens(combined_content)
        
        assert decision.trigger == f"{'short' if expected_tokens < 10 else ('medium' if expected_tokens < 50 else 'long')}_message_{expected_tokens}_tokens"
    
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
        assert decision.trigger == "short_message_0_tokens"
        
        # Empty content
        request_data = {
            "messages": [
                {"role": "user", "content": ""}
            ]
        }
        decision = rule.evaluate(request_data)
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == "short_message_0_tokens"
    
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
        
        content = "Hello"
        request_data = {
            "messages": [
                {"role": "system", "content": "a" * 1000},  # Should be ignored
                {"role": "assistant", "content": "b" * 1000},  # Should be ignored
                {"role": "user", "content": content}  # Only this counts
            ]
        }
        
        decision = rule.evaluate(request_data)
        expected_tokens = self._count_tokens(content)
        
        assert decision.value == "gpt-3.5-turbo"
        assert decision.trigger == f"short_message_{expected_tokens}_tokens"
    
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
        
        content = "Hello"
        request_data = {
            "messages": [
                {"role": "user", "content": content}
            ]
        }
        
        decision = rule.evaluate(request_data)
        expected_tokens = self._count_tokens(content)
        
        assert decision.value == short_rule
        assert decision.trigger == f"short_message_{expected_tokens}_tokens"
    
    def test_init_with_custom_encoding(self):
        """Test initialization with custom encoding."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo",
            encoding_name="p50k_base"  # Different encoding
        )
        
        assert rule.encoding_name == "p50k_base"
        
        # Test with invalid encoding
        with pytest.raises(ValueError, match="Unknown encoding"):
            MessageLengthRule(
                name="test_rule",
                short_threshold=100,
                long_threshold=500,
                short_model="gpt-3.5-turbo",
                medium_model="gpt-4",
                long_model="gpt-4-turbo",
                encoding_name="invalid_encoding"
            )
    
    def test_count_tokens_method(self):
        """Test the _count_tokens method directly."""
        rule = MessageLengthRule(
            name="test_rule",
            short_threshold=100,
            long_threshold=500,
            short_model="gpt-3.5-turbo",
            medium_model="gpt-4",
            long_model="gpt-4-turbo"
        )
        
        # Test empty string
        assert rule._count_tokens("") == 0
        
        # Test simple text
        tokens = rule._count_tokens("Hello world")
        assert tokens > 0
        assert isinstance(tokens, int)
        
        # Test that longer text has more tokens
        short_text = "Hello"
        long_text = "Hello world this is a much longer text with many more words"
        assert rule._count_tokens(long_text) > rule._count_tokens(short_text)
