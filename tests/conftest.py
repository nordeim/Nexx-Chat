"""Pytest configuration and fixtures.

Provides shared fixtures for all test types (unit, integration, e2e).
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime

from neural_terminal.domain.models import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
    TokenUsage,
)
from neural_terminal.infrastructure.repositories import SQLiteConversationRepository


# ============================================================================
# Domain Model Fixtures
# ============================================================================

@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing."""
    return Conversation(
        id=uuid4(),
        title="Test Conversation",
        model_id="openai/gpt-3.5-turbo",
        status=ConversationStatus.ACTIVE,
        total_cost=Decimal("0.05"),
        total_tokens=100,
        tags=["test"],
    )


@pytest.fixture
def sample_user_message():
    """Create a sample user message."""
    return Message(
        id=uuid4(),
        role=MessageRole.USER,
        content="Hello, this is a test message",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_assistant_message():
    """Create a sample assistant message with token usage."""
    return Message(
        id=uuid4(),
        role=MessageRole.ASSISTANT,
        content="This is a response",
        token_usage=TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        ),
        cost=Decimal("0.001"),
        latency_ms=500,
        model_id="openai/gpt-3.5-turbo",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_token_usage():
    """Create sample token usage for testing."""
    return TokenUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
    )


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def repository():
    """Create a fresh repository instance.
    
    Note: This uses the actual database. For true isolation,
    consider using an in-memory database for unit tests.
    """
    return SQLiteConversationRepository()


@pytest.fixture
def empty_conversation(repository):
    """Create and save an empty conversation."""
    conv = Conversation(
        id=uuid4(),
        title="Empty Test Conversation",
        model_id="openai/gpt-3.5-turbo",
    )
    repository.save(conv)
    return conv


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    from neural_terminal import config
    
    original_settings = config.settings
    
    # Create test settings
    test_settings = config.Settings(
        openrouter_api_key="test-key",
        openrouter_base_url="https://test.openrouter.ai/api/v1",
        database_url="sqlite:///test.db",
        app_env="testing",
    )
    
    monkeypatch.setattr(config, "settings", test_settings)
    
    yield test_settings
    
    # Restore original settings
    monkeypatch.setattr(config, "settings", original_settings)
