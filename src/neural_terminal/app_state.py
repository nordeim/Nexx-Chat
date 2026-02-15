"""Application state management for Neural Terminal.

Provides centralized state management for the Streamlit application,
combining the StateManager from Phase 3 with application-level concerns.
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from decimal import Decimal
import threading

import streamlit as st

from .application.state import StateManager, AppState
from .application.orchestrator import ChatOrchestrator
from .application.events import EventBus
from .application.cost_tracker import CostTracker
from .infrastructure.database import init_db, get_db_session
from .infrastructure.repositories import SQLiteConversationRepository
from .infrastructure.openrouter import OpenRouterClient
from .infrastructure.token_counter import TokenCounter
from .infrastructure.circuit_breaker import CircuitBreaker
from .config import settings


@dataclass
class AppConfig:
    """Application configuration state."""
    openrouter_api_key: str = ""
    default_model: str = "openai/gpt-3.5-turbo"
    budget_limit: Optional[Decimal] = None
    theme: str = "terminal"
    max_tokens_per_message: int = 4000
    temperature: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "openrouter_api_key": self.openrouter_api_key,
            "default_model": self.default_model,
            "budget_limit": str(self.budget_limit) if self.budget_limit else None,
            "theme": self.theme,
            "max_tokens_per_message": self.max_tokens_per_message,
            "temperature": self.temperature,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Create from dictionary."""
        budget = data.get("budget_limit")
        return cls(
            openrouter_api_key=data.get("openrouter_api_key", ""),
            default_model=data.get("default_model", "openai/gpt-3.5-turbo"),
            budget_limit=Decimal(budget) if budget else None,
            theme=data.get("theme", "terminal"),
            max_tokens_per_message=data.get("max_tokens_per_message", 4000),
            temperature=data.get("temperature", 0.7),
        )


@dataclass
class SessionState:
    """Complete session state container."""
    app_config: AppConfig = field(default_factory=AppConfig)
    initialized: bool = False
    error_message: Optional[str] = None
    current_page: str = "chat"
    
    # Conversation state
    conversations: List[Dict[str, Any]] = field(default_factory=list)
    current_conversation_id: Optional[str] = None
    
    # Runtime state
    is_streaming: bool = False
    streaming_content: str = ""
    
    # Statistics
    total_cost: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_tokens: int = 0
    message_count: int = 0


