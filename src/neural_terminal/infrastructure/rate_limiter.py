"""Rate limiter implementation using token bucket algorithm.

Provides client-side rate limiting to protect against excessive API usage.
"""

import threading
import time
from dataclasses import dataclass
from typing import Optional

from neural_terminal.domain.exceptions import RateLimitExceededError


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter.

    Attributes:
        requests_per_minute: Maximum requests allowed per minute
        burst_size: Maximum burst size (bucket capacity)
    """

    requests_per_minute: int = 20
    burst_size: int = 5

    def __post_init__(self):
        """Validate configuration values."""
        if self.requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        if self.burst_size <= 0:
            raise ValueError("burst_size must be positive")


class RateLimiter:
    """Token bucket rate limiter implementation.

    Thread-safe rate limiter that allows bursts up to a configured limit,
    then throttles requests to a steady rate.

    Example:
        limiter = RateLimiter()
        limiter.acquire()  # Blocks if rate limit exceeded

        if limiter.try_acquire():
            # Process request
            pass
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration (uses defaults if None)
        """
        self._config = config or RateLimitConfig()
        self._tokens = self._config.burst_size
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    def _replenish_tokens(self) -> None:
        """Replenish tokens based on time elapsed.

        Called internally to update token count before checking.
        """
        now = time.monotonic()
        elapsed = now - self._last_update

        # Calculate tokens to add: (requests_per_minute / 60) * elapsed
        tokens_to_add = (self._config.requests_per_minute / 60.0) * elapsed

        self._tokens = min(self._config.burst_size, self._tokens + tokens_to_add)
        self._last_update = now

    def acquire(self) -> None:
        """Acquire a token, blocking if rate limit exceeded.

        Raises:
            RateLimitExceededError: If no tokens available
        """
        with self._lock:
            self._replenish_tokens()

            if self._tokens < 1:
                wait_time = self._calculate_wait_time_unlocked()
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Retry after {wait_time:.1f} seconds.",
                    code="RATE_LIMIT_EXCEEDED",
                    retry_after=wait_time,
                )

            self._tokens -= 1

    def try_acquire(self) -> bool:
        """Try to acquire a token without blocking.

        Returns:
            True if token acquired, False if rate limited
        """
        with self._lock:
            self._replenish_tokens()

            if self._tokens < 1:
                return False

            self._tokens -= 1
            return True

    @property
    def available_tokens(self) -> int:
        """Get current number of available tokens.

        Returns:
            Number of tokens currently available (0 to burst_size)
        """
        with self._lock:
            self._replenish_tokens()
            return int(self._tokens)

    def _calculate_wait_time_unlocked(self) -> float:
        """Calculate seconds to wait for next token.

        Assumes lock is already held.

        Returns:
            Seconds to wait for next token
        """
        if self._tokens >= 1:
            return 0.0

        # Time to generate one token
        seconds_per_token = 60.0 / self._config.requests_per_minute
        tokens_needed = 1 - self._tokens
        return tokens_needed * seconds_per_token

    def get_wait_time(self) -> float:
        """Calculate seconds to wait for next token.

        Returns:
            Seconds to wait (0 if tokens available)
        """
        with self._lock:
            self._replenish_tokens()
            return self._calculate_wait_time_unlocked()

    def reset(self) -> None:
        """Reset rate limiter to initial state.

        Useful for testing or after rate limit errors.
        """
        with self._lock:
            self._tokens = self._config.burst_size
            self._last_update = time.monotonic()
