"""Tests for conversation export functionality.

Phase 6: Export Functionality - Export conversations to various formats.
"""

import json
from datetime import datetime
from uuid import uuid4
import pytest

from neural_terminal.domain.models import Conversation, Message, MessageRole, TokenUsage
from neural_terminal.infrastructure.repositories import SQLiteConversationRepository


class TestConversationExport:
    """Tests for conversation export."""

    def test_export_to_json_structure(self):
        """Test that export produces valid JSON structure."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        # Create conversation with messages
        conv = orchestrator.create_conversation(title="Export Test")

        from neural_terminal.domain.models import Message

        msg1 = Message(
            id=uuid4(), conversation_id=conv.id, role=MessageRole.USER, content="Hello"
        )
        msg2 = Message(
            id=uuid4(),
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="Hi there",
        )
        repo.add_message(msg1)
        repo.add_message(msg2)

        # Export
        exported = orchestrator.export_conversation(conv.id, format="json")

        # Should be valid JSON
        data = json.loads(exported)
        assert "id" in data
        assert "title" in data
        assert "messages" in data
        assert len(data["messages"]) == 2

    def test_export_includes_metadata(self):
        """Test that export includes conversation metadata."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(
            title="Test Conversation", model_id="openai/gpt-4"
        )

        exported = orchestrator.export_conversation(conv.id, format="json")
        data = json.loads(exported)

        assert data["title"] == "Test Conversation"
        assert data["model_id"] == "openai/gpt-4"
        assert "created_at" in data
        assert "updated_at" in data

    def test_export_messages_format(self):
        """Test that exported messages have correct format."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(title="Message Format Test")

        from neural_terminal.domain.models import Message

        msg = Message(
            id=uuid4(),
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="Test message",
            latency_ms=500,
            model_id="openai/gpt-4",
        )
        repo.add_message(msg)

        exported = orchestrator.export_conversation(conv.id, format="json")
        data = json.loads(exported)

        assert len(data["messages"]) == 1
        message = data["messages"][0]
        assert message["role"] == "user"
        assert message["content"] == "Test message"
        assert "timestamp" in message

    def test_export_to_markdown(self):
        """Test export to Markdown format."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(title="Markdown Test")

        from neural_terminal.domain.models import Message

        msg1 = Message(
            id=uuid4(), conversation_id=conv.id, role=MessageRole.USER, content="Hello"
        )
        msg2 = Message(
            id=uuid4(),
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="Hi there",
        )
        repo.add_message(msg1)
        repo.add_message(msg2)

        exported = orchestrator.export_conversation(conv.id, format="markdown")

        # Should be markdown format
        assert "# Markdown Test" in exported
        assert "## User" in exported or "**User**" in exported
        assert "Hello" in exported
        assert "Hi there" in exported

    def test_export_nonexistent_conversation(self):
        """Test export of non-existent conversation."""
        from neural_terminal.application.orchestrator import ChatOrchestrator
        from neural_terminal.domain.exceptions import ConversationNotFoundError

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        with pytest.raises(ConversationNotFoundError):
            orchestrator.export_conversation(uuid4(), format="json")

    def test_export_empty_conversation(self):
        """Test export of conversation with no messages."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(title="Empty")

        exported = orchestrator.export_conversation(conv.id, format="json")
        data = json.loads(exported)

        assert data["title"] == "Empty"
        assert data["messages"] == []

    def test_export_includes_cost_and_tokens(self):
        """Test that export includes cost and token information."""
        from decimal import Decimal
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(title="With Metrics")
        conv.total_cost = Decimal("0.05")
        conv.total_tokens = 150
        repo.save(conv)

        exported = orchestrator.export_conversation(conv.id, format="json")
        data = json.loads(exported)

        from decimal import Decimal

        assert Decimal(data["total_cost"]) == Decimal("0.05")
        assert data["total_tokens"] == 150

    def test_export_invalid_format(self):
        """Test export with invalid format."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(title="Format Test")

        with pytest.raises(ValueError, match="Unsupported format"):
            orchestrator.export_conversation(conv.id, format="xml")


class TestExportFormats:
    """Tests for different export formats."""

    def test_json_format_structure(self):
        """Test JSON export structure."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(title="JSON Test")

        exported = orchestrator.export_conversation(conv.id, format="json")

        # Parse and validate structure
        data = json.loads(exported)
        required_keys = [
            "id",
            "title",
            "model_id",
            "created_at",
            "updated_at",
            "total_cost",
            "total_tokens",
            "messages",
            "status",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

    def test_markdown_format_has_headers(self):
        """Test Markdown export has proper headers."""
        from neural_terminal.application.orchestrator import ChatOrchestrator

        repo = SQLiteConversationRepository()
        orchestrator = ChatOrchestrator(repo, None, None, None)

        conv = orchestrator.create_conversation(title="MD Headers Test")

        from neural_terminal.domain.models import Message

        msg = Message(
            id=uuid4(), conversation_id=conv.id, role=MessageRole.USER, content="Test"
        )
        repo.add_message(msg)

        exported = orchestrator.export_conversation(conv.id, format="markdown")

        # Should have markdown headers
        assert exported.startswith("#")
        assert "Test" in exported
