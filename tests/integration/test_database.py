"""Integration tests for database infrastructure.

Tests for Phase 0 Defect C-2: SQLite foreign keys fix.
Ensures PRAGMA foreign_keys=ON and PRAGMA journal_mode=WAL are set.
"""
import pytest
from sqlalchemy import text

from neural_terminal.infrastructure.database import (
    Base,
    ConversationORM,
    MessageORM,
    SessionLocal,
    engine,
)
from neural_terminal.domain.models import ConversationStatus, MessageRole


class TestDatabaseInfrastructure:
    """Tests for database infrastructure."""

    def test_foreign_keys_enabled(self):
        """Test that foreign key constraints are enabled.
        
        Phase 0 Defect C-2 Fix:
            Foreign keys must be explicitly enabled in SQLite via PRAGMA.
            The event listener must target the ENGINE INSTANCE, not the function.
        """
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys"))
            value = result.scalar()
            
            # Should return 1 (enabled), not 0 (disabled)
            assert value == 1, f"Foreign keys should be enabled, got {value}"
    
    def test_wal_mode_enabled(self):
        """Test that WAL mode is enabled for better concurrency."""
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode"))
            value = result.scalar()
            
            # Should return 'wal'
            assert value.lower() == "wal", f"WAL mode should be enabled, got {value}"
    
    def test_tables_created(self):
        """Test that all expected tables are created."""
        with engine.connect() as conn:
            # Get list of tables
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            assert "conversations" in tables, "conversations table should exist"
            assert "messages" in tables, "messages table should exist"
    
    def test_cascading_delete(self):
        """Test that deleting a conversation cascades to messages.
        
        This verifies foreign key constraints are actually enforced.
        """
        from uuid import uuid4
        from datetime import datetime
        
        session = SessionLocal()
        try:
            # Create a conversation
            conv_id = uuid4()
            conversation = ConversationORM(
                id=conv_id,
                title="Test Conversation",
                model_id="openai/gpt-3.5-turbo",
                status=ConversationStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                total_cost=0,
                total_tokens=0,
                tags=[],
            )
            session.add(conversation)
            session.commit()
            
            # Create messages for this conversation
            msg1_id = uuid4()
            msg2_id = uuid4()
            msg1 = MessageORM(
                id=msg1_id,
                conversation_id=conv_id,
                role=MessageRole.USER,
                content="Hello",
                created_at=datetime.utcnow(),
                metadata={},
            )
            msg2 = MessageORM(
                id=msg2_id,
                conversation_id=conv_id,
                role=MessageRole.ASSISTANT,
                content="Hi there",
                created_at=datetime.utcnow(),
                metadata={},
            )
            session.add(msg1)
            session.add(msg2)
            session.commit()
            
            # Verify messages exist
            messages = session.query(MessageORM).filter_by(conversation_id=conv_id).all()
            assert len(messages) == 2, "Should have 2 messages"
            
            # Delete the conversation (should cascade to messages)
            session.delete(conversation)
            session.commit()
            
            # Verify messages are also deleted
            remaining_messages = session.query(MessageORM).filter_by(conversation_id=conv_id).all()
            assert len(remaining_messages) == 0, "Messages should be deleted via cascade"
            
        finally:
            SessionLocal.remove()
    
    def test_foreign_key_violation_raises_error(self):
        """Test that foreign key violations raise proper errors."""
        from uuid import uuid4
        from datetime import datetime
        from sqlalchemy.exc import IntegrityError
        
        session = SessionLocal()
        try:
            # Try to create a message with non-existent conversation
            msg = MessageORM(
                id=uuid4(),
                conversation_id=uuid4(),  # Non-existent conversation
                role=MessageRole.USER,
                content="Test",
                created_at=datetime.utcnow(),
                metadata={},
            )
            session.add(msg)
            
            # Should raise IntegrityError due to foreign key constraint
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.rollback()
            SessionLocal.remove()
