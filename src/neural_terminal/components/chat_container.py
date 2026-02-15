"""Chat container component for message display.

Provides scrollable message containers and message rendering
with proper terminal aesthetic styling.
"""

from typing import List, Optional, Callable, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

import streamlit as st

from .message_renderer import MessageRenderer, StreamingMessageRenderer


@dataclass
class MessageViewModel:
    """View model for message display."""
    role: str  # 'user', 'assistant', 'system', 'error'
    content: str
    timestamp: Optional[datetime] = None
    cost: Optional[Decimal] = None
    tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    is_streaming: bool = False


class ChatContainer:
    """Chat message container with terminal styling."""
    
    def __init__(self, renderer: Optional[MessageRenderer] = None):
        """Initialize chat container.
        
        Args:
            renderer: Message renderer instance
        """
        self._renderer = renderer or MessageRenderer()
        self._streaming_renderer: Optional[StreamingMessageRenderer] = None
    
    def _get_message_class(self, role: str) -> str:
        """Get CSS class for message role.
        
        Args:
            role: Message role
            
        Returns:
            CSS class name
        """
        role_classes = {
            'user': 'nt-message-user',
            'assistant': 'nt-message-assistant',
            'system': 'nt-message-system',
            'error': 'nt-message-error',
        }
        return role_classes.get(role, 'nt-message-assistant')
    
    def _get_role_indicator(self, role: str) -> str:
        """Get indicator prefix for role.
        
        Args:
            role: Message role
            
        Returns:
            Indicator string
        """
        indicators = {
            'user': '>>>',
            'assistant': '█',
            'system': '◆',
            'error': '[ERROR]',
        }
        return indicators.get(role, '█')
    
    def _render_metadata(self, message: MessageViewModel) -> str:
        """Render message metadata HTML.
        
        Args:
            message: Message view model
            
        Returns:
            Metadata HTML
        """
        parts = []
        
        if message.cost is not None:
            parts.append(f'<span class="nt-meta-cost">${float(message.cost):.4f}</span>')
        
        if message.tokens is not None:
            parts.append(f'<span class="nt-meta-tokens">{message.tokens} tokens</span>')
        
        if message.latency_ms is not None:
            parts.append(f'<span class="nt-meta-latency">{message.latency_ms}ms</span>')
        
        if not parts:
            return ""
        
        return f'<div class="nt-message-meta">{" | ".join(parts)}</div>'
    
    def render_message(
        self,
        message: MessageViewModel,
        container: Optional[Any] = None,
    ) -> None:
        """Render a single message.
        
        Args:
            message: Message to render
            container: Optional streamlit container to render in
        """
        target = container or st
        
        # Determine message styling
        msg_class = self._get_message_class(message.role)
        indicator = self._get_role_indicator(message.role)
        
        # Render content
        if message.role == 'error':
            content_html = self._renderer.render_error(message.content)
        elif message.role == 'system':
            content_html = self._renderer.render_system_message(message.content)
        else:
            content_html = self._renderer.render(message.content)
        
        # Build message HTML
        if message.is_streaming:
            streaming_indicator = '<span class="nt-streaming"></span>'
            content_html = content_html + streaming_indicator
        
        metadata_html = self._render_metadata(message)
        
        html = f'''
        <div class="nt-message-container">
            <div class="nt-message {msg_class}">
                {content_html}
                {metadata_html}
            </div>
        </div>
        '''
        
        target.markdown(html, unsafe_allow_html=True)
    
    def render_messages(
        self,
        messages: List[MessageViewModel],
        container: Optional[Any] = None,
    ) -> None:
        """Render multiple messages.
        
        Args:
            messages: List of messages to render
            container: Optional streamlit container
        """
        target = container or st
        
        with target.container():
            for message in messages:
                self.render_message(message)
    
    def start_streaming(self) -> None:
        """Start streaming mode."""
        self._streaming_renderer = StreamingMessageRenderer()
        self._streaming_renderer.clear()
    
    def append_stream_chunk(self, chunk: str) -> str:
        """Append chunk to streaming message.
        
        Args:
            chunk: Text chunk to append
            
        Returns:
            Current rendered content
        """
        if self._streaming_renderer is None:
            self.start_streaming()
        
        return self._streaming_renderer.append(chunk)  # type: ignore
    
    def finalize_stream(self) -> str:
        """Finalize streaming message.
        
        Returns:
            Final rendered content
        """
        if self._streaming_renderer is None:
            return ""
        
        result = self._streaming_renderer.finalize()
        self._streaming_renderer = None
        return result
    
    def render_streaming_message(
        self,
        content: str,
        container: Optional[Any] = None,
    ) -> None:
        """Render a streaming message with cursor.
        
        Args:
            content: Current content
            container: Optional streamlit container
        """
        target = container or st
        
        msg_class = self._get_message_class('assistant')
        
        html = f'''
        <div class="nt-message-container">
            <div class="nt-message {msg_class}">
                {content}<span class="nt-streaming"></span>
            </div>
        </div>
        '''
        
        target.markdown(html, unsafe_allow_html=True)


class ChatHistory:
    """Manages chat history display with virtualization support."""
    
    def __init__(
        self,
        container: Optional[Any] = None,
        max_visible: int = 100,
    ):
        """Initialize chat history.
        
        Args:
            container: Streamlit container
            max_visible: Maximum messages to display
        """
        self._container = container or st
        self._max_visible = max_visible
        self._chat_container = ChatContainer()
    
    def display(
        self,
        messages: List[MessageViewModel],
        show_loading: bool = False,
    ) -> None:
        """Display message history.
        
        Args:
            messages: Messages to display
            show_loading: Show loading indicator
        """
        # Limit visible messages for performance
        visible = messages[-self._max_visible:] if len(messages) > self._max_visible else messages
        
        # Show truncation notice
        if len(messages) > self._max_visible:
            st.caption(f"Showing last {self._max_visible} of {len(messages)} messages")
        
        # Render messages
        self._chat_container.render_messages(visible, self._container)
        
        # Show loading indicator
        if show_loading:
            self._render_loading()
    
    def _render_loading(self) -> None:
        """Render loading indicator."""
        html = '''
        <div class="nt-message-container">
            <div class="nt-message nt-message-assistant">
                <span class="nt-streaming">Thinking...</span>
            </div>
        </div>
        '''
        self._container.markdown(html, unsafe_allow_html=True)
    
    def scroll_to_bottom(self) -> None:
        """Auto-scroll to bottom of chat."""
        # Streamlit handles scrolling automatically
        # This is a placeholder for future scroll control
        pass


# Convenience functions
def display_message(
    content: str,
    role: str = 'assistant',
    **kwargs,
) -> None:
    """Display a single message.
    
    Args:
        content: Message content
        role: Message role
        **kwargs: Additional message attributes
    """
    container = ChatContainer()
    message = MessageViewModel(role=role, content=content, **kwargs)
    container.render_message(message)


def display_chat_history(
    messages: List[MessageViewModel],
    container: Optional[Any] = None,
) -> None:
    """Display chat history.
    
    Args:
        messages: List of messages
        container: Optional streamlit container
    """
    chat = ChatHistory(container)
    chat.display(messages)
