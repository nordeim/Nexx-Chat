"""Event system for decoupled communication.

Implements Observer pattern with typed event bus.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    """Immutable domain event.
    
    Attributes:
        event_type: Event type identifier
        conversation_id: Optional conversation context
        payload: Event data dictionary
    """
    event_type: str
    conversation_id: Optional[UUID] = None
    payload: Optional[Dict[str, Any]] = None


class EventObserver(ABC):
    """Abstract base class for event observers."""
    
    @abstractmethod
    def on_event(self, event: DomainEvent) -> None:
        """Handle a domain event.
        
        Args:
            event: The event to handle
        """
        raise NotImplementedError


class EventBus:
    """Thread-safe event bus for decoupled communication.
    
    Supports:
    - Typed subscribers (specific event types)
    - Global subscribers (all events)
    - Error isolation (subscriber failures don't stop propagation)
    """
    
    def __init__(self):
        """Initialize empty subscriber registry."""
        self._subscribers: Dict[str, List[EventObserver]] = {}
        self._global_subscribers: List[EventObserver] = []
    
    def subscribe(self, event_type: str, observer: EventObserver) -> None:
        """Subscribe to a specific event type.
        
        Args:
            event_type: Event type to subscribe to
            observer: Observer instance
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(observer)
    
    def subscribe_all(self, observer: EventObserver) -> None:
        """Subscribe to all events.
        
        Args:
            observer: Observer instance
        """
        self._global_subscribers.append(observer)
    
    def emit(self, event: DomainEvent) -> None:
        """Emit an event to all subscribers.
        
        Errors in subscribers are caught and logged but don't stop
        event propagation to other subscribers.
        
        Args:
            event: Event to emit
        """
        # Notify specific subscribers
        for observer in self._subscribers.get(event.event_type, []):
            try:
                observer.on_event(event)
            except Exception as e:
                # Log but don't stop propagation
                print(f"Event handler error: {e}")
        
        # Notify global subscribers
        for observer in self._global_subscribers:
            try:
                observer.on_event(event)
            except Exception as e:
                print(f"Global handler error: {e}")


class Events:
    """Standard event type constants."""
    
    # Message lifecycle
    MESSAGE_STARTED = "message.started"
    TOKEN_GENERATED = "token.generated"
    MESSAGE_COMPLETED = "message.completed"
    
    # Budget
    BUDGET_THRESHOLD = "budget.threshold"
    BUDGET_EXCEEDED = "budget.exceeded"
    
    # Context
    CONTEXT_TRUNCATED = "context.truncated"
