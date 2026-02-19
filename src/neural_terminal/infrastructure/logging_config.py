"""Logging configuration for Neural Terminal.

Provides structured logging with structlog, supporting both console
and JSON output formats. Automatically redacts sensitive data.
"""

import logging
import sys
from typing import Any, Dict, List

import structlog
from structlog.stdlib import filter_by_level


def redact_sensitive_data(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Redact sensitive data from log messages.

    Looks for and masks:
    - API keys (nvapi-*, sk-*, etc.)
    - Bearer tokens
    - Passwords
    - Private keys
    """
    import re

    # Patterns to redact
    patterns = [
        (r"nvapi-[a-zA-Z0-9_-]+", "***API_KEY***"),
        (r"sk-[a-zA-Z0-9_-]+", "***API_KEY***"),
        (
            r"Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
            "Bearer ***TOKEN***",
        ),
        (r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+', "password=***REDACTED***"),
        (r'api_key["\']?\s*[:=]\s*["\']?[^"\'\s]+', "api_key=***REDACTED***"),
    ]

    # Check event message
    if "event" in event_dict and isinstance(event_dict["event"], str):
        for pattern, replacement in patterns:
            event_dict["event"] = re.sub(pattern, replacement, event_dict["event"])

    # Check other string fields
    for key, value in event_dict.items():
        if isinstance(value, str) and key != "event":
            for pattern, replacement in patterns:
                event_dict[key] = re.sub(pattern, replacement, value)

    return event_dict


def add_timestamp(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add ISO format timestamp to log events."""
    from datetime import datetime

    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def configure_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Configure structlog for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: If True, output JSON; if False, pretty console format
    """
    # Map string level to logging level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    level = level_map.get(log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
    )

    # Build processor chain
    shared_processors: List[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        redact_sensitive_data,
    ]

    if json_format:
        # JSON format for production
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        # Pretty console format for development
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set level on root logger
    logging.getLogger().setLevel(level)
