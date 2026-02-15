"""Unit tests for session state management.

Tests for Phase 3: StateManager with Streamlit session state.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from datetime import datetime

from neural_terminal.application.state import AppState, StateManager
from neural_terminal.domain.models import Conversation, ConversationStatus


class MockSessionState(dict):
    """Mock Streamlit session state."""
    pass


@pytest.fixture
def mock_st_session_state(monkeypatch):
    """Mock Streamlit's session state."""
    mock_state = MockSessionState()
    
    # Mock streamlit module
    import streamlit as st
    monkeypatch.setattr(st, "session_state", mock_state)
    
    return mock_state


class TestAppState:
    """Tests for AppState dataclass."""

    def test_default_values(self):
        """Test default AppState values."""
        state = AppState()
        
        assert state.current_conversation_id is None
        assert state.accumulated_cost == "0.00"
        assert state.selected_model == "openai/gpt-3.5-turbo"
        assert state.stream_buffer == ""
        assert state.is_streaming is False
        assert state.error_message is None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = AppState(
            current_conversation_id="test-id",
            accumulated_cost="1.50",
            is_streaming=True
        )
        
        data = state.to_dict()
        
        assert data["current_conversation_id"] == "test-id"
        assert data["accumulated_cost"] == "1.50"
        assert data["is_streaming"] is True
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "current_conversation_id": "test-id",
            "accumulated_cost": "2.00",
            "selected_model": "gpt-4",
            "stream_buffer": "Hello",
            "is_streaming": False,
            "error_message": None
        }
        
        state = AppState.from_dict(data)
        
        assert state.current_conversation_id == "test-id"
        assert state.accumulated_cost == "2.00"
        assert state.selected_model == "gpt-4"


class TestStateManager:
    """Tests for StateManager."""

    def test_initialization_creates_state(self, mock_st_session_state):
        """Test that initialization creates session state."""
        manager = StateManager()
        
        assert "neural_terminal_initialized" in mock_st_session_state
        assert "neural_terminal_state" in mock_st_session_state
        assert "neural_terminal_conversation_cache" in mock_st_session_state
    
    def test_initialization_is_idempotent(self, mock_st_session_state):
        """Test that multiple initializations don't reset state."""
        manager1 = StateManager()
        manager1.update(accumulated_cost="5.00")
        
        manager2 = StateManager()
        
        assert manager2.state.accumulated_cost == "5.00"
    
    def test_state_property_returns_app_state(self, mock_st_session_state):
        """Test state property returns AppState."""
        manager = StateManager()
        
        state = manager.state
        
        assert isinstance(state, AppState)
    
    def test_update_modifies_state(self, mock_st_session_state):
        """Test update modifies state atomically."""
        manager = StateManager()
        
        manager.update(accumulated_cost="10.00", is_streaming=True)
        
        assert manager.state.accumulated_cost == "10.00"
        assert manager.state.is_streaming is True
        # Other fields unchanged
        assert manager.state.selected_model == "openai/gpt-3.5-turbo"
    
    def test_set_conversation_caches_and_sets_current(self, mock_st_session_state):
        """Test set_conversation caches conversation and sets current."""
        manager = StateManager()
        
        conv = Conversation(
            id=uuid4(),
            title="Test Conversation",
            model_id="gpt-4",
            total_cost=Decimal("1.50"),
            total_tokens=100
        )
        
        manager.set_conversation(conv)
        
        # Should set current conversation ID
        assert manager.state.current_conversation_id == str(conv.id)
        
        # Should cache the conversation
        cached = manager.get_cached_conversation(str(conv.id))
        assert cached is not None
        assert cached.title == "Test Conversation"
        assert cached.model_id == "gpt-4"
    
    def test_get_cached_conversation_returns_none_if_not_found(self, mock_st_session_state):
        """Test get_cached_conversation returns None for unknown ID."""
        manager = StateManager()
        
        cached = manager.get_cached_conversation("non-existent-id")
        
        assert cached is None
    
    def test_conversation_serialization_roundtrip(self, mock_st_session_state):
        """Test conversation can be serialized and deserialized."""
        manager = StateManager()
        
        conv = Conversation(
            id=uuid4(),
            title="Test",
            total_cost=Decimal("5.50"),
            tags=["test", "demo"]
        )
        
        manager.set_conversation(conv)
        cached = manager.get_cached_conversation(str(conv.id))
        
        # After serialization roundtrip, ID and Decimal become strings
        assert str(cached.id) == str(conv.id)
        assert str(cached.total_cost) == "5.50"
        assert cached.tags == ["test", "demo"]
    
    def test_clear_stream_buffer(self, mock_st_session_state):
        """Test clear_stream_buffer clears buffer and resets flag."""
        manager = StateManager()
        manager.update(stream_buffer="Hello world", is_streaming=True)
        
        manager.clear_stream_buffer()
        
        assert manager.state.stream_buffer == ""
        assert manager.state.is_streaming is False
    
    def test_append_stream_buffer(self, mock_st_session_state):
        """Test append_stream_buffer appends text and sets flag."""
        manager = StateManager()
        manager.update(stream_buffer="Hello")
        
        manager.append_stream_buffer(" world")
        
        assert manager.state.stream_buffer == "Hello world"
        assert manager.state.is_streaming is True
    
    def test_set_error(self, mock_st_session_state):
        """Test set_error sets message and stops streaming."""
        manager = StateManager()
        manager.update(is_streaming=True)
        
        manager.set_error("Something went wrong")
        
        assert manager.state.error_message == "Something went wrong"
        assert manager.state.is_streaming is False
    
    def test_clear_error(self, mock_st_session_state):
        """Test clear_error removes error message."""
        manager = StateManager()
        manager.set_error("Error")
        
        manager.clear_error()
        
        assert manager.state.error_message is None
