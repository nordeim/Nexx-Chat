"""Tests for error handler components."""

import pytest
from unittest.mock import Mock, patch

from neural_terminal.components.error_handler import (
    ErrorSeverity,
    ErrorHandler,
    NotificationManager,
    show_error,
    show_success,
    show_warning,
    show_info,
    toast,
)


class TestErrorSeverity:
    """Tests for ErrorSeverity enum."""
    
    def test_severity_levels(self):
        """Severity levels exist."""
        assert ErrorSeverity.INFO.name == "INFO"
        assert ErrorSeverity.WARNING.name == "WARNING"
        assert ErrorSeverity.ERROR.name == "ERROR"
        assert ErrorSeverity.CRITICAL.name == "CRITICAL"


class TestErrorHandler:
    """Tests for ErrorHandler."""
    
    def test_init(self):
        """Handler initializes."""
        handler = ErrorHandler()
        
        assert handler.last_error is None
        assert handler.has_error() is False
    
    def test_get_error_type(self):
        """Extract error type name."""
        handler = ErrorHandler()
        
        error = ValueError("test")
        error_type = handler._get_error_type(error)
        
        assert error_type == "ValueError"
    
    def test_get_user_message_known_error(self):
        """Get message for known error type."""
        handler = ErrorHandler()
        
        # Create a mock exception with CircuitBreakerOpenError name
        error = type("CircuitBreakerOpenError", (Exception,), {})()
        message = handler._get_user_message(error)
        
        assert "circuit breaker" in message.lower()
    
    def test_get_user_message_with_text(self):
        """Get message from exception text."""
        handler = ErrorHandler()
        
        error = ValueError("Something went wrong")
        message = handler._get_user_message(error)
        
        assert "Something went wrong" in message
    
    def test_get_user_message_default(self):
        """Get default message for unknown errors."""
        handler = ErrorHandler()
        
        error = RuntimeError()
        message = handler._get_user_message(error)
        
        assert "unexpected error" in message.lower()
    
    def test_determine_severity_critical(self):
        """Critical errors detected."""
        handler = ErrorHandler()
        
        error = type("AuthenticationError", (Exception,), {})()
        severity = handler._determine_severity(error)
        
        assert severity == ErrorSeverity.CRITICAL
    
    def test_determine_severity_warning(self):
        """Warning errors detected."""
        handler = ErrorHandler()
        
        error = type("RateLimitError", (Exception,), {})()
        severity = handler._determine_severity(error)
        
        assert severity == ErrorSeverity.WARNING
    
    def test_determine_severity_error(self):
        """Regular errors detected."""
        handler = ErrorHandler()
        
        error = ValueError("test")
        severity = handler._determine_severity(error)
        
        assert severity == ErrorSeverity.ERROR
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_error_critical(self, mock_st):
        """Show critical error."""
        handler = ErrorHandler()
        
        error = type("AuthenticationError", (Exception,), {})()
        handler.show_error(error)
        
        mock_st.error.assert_called()
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_error_warning(self, mock_st):
        """Show warning error."""
        handler = ErrorHandler()
        
        error = type("RateLimitError", (Exception,), {})()
        handler.show_error(error)
        
        mock_st.warning.assert_called()
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_error_with_recovery(self, mock_st):
        """Show error with recovery button."""
        mock_st.button.return_value = True
        handler = ErrorHandler()
        
        callback = Mock()
        error = ValueError("test")
        handler.show_error(error, recovery_action=callback, recovery_label="Try Again")
        
        # Check button was called with correct label
        mock_st.button.assert_called()
        call_args = mock_st.button.call_args
        assert call_args[0][0] == "Try Again"
        # Verify callback was triggered
        callback.assert_called()
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_error_message(self, mock_st):
        """Show raw error message."""
        handler = ErrorHandler()
        
        handler.show_error_message("Custom error", ErrorSeverity.WARNING)
        
        mock_st.warning.assert_called()
        assert handler.last_error == "Custom error"
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_startup_error(self, mock_st):
        """Show startup error."""
        handler = ErrorHandler()
        
        handler.show_startup_error("Database connection failed")
        
        mock_st.error.assert_called()
        mock_st.markdown.assert_called()
        mock_st.button.assert_called_with("🔄 Retry Initialization")
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_validation_error(self, mock_st):
        """Show validation error."""
        handler = ErrorHandler()
        
        handler.show_validation_error("API Key", "Cannot be empty")
        
        mock_st.warning.assert_called()
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_success(self, mock_st):
        """Show success message."""
        handler = ErrorHandler()
        
        handler.show_success("Settings saved")
        
        mock_st.success.assert_called_with("✅ Settings saved")
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_info(self, mock_st):
        """Show info message."""
        handler = ErrorHandler()
        
        handler.show_info("Processing...")
        
        mock_st.info.assert_called_with("ℹ️ Processing...")
    
    @patch("neural_terminal.components.error_handler.st")
    def test_show_warning(self, mock_st):
        """Show warning message."""
        handler = ErrorHandler()
        
        handler.show_warning("Low budget")
        
        mock_st.warning.assert_called_with("⚠️ Low budget")
    
    def test_clear_error(self):
        """Clear last error."""
        handler = ErrorHandler()
        
        handler.show_error_message("Test error")
        assert handler.has_error() is True
        
        handler.clear_error()
        
        assert handler.last_error is None
        assert handler.has_error() is False


