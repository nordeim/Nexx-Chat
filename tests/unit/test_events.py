"""Unit tests for event system.

Tests for Phase 2: Event bus with typed observers.
"""
from dataclasses import dataclass
from uuid import uuid4

import pytest

from neural_terminal.application.events import (
    DomainEvent,
    EventBus,
    EventObserver,
    Events,
)


class MockObserver(EventObserver):
    """Mock observer for testing."""
    
    def __init__(self):
        self.received_events = []
    
    def on_event(self, event: DomainEvent) -> None:
        self.received_events.append(event)


class ErrorObserver(EventObserver):
    """Observer that always raises an error."""
    
    def on_event(self, event: DomainEvent) -> None:
        raise RuntimeError("Test error")


class TestDomainEvent:
    """Tests for DomainEvent."""

    def test_event_creation(self):
        """Test creating a domain event."""
        conv_id = uuid4()
        event = DomainEvent(
            event_type="test.event",
            conversation_id=conv_id,
            payload={"key": "value"}
        )
        
        assert event.event_type == "test.event"
        assert event.conversation_id == conv_id
        assert event.payload == {"key": "value"}
    
    def test_event_is_frozen(self):
        """Test that events are immutable."""
        event = DomainEvent(event_type="test")
        
        with pytest.raises(Exception):
            event.event_type = "modified"
    
    def test_event_optional_fields(self):
        """Test creating event with optional fields."""
        event = DomainEvent(event_type="test.event")
        
        assert event.conversation_id is None
        assert event.payload is None


class TestEventBus:
    """Tests for EventBus."""

    def test_subscribe_and_emit(self):
        """Test subscribing to events and emitting."""
        bus = EventBus()
        observer = MockObserver()
        
        bus.subscribe("test.event", observer)
        
        event = DomainEvent(event_type="test.event")
        bus.emit(event)
        
        assert len(observer.received_events) == 1
        assert observer.received_events[0] == event
    
    def test_subscribe_all_receives_all_events(self):
        """Test global subscriber receives all events."""
        bus = EventBus()
        observer = MockObserver()
        
        bus.subscribe_all(observer)
        
        event1 = DomainEvent(event_type="event.one")
        event2 = DomainEvent(event_type="event.two")
        
        bus.emit(event1)
        bus.emit(event2)
        
        assert len(observer.received_events) == 2
    
    def test_specific_subscriber_only_receives_specific(self):
        """Test specific subscriber only gets their event type."""
        bus = EventBus()
        observer = MockObserver()
        
        bus.subscribe("specific.event", observer)
        
        bus.emit(DomainEvent(event_type="other.event"))
        bus.emit(DomainEvent(event_type="specific.event"))
        bus.emit(DomainEvent(event_type="another.event"))
        
        assert len(observer.received_events) == 1
        assert observer.received_events[0].event_type == "specific.event"
    
    def test_error_isolation(self):
        """Test that one subscriber's error doesn't stop others."""
        bus = EventBus()
        error_observer = ErrorObserver()
        good_observer = MockObserver()
        
        bus.subscribe("test.event", error_observer)
        bus.subscribe("test.event", good_observer)
        
        event = DomainEvent(event_type="test.event")
        bus.emit(event)  # Should not raise
        
        # Good observer should still receive event
        assert len(good_observer.received_events) == 1
    
    def test_multiple_observers_same_event(self):
        """Test multiple observers for same event type."""
        bus = EventBus()
        observer1 = MockObserver()
        observer2 = MockObserver()
        
        bus.subscribe("test.event", observer1)
        bus.subscribe("test.event", observer2)
        
        event = DomainEvent(event_type="test.event")
        bus.emit(event)
        
        assert len(observer1.received_events) == 1
        assert len(observer2.received_events) == 1
    
    def test_observer_receives_correct_event_data(self):
        """Test that observer receives correct event data."""
        bus = EventBus()
        observer = MockObserver()
        conv_id = uuid4()
        
        bus.subscribe("test.event", observer)
        
        event = DomainEvent(
            event_type="test.event",
            conversation_id=conv_id,
            payload={"cost": "0.05"}
        )
        bus.emit(event)
        
        received = observer.received_events[0]
        assert received.conversation_id == conv_id
        assert received.payload["cost"] == "0.05"


class TestEventsConstants:
    """Tests for Events constants."""

    def test_message_lifecycle_events(self):
        """Test message lifecycle event constants."""
        assert Events.MESSAGE_STARTED == "message.started"
        assert Events.TOKEN_GENERATED == "token.generated"
        assert Events.MESSAGE_COMPLETED == "message.completed"
    
    def test_budget_events(self):
        """Test budget event constants."""
        assert Events.BUDGET_THRESHOLD == "budget.threshold"
        assert Events.BUDGET_EXCEEDED == "budget.exceeded"
    
    def test_context_events(self):
        """Test context event constants."""
        assert Events.CONTEXT_TRUNCATED == "context.truncated"
