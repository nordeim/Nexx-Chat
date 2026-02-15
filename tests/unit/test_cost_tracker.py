"""Unit tests for cost tracker.

Tests for Phase 2: Cost tracking with budget enforcement.
Tests for Phase 0 Defect C-6: EventBus injection.
"""
from decimal import Decimal

import pytest

from neural_terminal.application.events import DomainEvent, EventBus, Events
from neural_terminal.application.cost_tracker import CostTracker
from neural_terminal.domain.models import TokenUsage


class MockOpenRouterModel:
    """Mock model for testing."""
    
    def __init__(self, prompt_price: str, completion_price: str):
        self.prompt_price = Decimal(prompt_price)
        self.completion_price = Decimal(completion_price)


class TestCostTracker:
    """Tests for CostTracker."""

    def test_requires_event_bus(self):
        """Test that CostTracker requires EventBus in constructor."""
        bus = EventBus()
        
        # Should work with EventBus
        tracker = CostTracker(event_bus=bus)
        assert tracker._bus is bus
        
        # Subscribe tracker to events it cares about
        bus.subscribe(Events.MESSAGE_STARTED, tracker)
        bus.subscribe(Events.TOKEN_GENERATED, tracker)
        bus.subscribe(Events.MESSAGE_COMPLETED, tracker)
    
    def test_message_started_resets_tracking(self):
        """Test MESSAGE_STARTED resets tracking state."""
        bus = EventBus()
        tracker = CostTracker(event_bus=bus)
        bus.subscribe(Events.MESSAGE_STARTED, tracker)
        
        # Set some state
        tracker._estimated_tokens = 50
        tracker._is_tracking = False
        
        # Emit start event
        bus.emit(DomainEvent(event_type=Events.MESSAGE_STARTED))
        
        assert tracker._is_tracking is True
        assert tracker._estimated_tokens == 0
    
    def test_token_generated_estimates_cost(self):
        """Test TOKEN_GENERATED accumulates estimated tokens."""
        bus = EventBus()
        tracker = CostTracker(event_bus=bus)
        bus.subscribe(Events.MESSAGE_STARTED, tracker)
        bus.subscribe(Events.TOKEN_GENERATED, tracker)
        
        # Set model with pricing
        model = MockOpenRouterModel("0.001", "0.002")
        tracker.set_model(model)
        
        # Start tracking
        bus.emit(DomainEvent(event_type=Events.MESSAGE_STARTED))
        
        # Generate tokens (need 100 to trigger budget check)
        for _ in range(100):
            bus.emit(DomainEvent(
                event_type=Events.TOKEN_GENERATED,
                payload={"delta": "x"}
            ))
        
        assert tracker._estimated_tokens == 100
    
    def test_message_completed_calculates_actual_cost(self):
        """Test MESSAGE_COMPLETED calculates and accumulates cost."""
        bus = EventBus()
        tracker = CostTracker(event_bus=bus)
        bus.subscribe(Events.MESSAGE_STARTED, tracker)
        bus.subscribe(Events.MESSAGE_COMPLETED, tracker)
        
        # Set model with pricing
        model = MockOpenRouterModel("0.0015", "0.002")
        tracker.set_model(model)
        
        # Start tracking
        bus.emit(DomainEvent(event_type=Events.MESSAGE_STARTED))
        
        # Complete with usage
        usage = TokenUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        bus.emit(DomainEvent(
            event_type=Events.MESSAGE_COMPLETED,
            payload={"usage": usage}
        ))
        
        # Cost: (1000/1000)*0.0015 + (500/1000)*0.002 = 0.0015 + 0.001 = 0.0025
        assert tracker.accumulated_cost == Decimal("0.0025")
    
    def test_accumulated_cost_property(self):
        """Test accumulated_cost property returns correct value."""
        bus = EventBus()
        tracker = CostTracker(event_bus=bus)
        bus.subscribe(Events.MESSAGE_COMPLETED, tracker)
        model = MockOpenRouterModel("0.001", "0.002")
        tracker.set_model(model)
        
        assert tracker.accumulated_cost == Decimal("0")
        
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=0, total_tokens=1000)
        bus.emit(DomainEvent(
            event_type=Events.MESSAGE_COMPLETED,
            payload={"usage": usage}
        ))
        
        assert tracker.accumulated_cost == Decimal("0.001")
    
    def test_reset_clears_accumulated(self):
        """Test reset clears accumulated cost."""
        bus = EventBus()
        tracker = CostTracker(event_bus=bus)
        bus.subscribe(Events.MESSAGE_COMPLETED, tracker)
        model = MockOpenRouterModel("0.001", "0.002")
        tracker.set_model(model)
        
        # Accumulate some cost
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=0, total_tokens=1000)
        bus.emit(DomainEvent(
            event_type=Events.MESSAGE_COMPLETED,
            payload={"usage": usage}
        ))
        
        assert tracker.accumulated_cost > 0
        
        # Reset
        tracker.reset()
        
        assert tracker.accumulated_cost == Decimal("0")
    
    def test_no_budget_limit_no_events(self):
        """Test that no budget limit means no budget events."""
        bus = EventBus()
        
        emitted_events = []
        class TrackingObserver:
            def on_event(self, event):
                emitted_events.append(event)
        
        observer = TrackingObserver()
        bus.subscribe_all(observer)
        
        # Create tracker without budget limit
        tracker = CostTracker(event_bus=bus, budget_limit=None)
        bus.subscribe(Events.MESSAGE_COMPLETED, tracker)
        model = MockOpenRouterModel("0.001", "0.002")
        tracker.set_model(model)
        
        # Use lots of tokens
        for _ in range(10):
            usage = TokenUsage(prompt_tokens=10000, completion_tokens=0, total_tokens=10000)
            bus.emit(DomainEvent(
                event_type=Events.MESSAGE_COMPLETED,
                payload={"usage": usage}
            ))
        
        # Should not have emitted any budget events
        budget_events = [e for e in emitted_events if "budget" in e.event_type]
        assert len(budget_events) == 0
    
    def test_uses_injected_bus_not_orphan(self):
        """Test that tracker uses injected bus (C-6 fix verification)."""
        bus = EventBus()
        tracker = CostTracker(event_bus=bus)
        
        # Verify the bus is the one we injected
        assert tracker._bus is bus
    
    def test_budget_exceeded_during_message_completion(self):
        """Test BUDGET_EXCEEDED emitted when cost exceeds limit."""
        bus = EventBus()
        
        # Track emitted events
        emitted_events = []
        class TrackingObserver:
            def on_event(self, event):
                emitted_events.append(event)
        
        observer = TrackingObserver()
        bus.subscribe(Events.BUDGET_EXCEEDED, observer)
        
        # Create tracker with $0.005 limit
        tracker = CostTracker(event_bus=bus, budget_limit=Decimal("0.005"))
        bus.subscribe(Events.MESSAGE_COMPLETED, tracker)
        model = MockOpenRouterModel("0.001", "0.002")
        tracker.set_model(model)
        
        # Send a message that costs $0.001 (under limit)
        usage1 = TokenUsage(prompt_tokens=1000, completion_tokens=0, total_tokens=1000)
        bus.emit(DomainEvent(
            event_type=Events.MESSAGE_COMPLETED,
            payload={"usage": usage1}
        ))
        
        # No budget exceeded yet
        assert len([e for e in emitted_events if e.event_type == Events.BUDGET_EXCEEDED]) == 0
        
        # Send another message that pushes over limit (total $0.002 > $0.005 is false)
        # Actually, $0.001 + $0.001 = $0.002 which is still under $0.005
        # Let's send a bigger message
        usage2 = TokenUsage(prompt_tokens=10000, completion_tokens=0, total_tokens=10000)
        bus.emit(DomainEvent(
            event_type=Events.MESSAGE_COMPLETED,
            payload={"usage": usage2}
        ))
        
        # Now total is $0.001 + $0.01 = $0.011 which exceeds $0.005
        exceeded_events = [e for e in emitted_events if e.event_type == Events.BUDGET_EXCEEDED]
        assert len(exceeded_events) > 0
