"""Tests for InputSanitizer - TDD Red Phase.
These tests define the expected behavior for input sanitization
before storing user messages in the database.
"""
import pytest
class TestInputSanitizer:
    """Test suite for InputSanitizer class."""
    def test_sanitize_removes_null_bytes(self):
        """Null bytes should be removed from input."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize("Hello\x00World")
        assert result == "HelloWorld"
        assert "\x00" not in result
    def test_sanitize_strips_control_characters(self):
        """Control characters except newline and tab should be stripped."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize("Hello\x01\x02\x03World\nNewLine\tTab")
        assert "HelloWorld" in result
        assert "\n" in result
        assert "\t" in result
    def test_sanitize_trims_whitespace(self):
        """Leading and trailing whitespace should be trimmed."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize("   Hello World   ")
        assert result == "Hello World"
    def test_sanitize_empty_string_returns_empty(self):
        """Empty string should return empty string."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize("")
        assert result == ""
    def test_sanitize_none_raises_error(self):
        """None input should raise ValidationError."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        from neural_terminal.domain.exceptions import ValidationError
        sanitizer = InputSanitizer()
        with pytest.raises(ValidationError):
            sanitizer.sanitize(None)
    def test_sanitize_max_length_truncates(self):
        """Content exceeding max length should be truncated."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer(max_length=10)
        result = sanitizer.sanitize("This is a very long message")
        assert len(result) == 10
    def test_sanitize_default_max_length(self):
        """Default max length should be 32000 characters."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        long_string = "a" * 40000
        result = sanitizer.sanitize(long_string)
        assert len(result) == 32000
    def test_sanitize_html_escaping(self):
        """Dangerous HTML entities should be escaped."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize("<script>alert('xss')</script>")
        assert "<script>" not in result
    def test_sanitize_multiline_preserves_structure(self):
        """Multiline content should preserve line structure."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize("Line 1\nLine 2\nLine 3")
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    def test_sanitize_returns_sanitized_result_object(self):
        """Sanitize should return a SanitizedResult object with metadata."""
        from neural_terminal.infrastructure.input_sanitizer import (
            InputSanitizer, SanitizedResult
        )
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_with_metadata("  Hello World  ")
        assert isinstance(result, SanitizedResult)
        assert result.content == "Hello World"
        assert result.original_length == 15
        assert result.sanitized_length == 11
        assert result.was_modified is True
    def test_sanitize_detects_sql_injection_patterns(self):
        """Common SQL injection patterns should be flagged."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_with_metadata("'; DROP TABLE users; --")
        assert result.has_suspicious_patterns is True
    def test_sanitize_detects_xss_patterns(self):
        """Common XSS patterns should be flagged."""
        from neural_terminal.infrastructure.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_with_metadata(
            "<img src=x onerror=alert('xss')>"
        )
        assert result.has_suspicious_patterns is True
    def test_sanitize_configurable_strictness(self):
        """Sanitizer should support configurable strictness levels."""
        from neural_terminal.infrastructure.input_sanitizer import (
            InputSanitizer, SanitizationLevel
        )
        sanitizer = InputSanitizer(level=SanitizationLevel.STRICT)
        result = sanitizer.sanitize("<b>Hello</b>")
        assert "<b>" not in result
