"""Unit tests for circuit breaker.

Tests for Phase 0 Defect C-7: Circuit breaker test fix.
Tests for Phase 0 Defect H-2: Thread safety.
Tests for Phase 0 Defect C-4: _check_state method.
"""
import threading
import time

import pytest

from neural_terminal.domain.exceptions import CircuitBreakerOpenError
from neural_terminal.infrastructure.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Tests for circuit breaker."""

    def test_circuit_starts_closed(self):
        """Test that circuit starts in closed state."""
        cb = CircuitBreaker()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_successful_call_resets_failure_count(self):
        """Test that successful call resets failure count."""
        cb = CircuitBreaker(failure_threshold=3)
        
        # Fail twice
        def fail():
            raise ValueError("error")
        
        with pytest.raises(ValueError):
            cb.call(fail)
        with pytest.raises(ValueError):
            cb.call(fail)
        
        assert cb.failure_count == 2
        assert cb.state == CircuitState.CLOSED
        
        # Succeed - should reset
        result = cb.call(lambda: "success")
        
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure threshold reached.
        
        Phase 0 Defect C-7 Fix:
            Test was broken because it didn't handle exceptions properly.
            Each call that fails raises the original exception.
            Only after threshold is the CircuitBreakerOpenError raised.
        """
        cb = CircuitBreaker(failure_threshold=2)
        
        def fail():
            raise ValueError("error")
        
        # 1st failure - exception propagates, circuit still closed
        with pytest.raises(ValueError):
            cb.call(fail)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1
        
        # 2nd failure - exception propagates, circuit now open
        with pytest.raises(ValueError):
            cb.call(fail)
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2
        
        # 3rd call - circuit is open, should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(fail)
    
    def test_check_state_raises_when_open(self):
        """Test that _check_state raises when circuit is open.
        
        Phase 0 Defect C-4 Fix:
            _check_state() method added for manual circuit state checks.
        """
        cb = CircuitBreaker(failure_threshold=1)
        
        def fail():
            raise ValueError("error")
        
        # Open the circuit
        with pytest.raises(ValueError):
            cb.call(fail)
        
        assert cb.state == CircuitState.OPEN
        
        # _check_state should raise
        with pytest.raises(CircuitBreakerOpenError):
            cb._check_state()
    
    def test_check_state_transitions_to_half_open(self):
        """Test that _check_state transitions to half_open after timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        def fail():
            raise ValueError("error")
        
        # Open the circuit
        with pytest.raises(ValueError):
            cb.call(fail)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # _check_state should transition to HALF_OPEN
        cb._check_state()  # Should not raise
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_circuit_closes_after_success_in_half_open(self):
        """Test that circuit closes after success in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        def fail():
            raise ValueError("error")
        
        # Open the circuit
        with pytest.raises(ValueError):
            cb.call(fail)
        
        # Wait for recovery
        time.sleep(0.15)
        
        # Success in half-open should close circuit
        result = cb.call(lambda: "success")
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_circuit_reopens_after_failure_in_half_open(self):
        """Test that circuit reopens after failure in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        def fail():
            raise ValueError("error")
        
        # Open the circuit
        with pytest.raises(ValueError):
            cb.call(fail)
        
        # Wait for recovery
        time.sleep(0.15)
        
        # Failure in half-open should reopen circuit
        with pytest.raises(ValueError):
            cb.call(fail)
        
        assert cb.state == CircuitState.OPEN
    
    def test_thread_safety(self):
        """Test that circuit breaker is thread-safe.
        
        Phase 0 Defect H-2 Fix:
            Circuit breaker must be thread-safe for Streamlit's multi-session
            environment.
        """
        cb = CircuitBreaker(failure_threshold=100)  # High threshold for this test
        success_count = [0]
        lock = threading.Lock()
        
        def increment():
            with lock:
                success_count[0] += 1
            return success_count[0]
        
        # Spawn 50 threads, each calling 10 times
        threads = []
        for _ in range(50):
            t = threading.Thread(target=lambda: [cb.call(increment) for _ in range(10)])
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All calls should succeed
        assert success_count[0] == 500
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED
