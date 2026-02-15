"""Error handling and display components.

Provides user-friendly error messages and recovery options.
"""

from typing import Optional, Callable, Any
from enum import Enum, auto

import streamlit as st


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorHandler:
    """Handles error display and recovery in the UI."""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        "CircuitBreakerOpenError": (
            "⚠️ Service temporarily unavailable. "
            "The circuit breaker is open. Please wait a moment and try again."
        ),
        "RateLimitError": (
            "⏱️ Rate limit exceeded. "
            "Please wait a moment before sending more messages."
        ),
        "TokenLimitError": (
            "📏 Message too long. "
            "Please shorten your message or start a new conversation."
        ),
        "ModelUnavailableError": (
            "🤖 Model unavailable. "
            "The selected AI model is currently unavailable. Please try another model."
        ),
        "AuthenticationError": (
            "🔑 Authentication failed. "
            "Please check your API key in settings."
        ),
        "NetworkError": (
            "🌐 Network error. "
            "Please check your internet connection and try again."
        ),
        "BudgetExceededError": (
            "💰 Budget exceeded. "
            "You've reached your budget limit. Please increase it in settings."
        ),
    }
    
    def __init__(self):
        """Initialize error handler."""
        self._last_error: Optional[str] = None
    
    def _get_error_type(self, error: Exception) -> str:
        """Get error type name.
        
        Args:
            error: Exception instance
            
        Returns:
            Error type name
        """
        return type(error).__name__
    
    def _get_user_message(self, error: Exception) -> str:
        """Get user-friendly error message.
        
        Args:
            error: Exception instance
            
        Returns:
            User-friendly message
        """
        error_type = self._get_error_type(error)
        
        # Check for known error types
        if error_type in self.ERROR_MESSAGES:
            return self.ERROR_MESSAGES[error_type]
        
        # Check for exception message
        if str(error):
            return f"⚠️ {str(error)}"
        
        # Default message
        return f"⚠️ An unexpected error occurred: {error_type}"
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity.
        
        Args:
            error: Exception instance
            
        Returns:
            Error severity level
        """
        error_type = self._get_error_type(error)
        
        critical_errors = [
            "AuthenticationError",
            "BudgetExceededError",
        ]
        
        warning_errors = [
            "RateLimitError",
            "TokenLimitError",
        ]
        
        info_errors = [
            "CircuitBreakerOpenError",
        ]
        
        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in warning_errors:
            return ErrorSeverity.WARNING
        elif error_type in info_errors:
            return ErrorSeverity.INFO
        else:
            return ErrorSeverity.ERROR
    
    def show_error(
        self,
        error: Exception,
        recovery_action: Optional[Callable[[], Any]] = None,
        recovery_label: str = "Retry",
    ) -> None:
        """Display error message with optional recovery action.
        
        Args:
            error: Exception to display
            recovery_action: Optional recovery callback
            recovery_label: Label for recovery button
        """
        message = self._get_user_message(error)
        severity = self._determine_severity(error)
        
        self._last_error = message
        
        # Display based on severity
        if severity == ErrorSeverity.CRITICAL:
            st.error(message)
        elif severity == ErrorSeverity.WARNING:
            st.warning(message)
        elif severity == ErrorSeverity.INFO:
            st.info(message)
        else:
            st.error(message)
        
        # Show recovery button if provided
        if recovery_action:
            if st.button(recovery_label, key=f"retry_{id(error)}"):
                recovery_action()
    
    def show_error_message(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> None:
        """Display raw error message.
        
        Args:
            message: Error message to display
            severity: Error severity level
        """
        self._last_error = message
        
        if severity == ErrorSeverity.CRITICAL:
            st.error(message)
        elif severity == ErrorSeverity.WARNING:
            st.warning(message)
        elif severity == ErrorSeverity.INFO:
            st.info(message)
        else:
            st.error(message)
    
    def show_startup_error(self, message: str) -> None:
        """Display startup/configuration error.
        
        Args:
            message: Error message
        """
        st.error(f"🚨 Startup Error")
        st.markdown(f"```\n{message}\n```")
        
        st.markdown("""
        **Please check:**
        1. Your API key is configured correctly
        2. Database permissions are correct
        3. Required dependencies are installed
        """)
        
        if st.button("🔄 Retry Initialization"):
            st.rerun()
    
    def show_validation_error(self, field: str, message: str) -> None:
        """Display form validation error.
        
        Args:
            field: Field name
            message: Validation message
        """
        st.warning(f"⚠️ {field}: {message}")
    
    def show_success(self, message: str) -> None:
        """Display success message.
        
        Args:
            message: Success message
        """
        st.success(f"✅ {message}")
    
    def show_info(self, message: str) -> None:
        """Display info message.
        
        Args:
            message: Info message
        """
        st.info(f"ℹ️ {message}")
    
    def show_warning(self, message: str) -> None:
        """Display warning message.
        
        Args:
            message: Warning message
        """
        st.warning(f"⚠️ {message}")
    
    def clear_error(self) -> None:
        """Clear last error."""
        self._last_error = None
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error
    
    def has_error(self) -> bool:
        """Check if there's an active error."""
        return self._last_error is not None


class NotificationManager:
    """Manages toast notifications and alerts."""
    
    def toast(self, message: str) -> None:
        """Show toast notification.
        
        Args:
            message: Toast message
        """
        st.toast(message)
    
    def success(self, message: str) -> None:
        """Show success toast.
        
        Args:
            message: Success message
        """
        st.toast(f"✅ {message}")
    
    def error(self, message: str) -> None:
        """Show error toast.
        
        Args:
            message: Error message
        """
        st.toast(f"❌ {message}")
    
    def warning(self, message: str) -> None:
        """Show warning toast.
        
        Args:
            message: Warning message
        """
        st.toast(f"⚠️ {message}")
    
    def info(self, message: str) -> None:
        """Show info toast.
        
        Args:
            message: Info message
        """
        st.toast(f"ℹ️ {message}")


# Convenience functions
def show_error(error: Exception, **kwargs) -> None:
    """Show error with default handler.
    
    Args:
        error: Exception to display
        **kwargs: Additional options
    """
    handler = ErrorHandler()
    handler.show_error(error, **kwargs)


def show_success(message: str) -> None:
    """Show success message.
    
    Args:
        message: Success message
    """
    handler = ErrorHandler()
    handler.show_success(message)


def show_warning(message: str) -> None:
    """Show warning message.
    
    Args:
        message: Warning message
    """
    handler = ErrorHandler()
    handler.show_warning(message)


def show_info(message: str) -> None:
    """Show info message.
    
    Args:
        message: Info message
    """
    handler = ErrorHandler()
    handler.show_info(message)


def toast(message: str) -> None:
    """Show toast notification.
    
    Args:
        message: Toast message
    """
    manager = NotificationManager()
    manager.toast(message)
