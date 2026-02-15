"""Unit tests for repository pattern.

Tests for Phase 0 Defect C-3: Repository session leak fix.
Tests for Phase 0 Defect H-5: Missing get_messages method.
"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from neural_terminal.domain.models import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
    TokenUsage,
)
from neural_terminal.infrastructure.repositories import SQLiteConversationRepository


class TestSQLiteConversationRepository:
    """Tests for SQLite conversation repository."""

    def test_save_and_get_by_id(self):
        """Test saving a conversation and retrieving it by ID."""
        repo = SQLiteConversationRepository()
        
        # Create conversation
        conv = Conversation(
            id=uuid4(),
            title="Test Conversation",
            model_id="openai/gpt-3.5-turbo",
            status=ConversationStatus.ACTIVE,
            total_cost=Decimal("0.05"),
            total_tokens=100,
            tags=["test", "demo"],
        )
        
        # Save
        repo.save(conv)
        
        # Retrieve
        retrieved = repo.get_by_id(conv.id)
        
        assert retrieved is not None
        assert retrieved.id == conv.id
        assert retrieved.title == "Test Conversation"
        assert retrieved.model_id == "openai/gpt-3.5-turbo"
        assert retrieved.total_cost == Decimal("0.05")
        assert retrieved.total_tokens == 100
        assert retrieved.tags == ["test", "demo"]
    
    def test_get_by_id_not_found(self):
        """Test retrieving non-existent conversation returns None."""
        repo = SQLiteConversationRepository()
        
        retrieved = repo.get_by_id(uuid4())
        
        assert retrieved is None
    
    def test_add_message_and_get_messages(self):
        """Test adding messages and retrieving them.
        
        Phase 0 Defect H-5 Fix:
            get_messages() method must be implemented for orchestrator.
        """
        repo = SQLiteConversationRepository()
        
        # Create conversation
        conv_id = uuid4()
        conv = Conversation(
            id=conv_id,
            title="Test Conversation",
            model_id="openai/gpt-3.5-turbo",
        )
        repo.save(conv)
        
        # Add messages
        msg1 = Message(
            id=uuid4(),
            conversation_id=conv_id,
            role=MessageRole.USER,
            content="Hello",
            created_at=datetime.utcnow(),
        )
        msg2 = Message(
            id=uuid4(),
            conversation_id=conv_id,
            role=MessageRole.ASSISTANT,
            content="Hi there",
            token_usage=TokenUsage(10, 20, 30),
            cost=Decimal("0.001"),
            latency_ms=500,
            model_id="openai/gpt-3.5-turbo",
            created_at=datetime.utcnow(),
        )
        
        repo.add_message(msg1)
        repo.add_message(msg2)
        
        # Retrieve messages - THIS IS THE KEY TEST for H-5
        messages = repo.get_messages(conv_id)
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Hi there"
        assert messages[1].token_usage.prompt_tokens == 10
        assert messages[1].cost == Decimal("0.001")
    
    def test_get_messages_ordered_by_created_at(self):
        """Test that messages are returned in chronological order."""
        repo = SQLiteConversationRepository()
        
        # Create conversation
        conv_id = uuid4()
        conv = Conversation(
            id=conv_id,
            title="Test Conversation",
            model_id="openai/gpt-3.5-turbo",
        )
        repo.save(conv)
        
        # Add messages with different timestamps
        from datetime import timedelta
        base_time = datetime.utcnow()
        
        msg1 = Message(
            id=uuid4(),
            conversation_id=conv_id,
            role=MessageRole.USER,
            content="First",
            created_at=base_time + timedelta(seconds=2),
        )
        msg2 = Message(
            id=uuid4(),
            conversation_id=conv_id,
            role=MessageRole.USER,
            content="Second",
            created_at=base_time + timedelta(seconds=1),
        )
        msg3 = Message(
            id=uuid4(),
            conversation_id=conv_id,
            role=MessageRole.USER,
            content="Third",
            created_at=base_time + timedelta(seconds=3),
        )
        
        repo.add_message(msg2)  # Second (1s)
        repo.add_message(msg1)  # First (2s)
        repo.add_message(msg3)  # Third (3s)
        
        # Retrieve messages - should be ordered by created_at ascending
        messages = repo.get_messages(conv_id)
        
        assert len(messages) == 3
        assert messages[0].content == "Second"  # 1s
        assert messages[1].content == "First"   # 2s
        assert messages[2].content == "Third"   # 3s
    
    def test_get_messages_empty_conversation(self):
        """Test retrieving messages from conversation with no messages."""
        repo = SQLiteConversationRepository()
        
        # Create conversation without messages
        conv_id = uuid4()
        conv = Conversation(
            id=conv_id,
            title="Empty Conversation",
            model_id="openai/gpt-3.5-turbo",
        )
        repo.save(conv)
        
        messages = repo.get_messages(conv_id)
        
        assert messages == []
    
    def test_list_active_returns_active_conversations(self):
        """Test listing active conversations returns only active."""
        repo = SQLiteConversationRepository()
        
        # Create active conversations
        for i in range(3):
            conv = Conversation(
                id=uuid4(),
                title=f"Active Conv {i}",
                model_id="openai/gpt-3.5-turbo",
                status=ConversationStatus.ACTIVE,
            )
            repo.save(conv)
        
        # List active
        active = repo.list_active(limit=10)
        
        # Should have at least 3 (might have more from other tests)
        active_titles = [c.title for c in active]
        assert "Active Conv 0" in active_titles
        assert "Active Conv 1" in active_titles
        assert "Active Conv 2" in active_titles
        
        # Should be ordered by updated_at descending (newest first)
        # Active Conv 2 should come before Active Conv 0
        idx0 = active_titles.index("Active Conv 0")
        idx2 = active_titles.index("Active Conv 2")
        assert idx2 < idx0  # Conv 2 comes first (more recent)
    
    def test_list_active_respects_limit(self):
        """Test that list_active respects the limit parameter."""
        repo = SQLiteConversationRepository()
        
        # Get current count
        initial_count = len(repo.list_active(limit=100))
        
        # Create 10 conversations
        for i in range(10):
            conv = Conversation(
                id=uuid4(),
                title=f"LimitTest Conv {i}",
                model_id="openai/gpt-3.5-turbo",
            )
            repo.save(conv)
        
        # List with limit 5
        active = repo.list_active(limit=5)
        
        # Should return exactly 5, regardless of total count
        assert len(active) == 5
    
    def test_add_message_without_conversation_id_raises(self):
        """Test that adding a message without conversation_id raises ValueError."""
        repo = SQLiteConversationRepository()
        
        msg = Message(
            id=uuid4(),
            conversation_id=None,  # Missing!
            role=MessageRole.USER,
            content="Orphan message",
        )
        
        with pytest.raises(ValueError, match="must belong to a conversation"):
            repo.add_message(msg)
    
    def test_message_without_token_usage_handles_none(self):
        """Test that messages without token usage are handled gracefully."""
        repo = SQLiteConversationRepository()
        
        # Create conversation
        conv_id = uuid4()
        conv = Conversation(
            id=conv_id,
            title="Test Conversation",
            model_id="openai/gpt-3.5-turbo",
        )
        repo.save(conv)
        
        # Add message without token usage
        msg = Message(
            id=uuid4(),
            conversation_id=conv_id,
            role=MessageRole.USER,
            content="No tokens",
            token_usage=None,
            cost=None,
        )
        repo.add_message(msg)
        
        # Retrieve and verify
        messages = repo.get_messages(conv_id)
        assert len(messages) == 1
        assert messages[0].token_usage is None
        assert messages[0].cost is None
