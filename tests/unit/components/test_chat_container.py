"""Tests for chat container components."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from neural_terminal.components.chat_container import (
    MessageViewModel,
    ChatContainer,
    ChatHistory,
    display_message,
    display_chat_history,
)


class TestMessageViewModel:
    """Tests for MessageViewModel."""
    
    def test_create_basic(self):
        """Can create basic message view model."""
        msg = MessageViewModel(
            role="user",
            content="Hello",
        )
        
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is None
        assert msg.cost is None
    
    def test_create_full(self):
        """Can create full message view model."""
        msg = MessageViewModel(
            role="assistant",
            content="Hi there",
            timestamp=datetime.now(),
            cost=Decimal("0.0012"),
            tokens=150,
            latency_ms=500,
            is_streaming=False,
        )
        
        assert msg.role == "assistant"
        assert msg.tokens == 150
        assert msg.latency_ms == 500


class TestChatContainer:
    """Tests for ChatContainer."""
    
    def test_get_message_class_user(self):
        """Returns correct class for user."""
        container = ChatContainer()
        assert container._get_message_class("user") == "nt-message-user"
    
    def test_get_message_class_assistant(self):
        """Returns correct class for assistant."""
        container = ChatContainer()
        assert container._get_message_class("assistant") == "nt-message-assistant"
    
    def test_get_message_class_system(self):
        """Returns correct class for system."""
        container = ChatContainer()
        assert container._get_message_class("system") == "nt-message-system"
    
    def test_get_message_class_error(self):
        """Returns correct class for error."""
        container = ChatContainer()
        assert container._get_message_class("error") == "nt-message-error"
    
    def test_get_message_class_unknown(self):
        """Returns default class for unknown role."""
        container = ChatContainer()
        assert container._get_message_class("unknown") == "nt-message-assistant"
    
    def test_get_role_indicator_user(self):
        """Returns indicator for user."""
        container = ChatContainer()
        assert container._get_role_indicator("user") == ">>>"
    
    def test_get_role_indicator_assistant(self):
        """Returns indicator for assistant."""
        container = ChatContainer()
        assert container._get_role_indicator("assistant") == "█"
    
    def test_get_role_indicator_system(self):
        """Returns indicator for system."""
        container = ChatContainer()
        assert container._get_role_indicator("system") == "◆"
    
    def test_get_role_indicator_error(self):
        """Returns indicator for error."""
        container = ChatContainer()
        assert container._get_role_indicator("error") == "[ERROR]"
    
    def test_render_metadata_with_all_fields(self):
        """Renders metadata with all fields."""
        container = ChatContainer()
        msg = MessageViewModel(
            role="assistant",
            content="Hello",
            cost=Decimal("0.0012"),
            tokens=150,
            latency_ms=500,
        )
        
        html = container._render_metadata(msg)
        
        assert "nt-message-meta" in html
        assert "$0.0012" in html
        assert "150 tokens" in html
        assert "500ms" in html
    
    def test_render_metadata_empty(self):
        """Returns empty string when no metadata."""
        container = ChatContainer()
        msg = MessageViewModel(role="user", content="Hello")
        
        html = container._render_metadata(msg)
        
        assert html == ""
    
    @patch("neural_terminal.components.chat_container.st")
    def test_render_message(self, mock_st):
        """Renders message to streamlit."""
        container = ChatContainer()
        msg = MessageViewModel(role="user", content="Hello")
        
        container.render_message(msg)
        
        mock_st.markdown.assert_called_once()
        args, _ = mock_st.markdown.call_args
        assert "nt-message-user" in args[0]
        assert "Hello" in args[0]
    
    @patch("neural_terminal.components.chat_container.st")
    def test_render_message_error(self, mock_st):
        """Renders error message."""
        container = ChatContainer()
        msg = MessageViewModel(role="error", content="Error occurred")
        
        container.render_message(msg)
        
        args, _ = mock_st.markdown.call_args
        assert "nt-message-error" in args[0]
    
    @patch("neural_terminal.components.chat_container.st")
    def test_render_message_streaming(self, mock_st):
        """Renders streaming message with indicator."""
        container = ChatContainer()
        msg = MessageViewModel(
            role="assistant",
            content="Typing...",
            is_streaming=True,
        )
        
        container.render_message(msg)
        
        args, _ = mock_st.markdown.call_args
        assert "nt-streaming" in args[0]
    
    def test_start_streaming(self):
        """Start streaming initializes renderer."""
        container = ChatContainer()
        container.start_streaming()
        
        assert container._streaming_renderer is not None
    
    def test_append_stream_chunk(self):
        """Append adds chunks to stream."""
        container = ChatContainer()
        container.start_streaming()
        
        result = container.append_stream_chunk("Hello")
        result = container.append_stream_chunk(" World")
        
        assert "Hello World" in result
    
    def test_finalize_stream(self):
        """Finalize returns complete content."""
        container = ChatContainer()
        container.start_streaming()
        container.append_stream_chunk("Hello")
        
        result = container.finalize_stream()
        
        assert "Hello" in result
        assert container._streaming_renderer is None
    
    def test_finalize_stream_without_start(self):
        """Finalize without start returns empty."""
        container = ChatContainer()
        
        result = container.finalize_stream()
        
        assert result == ""


class TestChatHistory:
    """Tests for ChatHistory."""
    
    @patch("neural_terminal.components.chat_container.st")
    def test_display_messages(self, mock_st):
        """Displays list of messages."""
        mock_container = MagicMock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=False)
        
        history = ChatHistory()
        messages = [
            MessageViewModel(role="user", content="Hi"),
            MessageViewModel(role="assistant", content="Hello"),
        ]
        
        history.display(messages)
        
        # Should render both messages
        assert mock_st.markdown.call_count >= 2
    
    @patch("neural_terminal.components.chat_container.st")
    def test_display_limits_messages(self, mock_st):
        """Limits displayed messages for performance."""
        mock_container = MagicMock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=False)
        
        history = ChatHistory(max_visible=5)
        messages = [MessageViewModel(role="user", content=f"Msg {i}") for i in range(10)]
        
        history.display(messages)
        
        # Should show truncation notice
        mock_st.caption.assert_called()
    
    @patch("neural_terminal.components.chat_container.st")
    def test_display_with_loading(self, mock_st):
        """Shows loading indicator."""
        mock_container = MagicMock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=False)
        
        history = ChatHistory()
        messages = []
        
        history.display(messages, show_loading=True)
        
        # Should render loading
        assert mock_st.markdown.call_count >= 1


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @patch("neural_terminal.components.chat_container.st")
    def test_display_message(self, mock_st):
        """display_message renders message."""
        display_message("Hello", role="user")
        
        mock_st.markdown.assert_called_once()
    
    @patch("neural_terminal.components.chat_container.st")
    def test_display_chat_history(self, mock_st):
        """display_chat_history renders history."""
        mock_container = MagicMock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=False)
        
        messages = [
            MessageViewModel(role="user", content="Hi"),
        ]
        
        display_chat_history(messages)
        
        assert mock_st.markdown.called
