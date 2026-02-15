"""Cost tracking with budget enforcement.

Phase 0 Defect C-6 Fix:
    EventBus is injected in constructor, not created as orphan instance.
    This ensures budget events are emitted to the shared bus.
"""
from decimal import Decimal
from typing import Optional

from neural_terminal.application.events import DomainEvent, EventBus, EventObserver, Events
from neural_terminal.domain.models import TokenUsage
from neural_terminal.infrastructure.openrouter import OpenRouterModel


class CostTracker(EventObserver):
    """Real-time cost accumulator with budget enforcement.
    
    Implements Observer pattern for decoupled economic tracking.
    
    Phase 0 Defect C-6 Fix:
        EventBus is injected via constructor. Never create new EventBus
        instances within methods - that sends events to nowhere.
    
    Args:
        event_bus: Shared EventBus instance for emitting budget events
        budget_limit: Optional budget limit in USD
    """
    
    def __init__(self, event_bus: EventBus, budget_limit: Optional[Decimal] = None):
        """Initialize cost tracker.
        
        Args:
            event_bus: Shared event bus (injected, not created)
            budget_limit: Optional budget limit in USD
        """
        self._bus = event_bus  # Injected singleton - use this!
        self._accumulated = Decimal("0.00")
        self._budget_limit = budget_limit
        self._current_model_price: Optional[OpenRouterModel] = None
        self._estimated_tokens = 0
        self._is_tracking = False
    
    def set_model(self, model: OpenRouterModel) -> None:
        """Set current pricing model for estimation.
        
        Args:
            model: OpenRouter model with pricing
        """
        self._current_model_price = model
    
    def on_event(self, event: DomainEvent) -> None:
        """Handle domain events for cost tracking.
        
        Args:
            event: Domain event to process
        """
        if event.event_type == Events.MESSAGE_STARTED:
            self._is_tracking = True
            self._estimated_tokens = 0
        
        elif event.event_type == Events.TOKEN_GENERATED:
            # Estimate cost during streaming (rough approximation)
            self._estimated_tokens += 1
            # Check budget every 100 tokens
            if self._estimated_tokens % 100 == 0:
                self._check_budget(self._estimate_current_cost())
        
        elif event.event_type == Events.MESSAGE_COMPLETED:
            # Reconcile with actual usage from API
            usage = event.payload.get("usage") if event.payload else None
            if usage and isinstance(usage, TokenUsage):
                actual_cost = self._calculate_actual_cost(usage)
                self._accumulated += actual_cost
                self._is_tracking = False
                
                # Final budget check
                if self._budget_limit and self._accumulated > self._budget_limit:
                    self._emit_budget_exceeded()
    
    def _estimate_current_cost(self) -> Decimal:
        """Estimate cost during streaming.
        
        Returns:
            Estimated cost based on current token count
        """
        if not self._current_model_price or not self._current_model_price.completion_price:
            return Decimal("0")
        
        return (Decimal(self._estimated_tokens) / 1000) * self._current_model_price.completion_price
    
    def _calculate_actual_cost(self, usage: TokenUsage) -> Decimal:
        """Calculate precise cost from usage.
        
        Args:
            usage: Token usage from API
            
        Returns:
            Actual cost in USD
        """
        if not self._current_model_price:
            return Decimal("0")
        
        prompt_price = self._current_model_price.prompt_price or Decimal("0")
        completion_price = self._current_model_price.completion_price or Decimal("0")
        
        return usage.calculate_cost(prompt_price, completion_price)
    
    def _check_budget(self, estimated_cost: Decimal) -> None:
        """Check if approaching budget limit and emit events.
        
        Args:
            estimated_cost: Current estimated cost
        """
        if not self._budget_limit:
            return
        
        projected = self._accumulated + estimated_cost
        
        if projected > self._budget_limit:
            self._emit_budget_exceeded()
        elif projected > self._budget_limit * Decimal("0.8"):
            # Emit warning at 80%
            self._bus.emit(DomainEvent(
                event_type=Events.BUDGET_THRESHOLD,
                conversation_id=None,
                payload={
                    "accumulated": str(self._accumulated),
                    "limit": str(self._budget_limit),
                }
            ))
    
    def _emit_budget_exceeded(self) -> None:
        """Emit budget exceeded event using injected bus."""
        self._bus.emit(DomainEvent(
            event_type=Events.BUDGET_EXCEEDED,
            conversation_id=None,
            payload={"accumulated": str(self._accumulated)}
        ))
    
    @property
    def accumulated_cost(self) -> Decimal:
        """Get accumulated cost."""
        return self._accumulated
    
    def reset(self) -> None:
        """Reset accumulated cost."""
        self._accumulated = Decimal("0.00")
