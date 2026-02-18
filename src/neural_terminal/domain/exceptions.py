"""Domain exceptions for Neural Terminal.

Provides a comprehensive error hierarchy for the application.
All exceptions inherit from NeuralTerminalError for consistent handling.
"""

from typing import Optional


class NeuralTerminalError(Exception):
    """Base exception for all Neural Terminal errors.

    Attributes:
        message: Human-readable error description
        code: Machine-readable error code (e.g., 'HTTP_429')
    """

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(NeuralTerminalError):
    """Raised when there's an error in application configuration."""

    pass


# ============================================================================
# Validation Errors
# ============================================================================


class ValidationError(NeuralTerminalError):
    """Base class for validation errors."""

    pass


class InputTooLongError(ValidationError):
    """Raised when user input exceeds maximum length."""

    def __init__(self, message: str, max_length: int, actual_length: int):
        super().__init__(message, code="INPUT_TOO_LONG")
        self.max_length = max_length
        self.actual_length = actual_length


class EmptyInputError(ValidationError):
    """Raised when user input is empty or whitespace-only."""

    def __init__(self, message: str = "Input cannot be empty"):
        super().__init__(message, code="EMPTY_INPUT")


# ============================================================================
# Circuit Breaker Errors
# ============================================================================


class CircuitBreakerOpenError(NeuralTerminalError):
    """Raised when circuit breaker is open and operation is rejected.

    The circuit breaker prevents cascading failures by rejecting requests
    when the downstream service is failing.
    """

    def __init__(self, message: str):
        super().__init__(message, code="CIRCUIT_OPEN")


# ============================================================================
# API Errors
# ============================================================================


class APIError(NeuralTerminalError):
    """Base class for API-related errors."""

    def __init__(self, message: str, status_code: int, code: Optional[str] = None):
        super().__init__(message, code=code or f"HTTP_{status_code}")
        self.status_code = status_code


class OpenRouterAPIError(APIError):
    """Raised when OpenRouter API returns an error response.

    Attributes:
        status_code: HTTP status code
        response_body: Raw response body for debugging
    """

    def __init__(
        self, message: str, status_code: int, response_body: Optional[str] = None
    ):
        super().__init__(message, status_code)
        self.response_body = response_body


class RateLimitError(OpenRouterAPIError):
    """Raised when OpenRouter returns 429 Too Many Requests."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after  # Seconds to wait before retry


class ModelUnavailableError(OpenRouterAPIError):
    """Raised when requested model returns 503 Service Unavailable."""

    def __init__(
        self,
        message: str = "Model temporarily unavailable",
        model_id: Optional[str] = None,
    ):
        super().__init__(message, status_code=503)
        self.model_id = model_id


class TokenLimitError(OpenRouterAPIError):
    """Raised when context exceeds model's token limit (400 error)."""

    def __init__(
        self,
        message: str = "Context too long",
        max_tokens: Optional[int] = None,
        actual_tokens: Optional[int] = None,
    ):
        super().__init__(message, status_code=400)
        self.code = "TOKEN_LIMIT"  # Override the code after init
        self.max_tokens = max_tokens
        self.actual_tokens = actual_tokens


# ============================================================================
# Service Errors
# ============================================================================


class ServiceError(NeuralTerminalError):
    """Base class for service-layer errors."""

    pass


class ConversationNotFoundError(ServiceError):
    """Raised when requested conversation doesn't exist."""

    def __init__(self, conversation_id: str):
        super().__init__(
            f"Conversation {conversation_id} not found", code="CONVERSATION_NOT_FOUND"
        )
        self.conversation_id = conversation_id


class MessageNotFoundError(ServiceError):
    """Raised when requested message doesn't exist."""

    pass


# ============================================================================
# Budget Errors
# ============================================================================


class BudgetError(NeuralTerminalError):
    """Base class for budget-related errors."""

    pass


class BudgetExceededError(BudgetError):
    """Raised when conversation cost exceeds budget limit."""

    def __init__(
        self,
        message: str = "Budget exceeded",
        accumulated: Optional[str] = None,
        limit: Optional[str] = None,
    ):
        super().__init__(message, code="BUDGET_EXCEEDED")
        self.accumulated = accumulated
        self.limit = limit


# ============================================================================
# Rate Limiter Errors
# ============================================================================


class RateLimitExceededError(NeuralTerminalError):
    """Raised when client-side rate limit is exceeded.

    This is different from RateLimitError which is for API-level
    rate limiting (HTTP 429 responses).

    Attributes:
        retry_after: Seconds to wait before retrying
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        code: str = "RATE_LIMIT_EXCEEDED",
        retry_after: Optional[float] = None,
    ):
        super().__init__(message, code=code)
        self.retry_after = retry_after
