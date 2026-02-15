"""Circuit breaker pattern implementation.

Phase 0 Defect H-2 Fix:
- Add threading.Lock() for thread safety
- Lock around all state mutations

Phase 0 Defect C-4 Fix:
- Add _check_state() method for manual circuit state verification
  (used by streaming to check circuit before starting)
"""
import threading
import time
from enum import Enum, auto
from functools import wraps
from typing import Callable, Optional, TypeVar

from neural_terminal.config import settings
from neural_terminal.domain.exceptions import CircuitBreakerOpenError

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Failing, reject fast
    HALF_OPEN = auto()   # Testing if recovered


class CircuitBreaker:
    """Thread-safe circuit breaker for external API calls.
    
    Phase 0 Defect H-2 Fix:
        Uses threading.Lock() to prevent race conditions in Streamlit's
        multi-session environment.
    
    Phase 0 Defect C-4 Fix:
        Provides _check_state() method for manual circuit state checks,
        which is needed for async streaming where we can't wrap the
        async generator in the circuit breaker.
    """
    
    def __init__(
        self,
        failure_threshold: int = settings.circuit_failure_threshold,
        recovery_timeout: int = settings.circuit_recovery_timeout,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED
        self._lock = threading.Lock()  # Phase 0 Defect H-2 Fix
    
    def _check_state(self) -> None:
        """Check if circuit allows operation.
        
        Phase 0 Defect C-4 Fix:
            This method is called manually before async streaming operations
            to check circuit state without wrapping the async generator.
        
        Raises:
            CircuitBreakerOpenError: If circuit is open and recovery timeout
                hasn't elapsed.
        """
        with self._lock:  # Thread-safe state check
            if self._state == CircuitState.OPEN:
                if time.time() - (self._last_failure_time or 0) > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit is OPEN. Retry after {self.recovery_timeout}s"
                    )
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit protection (synchronous).
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if function fails
        """
        self._check_state()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit protection.
        
        WARNING: Do NOT use this with async generators (functions that yield).
        For async generators, use _check_state() manually before iterating.
        
        Phase 0 Defect C-4 Note:
            This method awaits the result. It CANNOT be used with async
            generators (functions using 'yield'). For streaming, use:
            1. Call _check_state() manually
            2. Iterate the async generator directly
            3. Call _on_success() or _on_failure() manually
        
        Args:
            func: Async function to call (NOT async generator)
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if function fails
        """
        self._check_state()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self) -> None:
        """Record successful operation.
        
        Phase 0 Defect H-2 Fix:
            Uses lock for thread-safe state mutation.
        """
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
    
    def _on_failure(self) -> None:
        """Record failed operation.
        
        Phase 0 Defect H-2 Fix:
            Uses lock for thread-safe state mutation.
        """
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        with self._lock:
            return self._failure_count
