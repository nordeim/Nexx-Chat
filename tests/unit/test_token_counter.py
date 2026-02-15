"""Unit tests for token counter.

Tests for Phase 2: Token counting with tiktoken.
"""
import pytest

from neural_terminal.domain.models import Message, MessageRole
from neural_terminal.infrastructure.token_counter import TokenCounter


class TestTokenCounter:
    """Tests for TokenCounter."""

    def test_count_tokens_hello_world(self):
        """Test token counting for simple text."""
        counter = TokenCounter()
        
        # "Hello world" is typically 2 tokens with cl100k_base
        tokens = counter.count_tokens("Hello world", "gpt-3.5-turbo")
        
        assert tokens == 2
    
    def test_count_tokens_empty_string(self):
        """Test token counting for empty string."""
        counter = TokenCounter()
        
        tokens = counter.count_tokens("", "gpt-3.5-turbo")
        
        assert tokens == 0
    
    def test_count_message_with_role(self):
        """Test token counting for a message."""
        counter = TokenCounter()
        
        msg = Message(role=MessageRole.USER, content="Hello")
        tokens = counter.count_message(msg, "gpt-3.5-turbo")
        
        # Should be: 4 (overhead) + len("user") + len("Hello")
        # "user" is 1 token, "Hello" is 1 token
        assert tokens == 6  # 4 + 1 + 1
    
    def test_count_messages_total(self):
        """Test token counting for multiple messages."""
        counter = TokenCounter()
        
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there"),
            Message(role=MessageRole.USER, content="How are you?"),
        ]
        
        total = counter.count_messages(messages, "gpt-3.5-turbo")
        
        # Should sum individual counts + 2 (reply primer)
        individual = sum(counter.count_message(m, "gpt-3.5-turbo") for m in messages)
        assert total == individual + 2
    
    def test_encoder_caching(self):
        """Test that encoders are cached."""
        counter = TokenCounter()
        
        # First call creates encoder
        encoder1 = counter._get_encoder("gpt-3.5-turbo")
        
        # Second call returns cached
        encoder2 = counter._get_encoder("gpt-3.5-turbo")
        
        assert encoder1 is encoder2
    
    def test_different_models_same_encoding(self):
        """Test that different OpenAI models use same encoding."""
        counter = TokenCounter()
        
        # Both should use cl100k_base
        encoder_gpt35 = counter._get_encoder("openai/gpt-3.5-turbo")
        encoder_gpt4 = counter._get_encoder("openai/gpt-4")
        
        assert encoder_gpt35 is encoder_gpt4
    
    def test_truncate_context_no_truncation_needed(self):
        """Test truncate when no truncation needed."""
        counter = TokenCounter()
        
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
        ]
        
        result = counter.truncate_context(
            messages,
            "gpt-3.5-turbo",
            max_tokens=1000,
            reserve_tokens=500
        )
        
        assert len(result) == 1
        assert result[0].content == "Hello"
    
    def test_truncate_context_keeps_system_message(self):
        """Test that system message is preserved during truncation."""
        counter = TokenCounter()
        
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful"),
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.USER, content="World"),
            Message(role=MessageRole.USER, content="Test"),
        ]
        
        # Truncate with very small limit to force truncation
        result = counter.truncate_context(
            messages,
            "gpt-3.5-turbo",
            max_tokens=20,  # Very small
            reserve_tokens=0
        )
        
        # System message should be preserved
        assert result[0].role == MessageRole.SYSTEM
        assert result[0].content == "You are helpful"
    
    def test_truncate_context_adds_marker(self):
        """Test that truncation adds marker message."""
        counter = TokenCounter()
        
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.USER, content="World"),
            Message(role=MessageRole.USER, content="Test message"),
            Message(role=MessageRole.USER, content="Another message"),
        ]
        
        # Truncate with small limit
        result = counter.truncate_context(
            messages,
            "gpt-3.5-turbo",
            max_tokens=15,  # Small limit
            reserve_tokens=0
        )
        
        # Should have fewer messages and include marker
        assert len(result) < len(messages)
        
        # Check for truncation marker
        marker_contents = [m.content for m in result if "truncated" in m.content]
        assert len(marker_contents) > 0
    
    def test_truncate_context_empty_list(self):
        """Test truncate with empty list."""
        counter = TokenCounter()
        
        result = counter.truncate_context(
            [],
            "gpt-3.5-turbo",
            max_tokens=1000
        )
        
        assert result == []
    
    def test_count_consistency(self):
        """Test that counting is consistent."""
        counter = TokenCounter()
        
        text = "This is a test message for consistency checking."
        
        count1 = counter.count_tokens(text, "gpt-3.5-turbo")
        count2 = counter.count_tokens(text, "gpt-3.5-turbo")
        count3 = counter.count_tokens(text, "gpt-4")
        
        assert count1 == count2 == count3
