"""UI Components for Neural Terminal.

Provides terminal aesthetic components for Streamlit applications.
"""

from .themes import Theme, ThemeRegistry, ThemeMode, DEFAULT_THEME
from .styles import (
    StyleManager,
    inject_css,
    switch_theme,
    generate_all_css,
)
from .message_renderer import (
    MessageRenderer,
    MessageSanitizer,
    StreamingMessageRenderer,
    render_message,
    sanitize_html,
    escape_html,
)
from .error_handler import (
    ErrorHandler,
    NotificationManager,
    ErrorSeverity,
    show_error,
    show_success,
    show_warning,
    show_info,
    toast,
)

__all__ = [
    # Themes
    "Theme",
    "ThemeRegistry", 
    "ThemeMode",
    "DEFAULT_THEME",
    # Styles
    "StyleManager",
    "inject_css",
    "switch_theme",
    "generate_all_css",
    # Message Rendering
    "MessageRenderer",
    "MessageSanitizer",
    "StreamingMessageRenderer",
    "render_message",
    "sanitize_html",
    "escape_html",
    # Error Handling
    "ErrorHandler",
    "NotificationManager",
    "ErrorSeverity",
    "show_error",
    "show_success",
    "show_warning",
    "show_info",
    "toast",
]
