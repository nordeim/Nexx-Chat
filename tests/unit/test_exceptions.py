"""Unit tests for exception hierarchy.

Phase 1: Complete exception hierarchy testing.
"""
import pytest

from neural_terminal.domain.exceptions import (
    APIError,
    BudgetError,
    BudgetExceededError,
    CircuitBreakerOpenError,
    ConfigurationError,
    ConversationNotFoundError,
    EmptyInputError,
    InputTooLongError,
    MessageNotFoundError,
    ModelUnavailableError,
    NeuralTerminalError,
    OpenRouterAPIError,
    RateLimitError,
    ServiceError,
    TokenLimitError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_neural_terminal_error_is_base(self):
        """Test that NeuralTerminalError is the base exception."""
        assert issubclass(CircuitBreakerOpenError, NeuralTerminalError)
        assert issubclass(ValidationError, NeuralTerminalError)
        assert issubclass(APIError, NeuralTerminalError)
        assert issubclass(ServiceError, NeuralTerminalError)
        assert issubclass(BudgetError, NeuralTerminalError)
        assert issubclass(ConfigurationError, NeuralTerminalError)

    def test_open_router_error_inherits_api_error(self):
        """Test OpenRouter errors inherit from APIError."""
        assert issubclass(OpenRouterAPIError, APIError)
        assert issubclass(RateLimitError, OpenRouterAPIError)
        assert issubclass(ModelUnavailableError, OpenRouterAPIError)
        assert issubclass(TokenLimitError, OpenRouterAPIError)

    def test_validation_error_hierarchy(self):
        """Test validation error hierarchy."""
        assert issubclass(InputTooLongError, ValidationError)
        assert issubclass(EmptyInputError, ValidationError)

    def test_service_error_hierarchy(self):
        """Test service error hierarchy."""
        assert issubclass(ConversationNotFoundError, ServiceError)
        assert issubclass(MessageNotFoundError, ServiceError)

    def test_budget_error_hierarchy(self):
        """Test budget error hierarchy."""
        assert issubclass(BudgetExceededError, BudgetError)


class TestErrorCodes:
    """Tests for error codes."""

    def test_circuit_breaker_error_code(self):
        """Test circuit breaker error has correct code."""
        err = CircuitBreakerOpenError("Circuit is open")
        assert err.code == "CIRCUIT_OPEN"
        assert "[CIRCUIT_OPEN]" in str(err)

    def test_input_too_long_error_code(self):
        """Test input too long error has correct code."""
        err = InputTooLongError("Too long", 100, 200)
        assert err.code == "INPUT_TOO_LONG"

    def test_empty_input_error_code(self):
        """Test empty input error has correct code."""
        err = EmptyInputError()
        assert err.code == "EMPTY_INPUT"

    def test_api_error_code_from_status(self):
        """Test API error derives code from status code."""
        err = APIError("Error", status_code=500)
        assert err.code == "HTTP_500"

    def test_token_limit_error_code(self):
        """Test token limit error has correct code."""
        err = TokenLimitError()
        assert err.code == "TOKEN_LIMIT"
        assert err.status_code == 400

    def test_conversation_not_found_error_code(self):
        """Test conversation not found error has correct code."""
        err = ConversationNotFoundError("abc-123")
        assert err.code == "CONVERSATION_NOT_FOUND"

    def test_budget_exceeded_error_code(self):
        """Test budget exceeded error has correct code."""
        err = BudgetExceededError()
        assert err.code == "BUDGET_EXCEEDED"


class TestOpenRouterAPIError:
    """Tests for OpenRouterAPIError."""

    def test_attributes(self):
        """Test OpenRouterAPIError has correct attributes."""
        err = OpenRouterAPIError(
            message="API Error",
            status_code=500,
            response_body='{"error": "internal"}'
        )
        
        assert err.message == "API Error"
        assert err.status_code == 500
        assert err.response_body == '{"error": "internal"}'
        assert err.code == "HTTP_500"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_message(self):
        """Test default error message."""
        err = RateLimitError()
        assert err.message == "Rate limit exceeded"
        assert err.status_code == 429

    def test_retry_after_attribute(self):
        """Test retry_after attribute."""
        err = RateLimitError(retry_after=60)
        assert err.retry_after == 60


class TestModelUnavailableError:
    """Tests for ModelUnavailableError."""

    def test_model_id_attribute(self):
        """Test model_id attribute."""
        err = ModelUnavailableError(model_id="gpt-4")
        assert err.model_id == "gpt-4"
        assert err.status_code == 503


class TestTokenLimitError:
    """Tests for TokenLimitError."""

    def test_token_attributes(self):
        """Test max_tokens and actual_tokens attributes."""
        err = TokenLimitError(
            max_tokens=4096,
            actual_tokens=5000
        )
        assert err.max_tokens == 4096
        assert err.actual_tokens == 5000
        assert err.status_code == 400
        assert err.code == "TOKEN_LIMIT"


class TestInputTooLongError:
    """Tests for InputTooLongError."""

    def test_length_attributes(self):
        """Test length attributes."""
        err = InputTooLongError(
            message="Too long",
            max_length=1000,
            actual_length=1500
        )
        assert err.max_length == 1000
        assert err.actual_length == 1500


class TestConversationNotFoundError:
    """Tests for ConversationNotFoundError."""

    def test_conversation_id_attribute(self):
        """Test conversation_id attribute."""
        err = ConversationNotFoundError("conv-123")
        assert err.conversation_id == "conv-123"
        assert "conv-123" in err.message


class TestBudgetExceededError:
    """Tests for BudgetExceededError."""

    def test_budget_attributes(self):
        """Test accumulated and limit attributes."""
        err = BudgetExceededError(
            accumulated="5.50",
            limit="5.00"
        )
        assert err.accumulated == "5.50"
        assert err.limit == "5.00"