class ApplicationState:
    """Centralized application state manager.
    
    Manages both UI state and business logic state,
    providing a single interface for the application.
    """
    
    _instance: Optional["ApplicationState"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "ApplicationState":
        """Singleton pattern for application state."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize application state."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._state_manager = StateManager()
        self._orchestrator: Optional[ChatOrchestrator] = None
        self._event_bus: Optional[EventBus] = None
        
        # Namespace for app state
        self._NAMESPACE = "nt_app_"
    
    def _get_key(self, key: str) -> str:
        """Get namespaced key."""
        return f"{self._NAMESPACE}{key}"
    
    def _ensure_state(self) -> None:
        """Ensure session state is initialized."""
        state_key = self._get_key("session")
        if state_key not in st.session_state:
            st.session_state[state_key] = SessionState()
    
    @property
    def session(self) -> SessionState:
        """Get current session state."""
        self._ensure_state()
        return st.session_state[self._get_key("session")]
    
    @property
    def config(self) -> AppConfig:
        """Get application configuration."""
        return self.session.app_config
    
    @config.setter
    def config(self, value: AppConfig) -> None:
        """Set application configuration."""
        self.session.app_config = value
        self._persist_config()
    
    @property
    def orchestrator(self) -> Optional[ChatOrchestrator]:
        """Get chat orchestrator."""
        return self._orchestrator
    
    def is_initialized(self) -> bool:
        """Check if application is initialized."""
        return self.session.initialized
    
    def initialize(self) -> None:
        """Initialize application state and dependencies.
        
        This should be called once at application startup.
        """
        if self.session.initialized:
            return
        
        try:
            # Initialize database
            init_db()
            
            # Load configuration
            self._load_config()
            
            # Initialize event system
            self._event_bus = EventBus()
            
            # Initialize cost tracker
            cost_tracker = CostTracker(
                self._event_bus,
                budget_limit=self.config.budget_limit,
            )
            
            # Initialize infrastructure
            circuit_breaker = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30.0,
            )
            
            openrouter = OpenRouterClient(
                api_key=self.config.openrouter_api_key or settings.openrouter_api_key,
                circuit_breaker=circuit_breaker,
            )
            
            tokenizer = TokenCounter()
            repository = SQLiteConversationRepository()
            
            # Initialize orchestrator
            self._orchestrator = ChatOrchestrator(
                openrouter_client=openrouter,
                conversation_repository=repository,
                token_counter=tokenizer,
                event_bus=self._event_bus,
                circuit_breaker=circuit_breaker,
                cost_tracker=cost_tracker,
            )
            
            # Subscribe to events
            self._setup_event_handlers()
            
            # Load conversation list
            self._load_conversations()
            
            self.session.initialized = True
            self.session.error_message = None
            
        except Exception as e:
            self.session.error_message = str(e)
            self.session.initialized = False
            raise
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers."""
        if not self._event_bus:
            return
        
        # Handle budget threshold
        from .application.events import Events
        
        def on_budget_threshold(event: Any) -> None:
            st.warning(f"⚠️ Budget at {event.payload.get('percent', 0):.1f}%")
        
        def on_budget_exceeded(event: Any) -> None:
            st.error("⚠️ Budget exceeded! Please increase limit or start new session.")
        
        self._event_bus.subscribe(Events.BUDGET_THRESHOLD, on_budget_threshold)
        self._event_bus.subscribe(Events.BUDGET_EXCEEDED, on_budget_exceeded)
    
    def _load_config(self) -> None:
        """Load configuration from storage."""
        config_key = self._get_key("config")
        if config_key in st.session_state:
            try:
                data = st.session_state[config_key]
                self.session.app_config = AppConfig.from_dict(data)
            except Exception:
                pass  # Use defaults
    
    def _persist_config(self) -> None:
        """Persist configuration to storage."""
        config_key = self._get_key("config")
        st.session_state[config_key] = self.session.app_config.to_dict()
    
    def _load_conversations(self) -> None:
        """Load conversation list from repository."""
        if not self._orchestrator:
            return
        
        try:
            conversations = self._orchestrator.get_conversation_history(limit=100)
            self.session.conversations = [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "created_at": c.created_at.isoformat() if c.created_at else "",
                    "total_cost": str(c.total_cost),
                }
                for c in conversations
            ]
        except Exception:
            self.session.conversations = []
    
    def update_config(self, **kwargs) -> None:
        """Update configuration values.
        
        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._persist_config()
    
    def set_current_conversation(self, conversation_id: Optional[str]) -> None:
        """Set current conversation.
        
        Args:
            conversation_id: Conversation ID or None
        """
        self.session.current_conversation_id = conversation_id
        
        if conversation_id and self._orchestrator:
            try:
                conversation = self._orchestrator.get_conversation(conversation_id)
                self._state_manager.set_conversation(conversation)
            except Exception:
                pass
    
    def create_conversation(self, system_prompt: Optional[str] = None) -> str:
        """Create new conversation.
        
        Args:
            system_prompt: Optional system prompt
            
        Returns:
            New conversation ID
        """
        if not self._orchestrator:
            raise RuntimeError("Application not initialized")
        
        conversation = self._orchestrator.create_conversation(
            system_prompt=system_prompt,
        )
        
        self.session.current_conversation_id = str(conversation.id)
        self._load_conversations()
        
        return str(conversation.id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation.
        
        Args:
            conversation_id: Conversation ID to delete
            
        Returns:
            True if deleted successfully
        """
        if not self._orchestrator:
            return False
        
        try:
            # Note: This would need to be implemented in the repository
            # For now, just remove from list
            self.session.conversations = [
                c for c in self.session.conversations
                if c["id"] != conversation_id
            ]
            
            if self.session.current_conversation_id == conversation_id:
                self.session.current_conversation_id = None
            
            return True
        except Exception:
            return False
    
    def get_conversation_messages(self) -> List[Dict[str, Any]]:
        """Get messages for current conversation.
        
        Returns:
            List of message dictionaries
        """
        if not self._orchestrator or not self.session.current_conversation_id:
            return []
        
        try:
            messages = self._orchestrator.get_conversation_messages(
                self.session.current_conversation_id,
            )
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else "",
                    "cost": str(m.cost) if m.cost else "0",
                    "tokens": m.token_usage.total_tokens if m.token_usage else 0,
                }
                for m in messages
            ]
        except Exception:
            return []
    
    async def send_message(self, content: str) -> Any:
        """Send message in current conversation.
        
        Args:
            content: Message content
            
        Yields:
            Stream chunks
        """
        if not self._orchestrator:
            raise RuntimeError("Application not initialized")
        
        if not self.session.current_conversation_id:
            # Create new conversation
            self.create_conversation()
        
        self.session.is_streaming = True
        self.session.streaming_content = ""
        
        try:
            async for chunk, error in self._orchestrator.send_message(
                conversation_id=self.session.current_conversation_id,
                content=content,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens_per_message,
                model=self.config.default_model,
            ):
                if error:
                    raise error
                
                if chunk:
                    self.session.streaming_content += chunk
                    yield chunk
        
        finally:
            self.session.is_streaming = False
            self._update_stats()
    
    def _update_stats(self) -> None:
        """Update session statistics."""
        if not self._orchestrator:
            return
        
        # This would integrate with cost tracker
        # For now, just increment counters
        self.session.message_count += 1


# Global instance getter
def get_app_state() -> ApplicationState:
    """Get the global application state instance.
    
    Returns:
        ApplicationState singleton
    """
    return ApplicationState()


def init_app() -> ApplicationState:
    """Initialize application.
    
    Returns:
        Initialized ApplicationState
    """
    app = get_app_state()
    
    if not app.is_initialized():
        app.initialize()
    
    return app
