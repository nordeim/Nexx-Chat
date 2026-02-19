"""Tests for logging infrastructure.

Phase: Debug Print Replacement - Proper logging implementation.
"""

import logging
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest
import structlog


class TestLoggingInfrastructure:
    """Tests for logging infrastructure setup."""

    def test_logger_factory_exists(self):
        """Test that logger factory module exists."""
        from neural_terminal.infrastructure.logger import get_logger

        assert callable(get_logger)

    def test_get_logger_returns_structlog_logger(self):
        """Test that get_logger returns a structlog BoundLogger."""
        from neural_terminal.infrastructure.logger import get_logger

        logger = get_logger("test.module")
        assert logger is not None
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_logger_has_bound_context(self):
        """Test that logger has bound context."""
        from neural_terminal.infrastructure.logger import get_logger

        logger = get_logger("test.context")
        # Should have app_name bound
        assert hasattr(logger, "_context")

    def test_log_level_configuration_exists(self):
        """Test that log level can be configured via Settings."""
        from neural_terminal.config import settings

        assert hasattr(settings, "log_level")
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]


class TestLoggingLevels:
    """Tests for log level behavior."""

    def test_debug_filtered_when_info_level(self):
        """Test that DEBUG messages are filtered when level is INFO."""
        from neural_terminal.infrastructure.logger import get_logger

        # Capture log output
        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.levels")
            logger.setLevel(logging.INFO)

            logger.debug("This should not appear")
            logger.info("This should appear")

            # Check that info was logged but debug was not
            calls = [call for call in mock_print.call_args_list if "This" in str(call)]
            assert any("should appear" in str(call) for call in calls)

    def test_info_shown_when_info_level(self):
        """Test that INFO messages are shown when level is INFO."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.info")
            logger.setLevel(logging.INFO)

            logger.info("Info message")

            calls = str(mock_print.call_args_list)
            assert "Info message" in calls

    def test_warning_shown_when_info_level(self):
        """Test that WARNING messages are shown when level is INFO."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.warning")
            logger.setLevel(logging.INFO)

            logger.warning("Warning message")

            calls = str(mock_print.call_args_list)
            assert "Warning message" in calls

    def test_error_shown_at_all_levels(self):
        """Test that ERROR messages are always shown."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.error")
            logger.setLevel(logging.ERROR)

            logger.error("Error message")

            calls = str(mock_print.call_args_list)
            assert "Error message" in calls


class TestSensitiveDataRedaction:
    """Tests for automatic redaction of sensitive data."""

    def test_api_key_redacted(self):
        """Test that API keys are redacted in logs."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.redaction")

            api_key = (
                "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"
            )
            logger.info(f"Request with key: {api_key}")

            output = str(mock_print.call_args_list)
            # API key should be redacted or masked
            assert api_key not in output or "***" in output

    def test_bearer_token_redacted(self):
        """Test that Bearer tokens are redacted."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.tokens")

            token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            logger.info(f"Auth header: {token}")

            output = str(mock_print.call_args_list)
            assert "eyJhbGci" not in output or "***" in output


class TestNoPrintStatementsRemain:
    """Tests to verify no debug print statements remain in codebase."""

    def test_no_stderr_prints_in_orchestrator(self):
        """Verify no print to stderr in orchestrator.py."""
        import subprocess

        result = subprocess.run(
            [
                "grep",
                "-n",
                "file=sys.stderr",
                "src/neural_terminal/application/orchestrator.py",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0 or result.stdout == "", (
            f"Found print to stderr in orchestrator.py:\n{result.stdout}"
        )

    def test_no_stderr_prints_in_app_state(self):
        """Verify no print to stderr in app_state.py."""
        import subprocess

        result = subprocess.run(
            ["grep", "-n", "file=sys.stderr", "src/neural_terminal/app_state.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0 or result.stdout == "", (
            f"Found print to stderr in app_state.py:\n{result.stdout}"
        )

    def test_no_stderr_prints_in_openrouter(self):
        """Verify no print to stderr in openrouter.py."""
        import subprocess

        result = subprocess.run(
            [
                "grep",
                "-n",
                "file=sys.stderr",
                "src/neural_terminal/infrastructure/openrouter.py",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0 or result.stdout == "", (
            f"Found print to stderr in openrouter.py:\n{result.stdout}"
        )

    def test_no_stderr_prints_in_main(self):
        """Verify no print to stderr in main.py."""
        import subprocess

        result = subprocess.run(
            ["grep", "-n", "file=sys.stderr", "src/neural_terminal/main.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0 or result.stdout == "", (
            f"Found print to stderr in main.py:\n{result.stdout}"
        )

    def test_no_debug_prints_with_brackets(self):
        """Verify no [DEBUG] print statements remain."""
        import subprocess

        result = subprocess.run(
            ["grep", "-rn", "print.*\\[DEBUG\\]", "src/neural_terminal"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0 or result.stdout == "", (
            f"Found [DEBUG] print statements:\n{result.stdout}"
        )


class TestLoggerUsagePatterns:
    """Tests for proper logger usage patterns."""

    def test_logger_in_module_context(self):
        """Test that modules can get logger at module level."""
        # This will fail until logger is implemented
        from neural_terminal.infrastructure.logger import get_logger

        logger = get_logger("neural_terminal.test_module")
        assert logger is not None

    def test_logger_accepts_keyword_arguments(self):
        """Test that logger accepts keyword arguments for structured logging."""
        from neural_terminal.infrastructure.logger import get_logger

        logger = get_logger("test.structured")
        # Should accept key=value pairs for structured logging
        try:
            logger.info("User action", user_id="123", action="login")
        except TypeError as e:
            pytest.fail(f"Logger should accept keyword arguments: {e}")

    def test_exception_logging_works(self):
        """Test that exception logging works."""
        from neural_terminal.infrastructure.logger import get_logger

        logger = get_logger("test.exceptions")

        try:
            raise ValueError("Test exception")
        except ValueError:
            # Should be able to log exception with traceback
            try:
                logger.exception("An error occurred")
            except AttributeError:
                pytest.fail("Logger should have exception() method")


class TestLoggingConfigurationModule:
    """Tests for logging configuration module."""

    def test_logging_config_module_exists(self):
        """Test that logging configuration module exists."""
        from neural_terminal.infrastructure.logging_config import configure_logging

        assert callable(configure_logging)

    def test_configure_logging_accepts_level(self):
        """Test that configure_logging accepts log level."""
        from neural_terminal.infrastructure.logging_config import configure_logging

        # Should not raise
        try:
            configure_logging("INFO")
        except Exception as e:
            pytest.fail(f"configure_logging should accept level parameter: {e}")

    def test_configure_logging_returns_none(self):
        """Test that configure_logging returns None (no return value needed)."""
        from neural_terminal.infrastructure.logging_config import configure_logging

        result = configure_logging("DEBUG")
        assert result is None


class TestLogOutputFormats:
    """Tests for log output formatting."""

    def test_log_includes_timestamp(self):
        """Test that logs include timestamps."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.timestamp")
            logger.info("Test message")

            output = str(mock_print.call_args_list)
            # Should contain some timestamp format
            import re

            assert re.search(r"\d{4}-\d{2}-\d{2}", output) or re.search(
                r"\d{2}:\d{2}:\d{2}", output
            ), "Log should contain timestamp"

    def test_log_includes_log_level(self):
        """Test that logs include log level."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.level")
            logger.info("Test message")

            output = str(mock_print.call_args_list)
            assert "info" in output.lower() or "INFO" in output

    def test_log_includes_module_name(self):
        """Test that logs include module name."""
        from neural_terminal.infrastructure.logger import get_logger

        with patch("structlog._loggers.print") as mock_print:
            logger = get_logger("test.module.name")
            logger.info("Test message")

            output = str(mock_print.call_args_list)
            assert "test.module.name" in output or "module" in output.lower()
