"""Database infrastructure for Neural Terminal.

Phase 0 Defect C-2 Fix:
- Add missing imports (Column, Text, datetime)
- Create engine BEFORE event listener
- Listen on ENGINE INSTANCE, not the function
- Add PRAGMA journal_mode=WAL for better concurrency
- Use SQLAlchemy 2.0 DeclarativeBase style
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    create_engine,
    event,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    relationship,
    scoped_session,
    sessionmaker,
)

from neural_terminal.config import settings
from neural_terminal.domain.models import ConversationStatus, MessageRole


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base."""
    pass


# ============================================================================
# PHASE 0 DEFECT C-2 FIX
# ============================================================================
# Create engine FIRST at module level, BEFORE any event listeners.
# This ensures we have an engine instance to listen on.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for Streamlit threads
    pool_pre_ping=True,
)


# Listen on the ENGINE INSTANCE, not the create_engine function!
# This was the critical bug: @event.listens_for(create_engine, "connect") was wrong.
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints and production optimizations on connection.
    
    Phase 0 Defect C-2 Fix:
        - PRAGMA foreign_keys=ON ensures foreign key constraints are enforced
        - PRAGMA journal_mode=WAL enables Write-Ahead Logging for better concurrency
    
    Production Optimizations:
        - PRAGMA synchronous=NORMAL (balance of safety and performance)
        - PRAGMA cache_size=-64000 (~64MB cache)
        - PRAGMA temp_store=MEMORY (faster temp operations)
        - PRAGMA mmap_size=268435456 (256MB memory-mapped I/O)
    
    Args:
        dbapi_conn: The DBAPI connection
        connection_record: The connection record
    """
    cursor = dbapi_conn.cursor()
    # Critical settings
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    # Performance optimizations
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")
    cursor.close()


# Create scoped session factory for thread safety
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


class ConversationORM(Base):
    """SQLAlchemy ORM model for conversations."""
    
    __tablename__ = "conversations"
    
    id = Column(Uuid(as_uuid=True), primary_key=True)
    title = Column(String(255), nullable=True)
    model_id = Column(String(100), nullable=False)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_cost = Column(Numeric(10, 6), default=0)
    total_tokens = Column(Integer, default=0)
    parent_conversation_id = Column(
        Uuid(as_uuid=True), 
        ForeignKey("conversations.id"),
        nullable=True
    )
    tags = Column(JSON, default=list)
    
    # Relationship to messages with cascade delete
    messages = relationship(
        "MessageORM",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class MessageORM(Base):
    """SQLAlchemy ORM model for messages."""
    
    __tablename__ = "messages"
    
    id = Column(Uuid(as_uuid=True), primary_key=True)
    conversation_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False
    )
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 6), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    model_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta = Column("metadata", JSON, default=dict)
    
    # Relationship back to conversation
    conversation = relationship("ConversationORM", back_populates="messages")


# Create all tables
Base.metadata.create_all(bind=engine)


def init_db() -> None:
    """Initialize database tables.
    
    Creates all tables if they don't exist.
    Safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Get a database session.
    
    Returns:
        SQLAlchemy Session
    """
    return SessionLocal()
