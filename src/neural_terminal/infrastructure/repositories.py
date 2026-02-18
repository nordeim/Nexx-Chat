"""Repository pattern implementation for Neural Terminal.

Phase 0 Defect C-3 Fix:
- Replace broken context manager pattern with proper _session_scope()
- Add get_messages() method (Phase 0 Defect H-5)
- Add _message_to_domain() converter
- Use SessionLocal.remove() for cleanup
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from decimal import Decimal
from typing import Generator, List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from neural_terminal.domain.models import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
    TokenUsage,
)
from neural_terminal.infrastructure.database import (
    ConversationORM,
    MessageORM,
    SessionLocal,
)


class ConversationRepository(ABC):
    """Abstract base class for conversation repositories."""

    @abstractmethod
    def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Retrieve a conversation by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_messages(self, conversation_id: UUID) -> List[Message]:
        """Retrieve all messages for a conversation.

        Phase 0 Defect H-5 Fix:
            This method was missing but is required by ChatOrchestrator.
            Messages must be ordered by created_at ascending.
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, conversation: Conversation) -> None:
        """Save or update a conversation."""
        raise NotImplementedError

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Add a message to a conversation."""
        raise NotImplementedError

    @abstractmethod
    def list_active(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List active conversations ordered by updated_at descending."""
        raise NotImplementedError


class SQLiteConversationRepository(ConversationRepository):
    """Thread-safe SQLite implementation of conversation repository.

    Phase 0 Defect C-3 Fix:
        Uses _session_scope() context manager for proper session lifecycle.
        SessionLocal.remove() is called in finally block to prevent leaks.
    """

    @contextmanager
    def _session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations.

        Yields:
            SQLAlchemy Session

        Ensures:
            - Commit on success
            - Rollback on exception
            - Session cleanup via scoped_session.remove()

        Phase 0 Defect C-3 Fix:
            This replaces the broken _get_session()/_close_session() pattern
            that leaked sessions by creating orphaned context managers.
        """
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            SessionLocal.remove()  # Critical for scoped_session cleanup

    def _to_domain(self, orm: ConversationORM) -> Conversation:
        """Convert Conversation ORM to domain model."""
        return Conversation(
            id=orm.id,
            title=orm.title,
            model_id=orm.model_id,
            status=orm.status,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            total_cost=orm.total_cost or Decimal("0"),
            total_tokens=orm.total_tokens or 0,
            parent_conversation_id=orm.parent_conversation_id,
            tags=orm.tags or [],
        )

    def _message_to_domain(self, orm: MessageORM) -> Message:
        """Convert Message ORM to domain model.

        Phase 0 Defect C-3 Fix:
            Properly reconstructs TokenUsage from individual token columns.
            Handles None values gracefully.
        """
        usage = None
        if orm.prompt_tokens is not None:
            usage = TokenUsage(
                prompt_tokens=orm.prompt_tokens,
                completion_tokens=orm.completion_tokens or 0,
                total_tokens=orm.total_tokens or 0,
            )

        return Message(
            id=orm.id,
            conversation_id=orm.conversation_id,
            role=orm.role,
            content=orm.content,
            token_usage=usage,
            cost=orm.cost,
            latency_ms=orm.latency_ms,
            model_id=orm.model_id,
            created_at=orm.created_at,
            metadata=orm.meta or {},  # Note: 'meta' column stores metadata
        )

    def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Retrieve a conversation by ID."""
        with self._session_scope() as session:
            result = session.execute(
                select(ConversationORM).where(ConversationORM.id == conversation_id)
            ).scalar_one_or_none()
            return self._to_domain(result) if result else None

    def get_messages(self, conversation_id: UUID) -> List[Message]:
        """Retrieve all messages for a conversation, ordered by creation time.

        Phase 0 Defect H-5 Fix:
            This method was missing from the original design but is required
            by ChatOrchestrator to retrieve conversation history for context.

        Args:
            conversation_id: The conversation UUID

        Returns:
            List of messages ordered by created_at ascending (oldest first)
        """
        with self._session_scope() as session:
            results = (
                session.execute(
                    select(MessageORM)
                    .where(MessageORM.conversation_id == conversation_id)
                    .order_by(MessageORM.created_at.asc())
                )
                .scalars()
                .all()
            )
            return [self._message_to_domain(r) for r in results]

    def save(self, conversation: Conversation) -> None:
        """Save or update a conversation."""
        with self._session_scope() as session:
            orm = ConversationORM(
                id=conversation.id,
                title=conversation.title,
                model_id=conversation.model_id,
                status=conversation.status,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                total_cost=conversation.total_cost,
                total_tokens=conversation.total_tokens,
                parent_conversation_id=conversation.parent_conversation_id,
                tags=conversation.tags,
            )
            session.merge(orm)  # Upsert

    def add_message(self, message: Message) -> None:
        """Add a message to a conversation."""
        if message.conversation_id is None:
            raise ValueError("Message must belong to a conversation")

        with self._session_scope() as session:
            orm = MessageORM(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                prompt_tokens=message.token_usage.prompt_tokens
                if message.token_usage
                else None,
                completion_tokens=message.token_usage.completion_tokens
                if message.token_usage
                else None,
                total_tokens=message.token_usage.total_tokens
                if message.token_usage
                else None,
                cost=message.cost,
                latency_ms=message.latency_ms,
                model_id=message.model_id,
                metadata=message.metadata,
            )
            session.add(orm)

    def list_active(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List active conversations ordered by updated_at descending.

        Phase 5: Soft Delete - Excludes DELETED conversations.
        """
        with self._session_scope() as session:
            results = (
                session.execute(
                    select(ConversationORM)
                    .where(
                        (ConversationORM.status == ConversationStatus.ACTIVE)
                        | (ConversationORM.status == ConversationStatus.ARCHIVED)
                        | (ConversationORM.status == ConversationStatus.FORKED)
                    )
                    .order_by(ConversationORM.updated_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            return [self._to_domain(r) for r in results]

    def list_all(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List all conversations including soft deleted.

        Phase 5: Soft Delete - Includes all conversation statuses.

        Args:
            limit: Maximum number of conversations
            offset: Number of conversations to skip

        Returns:
            List of all conversations
        """
        with self._session_scope() as session:
            results = (
                session.execute(
                    select(ConversationORM)
                    .order_by(ConversationORM.updated_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            return [self._to_domain(r) for r in results]

    def soft_delete(self, conversation_id: UUID) -> None:
        """Soft delete a conversation by setting status to DELETED.

        Phase 5: Soft Delete - Marks conversation as deleted without
        removing data from database.

        Args:
            conversation_id: The conversation UUID to delete
        """
        with self._session_scope() as session:
            session.execute(
                update(ConversationORM)
                .where(ConversationORM.id == conversation_id)
                .values(status=ConversationStatus.DELETED)
            )

    def restore_conversation(self, conversation_id: UUID) -> None:
        """Restore a soft-deleted conversation to ACTIVE status.

        Phase 5: Soft Delete - Restores conversation from deleted status.

        Args:
            conversation_id: The conversation UUID to restore
        """
        with self._session_scope() as session:
            session.execute(
                update(ConversationORM)
                .where(ConversationORM.id == conversation_id)
                .values(status=ConversationStatus.ACTIVE)
            )
