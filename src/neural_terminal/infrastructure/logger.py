"""Logger factory for Neural Terminal.

Provides pre-configured structlog loggers with common context.
"""

import structlog
from typing import Any, Optional


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a pre-configured logger instance.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured structlog BoundLogger with common context

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id=123)
    """
    logger = structlog.get_logger(name)
    return logger


class LoggerMixin:
    """Mixin class to add logger to any class.

    Automatically creates a logger named after the class module.

    Example:
        >>> class MyService(LoggerMixin):
        ...     def do_something(self):
        ...         self.logger.info("Doing something")
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize logger mixin."""
        super().__init__(*args, **kwargs)
        self._logger: Optional[structlog.stdlib.BoundLogger] = None

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance (lazy initialization)."""
        if self._logger is None:
            # Get the module name from the class
            module_name = self.__class__.__module__
            self._logger = get_logger(module_name)
        return self._logger
