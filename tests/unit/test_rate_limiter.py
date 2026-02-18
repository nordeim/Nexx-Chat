"""Tests for RateLimiter implementation.

Phase 2: Rate Limiting - Token bucket algorithm for API protection.
"""

import time
import threading
import pytest

from neural_terminal.domain.exceptions import RateLimitExceededError
from neural_terminal.infrastructure.rate_limiter import RateLimiter, RateLimitConfig


class TestRateLimiterConfig:
    """Tests for RateLimitConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 20
        assert config.burst_size == 5

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(requests_per_minute=60, burst_size=10)
        assert config.requests_per_minute == 60
        assert config.burst_size == 10

    def test_invalid_requests_per_minute(self):
        """Test that invalid requests_per_minute raises error."""
        with pytest.raises(ValueError):
            RateLimitConfig(requests_per_minute=0)

        with pytest.raises(ValueError):
            RateLimitConfig(requests_per_minute=-1)

    def test_invalid_burst_size(self):
        """Test that invalid burst_size raises error."""
        with pytest.raises(ValueError):
            RateLimitConfig(burst_size=0)

        with pytest.raises(ValueError):
            RateLimitConfig(burst_size=-1)


class TestRateLimiter:
    """Tests for RateLimiter token bucket implementation."""

    def test_initial_state_allows_requests(self):
        """Test that rate limiter allows requests initially."""
        limiter = RateLimiter()
        limiter.acquire()
        assert limiter.available_tokens == 4

    def test_acquire_consumes_token(self):
        """Test that acquire consumes a token."""
        limiter = RateLimiter(config=RateLimitConfig(burst_size=3))
        assert limiter.available_tokens == 3

        limiter.acquire()
        assert limiter.available_tokens == 2

        limiter.acquire()
        assert limiter.available_tokens == 1

    def test_exhaust_tokens_raises_error(self):
        """Test that exhausting tokens raises RateLimitExceededError."""
        limiter = RateLimiter(config=RateLimitConfig(burst_size=2))

        limiter.acquire()
        limiter.acquire()

        with pytest.raises(RateLimitExceededError) as exc_info:
            limiter.acquire()

        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"

    def test_tokens_replenish_over_time(self):
        """Test that tokens replenish based on requests_per_minute."""
        config = RateLimitConfig(requests_per_minute=60, burst_size=1)
        limiter = RateLimiter(config=config)

        limiter.acquire()
        assert limiter.available_tokens == 0

        with pytest.raises(RateLimitExceededError):
            limiter.acquire()

        time.sleep(1.1)

        assert limiter.available_tokens == 1
        limiter.acquire()

    def test_tokens_capped_at_burst_size(self):
        """Test that tokens do not exceed burst size."""
        limiter = RateLimiter(config=RateLimitConfig(burst_size=3))
        time.sleep(0.5)
        assert limiter.available_tokens == 3

    def test_try_acquire_returns_bool(self):
        """Test that try_acquire returns success boolean."""
        limiter = RateLimiter(config=RateLimitConfig(burst_size=1))

        assert limiter.try_acquire() is True
        assert limiter.available_tokens == 0

        assert limiter.try_acquire() is False

    def test_thread_safety(self):
        """Test that rate limiter is thread-safe."""
        config = RateLimitConfig(requests_per_minute=1000, burst_size=10)
        limiter = RateLimiter(config=config)

        successes = []
        failures = []

        def worker():
            try:
                limiter.acquire()
                successes.append(1)
            except RateLimitExceededError:
                failures.append(1)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(successes) == 10
        assert len(failures) == 10

    def test_get_wait_time(self):
        """Test wait time calculation."""
        config = RateLimitConfig(requests_per_minute=60, burst_size=2)
        limiter = RateLimiter(config=config)

        limiter.acquire()
        limiter.acquire()

        wait_time = limiter.get_wait_time()
        assert 0.9 <= wait_time <= 1.1

    def test_get_wait_time_zero_when_tokens_available(self):
        """Test wait time is zero when tokens available."""
        limiter = RateLimiter(config=RateLimitConfig(burst_size=5))
        assert limiter.get_wait_time() == 0

    def test_reset(self):
        """Test resetting the rate limiter."""
        limiter = RateLimiter(config=RateLimitConfig(burst_size=3))

        limiter.acquire()
        limiter.acquire()
        limiter.acquire()

        assert limiter.available_tokens == 0

        limiter.reset()
        assert limiter.available_tokens == 3


class TestRateLimiterException:
    """Tests for RateLimitExceededError exception."""

    def test_exception_message(self):
        """Test exception message includes wait time."""
        error = RateLimitExceededError(
            "Rate limit exceeded. Retry after 2.5 seconds.",
            code="RATE_LIMIT_EXCEEDED",
            retry_after=2.5,
        )

        assert "Retry after 2.5 seconds" in str(error)
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert error.retry_after == 2.5

    def test_exception_default_code(self):
        """Test exception has default code."""
        error = RateLimitExceededError("Rate limit exceeded")
        assert error.code == "RATE_LIMIT_EXCEEDED"