class TestNotificationManager:
    """Tests for NotificationManager."""
    
    @patch("neural_terminal.components.error_handler.st")
    def test_toast(self, mock_st):
        """Show toast notification."""
        manager = NotificationManager()
        
        manager.toast("Hello")
        
        mock_st.toast.assert_called_with("Hello")
    
    @patch("neural_terminal.components.error_handler.st")
    def test_success(self, mock_st):
        """Show success toast."""
        manager = NotificationManager()
        
        manager.success("Done")
        
        mock_st.toast.assert_called_with("✅ Done")
    
    @patch("neural_terminal.components.error_handler.st")
    def test_error(self, mock_st):
        """Show error toast."""
        manager = NotificationManager()
        
        manager.error("Failed")
        
        mock_st.toast.assert_called_with("❌ Failed")
    
    @patch("neural_terminal.components.error_handler.st")
    def test_warning(self, mock_st):
        """Show warning toast."""
        manager = NotificationManager()
        
        manager.warning("Caution")
        
        mock_st.toast.assert_called_with("⚠️ Caution")
    
    @patch("neural_terminal.components.error_handler.st")
    def test_info(self, mock_st):
        """Show info toast."""
        manager = NotificationManager()
        
        manager.info("Note")
        
        mock_st.toast.assert_called_with("ℹ️ Note")


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @patch("neural_terminal.components.error_handler.ErrorHandler")
    def test_show_error(self, mock_handler_class):
        """show_error convenience function."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        error = ValueError("test")
        show_error(error)
        
        mock_handler.show_error.assert_called_with(error)
    
    @patch("neural_terminal.components.error_handler.ErrorHandler")
    def test_show_success(self, mock_handler_class):
        """show_success convenience function."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        show_success("Done")
        
        mock_handler.show_success.assert_called_with("Done")
    
    @patch("neural_terminal.components.error_handler.ErrorHandler")
    def test_show_warning(self, mock_handler_class):
        """show_warning convenience function."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        show_warning("Caution")
        
        mock_handler.show_warning.assert_called_with("Caution")
    
    @patch("neural_terminal.components.error_handler.ErrorHandler")
    def test_show_info(self, mock_handler_class):
        """show_info convenience function."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        show_info("Note")
        
        mock_handler.show_info.assert_called_with("Note")
    
    @patch("neural_terminal.components.error_handler.NotificationManager")
    def test_toast(self, mock_manager_class):
        """toast convenience function."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        toast("Hello")
        
        mock_manager.toast.assert_called_with("Hello")
