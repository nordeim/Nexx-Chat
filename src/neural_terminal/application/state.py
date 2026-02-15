"""Session state management for Streamlit.

Provides type-safe abstraction over st.session_state with namespace
isolation to prevent key collisions.
"""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

import streamlit as st

from neural_terminal.domain.models import Conversation


@dataclass
class AppState:
    """Immutable application state container.
    
    Attributes:
        current_conversation_id: Active conversation ID (as string for JSON serialization)
        accumulated_cost: Accumulated cost as string (Decimal doesn't JSON serialize)
        selected_model: Currently selected model ID
        stream_buffer: Partial SSE data buffer
        is_streaming: Whether currently streaming
        error_message: Current error message if any
    """
    current_conversation_id: Optional[str] = None
    accumulated_cost: str = "0.00"
    selected_model: str = "openai/gpt-3.5-turbo"
    stream_buffer: str = ""
    is_streaming: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for session storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppState":
        """Create from dictionary."""
        return cls(**data)


class StateManager:
    """Type-safe wrapper around Streamlit's session state.
    
    Provides:
    - Namespace isolation (prevents key collisions)
    - Atomic updates
    - Conversation caching with proper serialization
    
    Phase 0 Defect H-3 Note:
        This manages synchronous state only. For async operations,
        use the StreamlitStreamBridge which handles the async-to-sync bridge.
    """
    
    _NAMESPACE = "neural_terminal_"
    
    def __init__(self):
        """Initialize state manager with namespace."""
        self._ensure_initialized()
    
    def _ensure_initialized(self) -> None:
        """Idempotent initialization of session state."""
        init_key = f"{self._NAMESPACE}initialized"
        if init_key not in st.session_state:
            st.session_state[init_key] = True
            st.session_state[f"{self._NAMESPACE}state"] = AppState().to_dict()
            st.session_state[f"{self._NAMESPACE}conversation_cache"] = {}
    
    @property
    def state(self) -> AppState:
        """Get current application state.
        
        Returns:
            AppState instance
        """
        raw = st.session_state.get(f"{self._NAMESPACE}state", {})
        return AppState.from_dict(raw)
    
    def update(self, **kwargs) -> None:
        """Atomic state update.
        
        Args:
            **kwargs: Key-value pairs to update
        """
        current = self.state
        new_state = AppState(**{**current.to_dict(), **kwargs})
        st.session_state[f"{self._NAMESPACE}state"] = new_state.to_dict()
    
    def set_conversation(self, conversation: Conversation) -> None:
        """Cache conversation in session state.
        
        Phase 0 Defect H-4 Fix:
            Uses conversation.to_dict() for proper serialization.
        
        Args:
            conversation: Conversation to cache
        """
        cache_key = f"{self._NAMESPACE}conversation_cache"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = {}
        
        # Serialize conversation properly
        conv_data = conversation.to_dict()
        st.session_state[cache_key][str(conversation.id)] = conv_data
        
        # Update current conversation ID
        self.update(current_conversation_id=str(conversation.id))
    
    def get_cached_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve conversation from cache.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation or None if not cached
        """
        cache_key = f"{self._NAMESPACE}conversation_cache"
        cache = st.session_state.get(cache_key, {})
        data = cache.get(conversation_id)
        
        if data:
            return Conversation(**data)
        return None
    
    def clear_stream_buffer(self) -> None:
        """Clear streaming buffer and reset streaming flag."""
        self.update(stream_buffer="", is_streaming=False)
    
    def append_stream_buffer(self, text: str) -> None:
        """Append text to streaming buffer.
        
        Args:
            text: Text to append
        """
        current = self.state.stream_buffer
        self.update(stream_buffer=current + text, is_streaming=True)
    
    def set_error(self, message: str) -> None:
        """Set error message.
        
        Args:
            message: Error message
        """
        self.update(error_message=message, is_streaming=False)
    
    def clear_error(self) -> None:
        """Clear error message."""
        self.update(error_message=None)
