"""Input sanitization for Neural Terminal.
Provides secure input handling before storing user messages in the database.
Prevents stored XSS, handles control characters, and validates input.
"""
import html
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
from neural_terminal.domain.exceptions import ValidationError
class SanitizationLevel(Enum):
    """Sanitization strictness levels."""
    PERMISSIVE = auto()  # Allow most content
    NORMAL = auto()      # Default sanitization
    STRICT = auto()      # Maximum sanitization
@dataclass
class SanitizedResult:
    """Result of sanitization with metadata.
    
    Attributes:
        content: The sanitized content
        original_length: Length of original input
        sanitized_length: Length of sanitized output
        was_modified: Whether any modifications were made
        has_suspicious_patterns: Whether suspicious patterns were detected
        warnings: List of warning messages about detected patterns
    """
    content: str
    original_length: int
    sanitized_length: int
    was_modified: bool
    has_suspicious_patterns: bool = False
    warnings: List[str] = field(default_factory=list)
class InputSanitizer:
    """Sanitizes user input before storage.
    
    Provides multiple layers of sanitization:
    - Removes null bytes and control characters
    - Normalizes unicode to NFC form
    - Trims and collapses whitespace
    - Escapes dangerous HTML entities
    - Detects suspicious patterns (SQL injection, XSS)
    - Truncates to maximum length
    """
    
    DEFAULT_MAX_LENGTH = 32000
    
    SQL_INJECTION_PATTERNS = [
        r"';\s*DROP\s+TABLE",
        r"--\s*$",
        r"'\s*OR\s+'",
        r"'\s*AND\s+'",
        r";\s*DELETE\s+FROM",
        r";\s*INSERT\s+INTO",
        r";\s*UPDATE\s+\w+\s+SET",
        r"UNION\s+SELECT",
        r"EXEC\s*\(",
        r"xp_cmdshell",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript\s*:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"expression\s*\(",
        r"vbscript\s*:",
    ]
    
    def __init__(
        self,
        max_length: int = DEFAULT_MAX_LENGTH,
        level: SanitizationLevel = SanitizationLevel.NORMAL
    ):
        """Initialize sanitizer with configuration.
        
        Args:
            max_length: Maximum allowed content length
            level: Sanitization strictness level
        """
        self.max_length = max_length
        self.level = level
        self._sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self._xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
    
    def sanitize(self, content: Optional[str]) -> str:
        """Sanitize input string.
        
        Args:
            content: Input string to sanitize
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If content is None
        """
        if content is None:
            raise ValidationError("Input cannot be None", code="NULL_INPUT")
        
        if not isinstance(content, str):
            content = str(content)
        
        # Remove null bytes
        content = content.replace('\x00', '')
        
        # Strip control characters except newline and tab
        content = self._strip_control_chars(content)
        
        # Normalize unicode to NFC
        content = unicodedata.normalize('NFC', content)
        
        # Trim leading/trailing whitespace
        content = content.strip()
        
        # Collapse multiple spaces into single space
        content = re.sub(r' +', ' ', content)
        
        # Handle HTML based on strictness level
        if self.level == SanitizationLevel.STRICT:
            content = html.escape(content)
        elif self.level == SanitizationLevel.NORMAL:
            content = html.escape(content)
        # PERMISSIVE: Don't escape HTML
        
        # Truncate to max length
        if len(content) > self.max_length:
            content = content[:self.max_length]
        
        return content
    
    def sanitize_with_metadata(self, content: Optional[str]) -> SanitizedResult:
        """Sanitize input and return result with metadata.
        
        Args:
            content: Input string to sanitize
            
        Returns:
            SanitizedResult with content and metadata
        """
        if content is None:
            raise ValidationError("Input cannot be None", code="NULL_INPUT")
        
        original_length = len(content)
        sanitized = self.sanitize(content)
        sanitized_length = len(sanitized)
        
        warnings: List[str] = []
        has_suspicious = False
        
        # Check for SQL injection patterns
        for pattern in self._sql_patterns:
            if pattern.search(content):
                warnings.append("sql_injection")
                has_suspicious = True
                break
        
        # Check for XSS patterns
        for pattern in self._xss_patterns:
            if pattern.search(content):
                warnings.append("xss_attempt")
                has_suspicious = True
                break
        
        return SanitizedResult(
            content=sanitized,
            original_length=original_length,
            sanitized_length=sanitized_length,
            was_modified=(sanitized != content[:self.max_length]),
            has_suspicious_patterns=has_suspicious,
            warnings=warnings
        )
    
    def _strip_control_chars(self, content: str) -> str:
        """Remove control characters except newline and tab.
        
        Args:
            content: Input string
            
        Returns:
            String with control characters removed
        """
        result = []
        for char in content:
            # Keep printable chars, newline, and tab
            if char == '\n' or char == '\t':
                result.append(char)
            elif ord(char) >= 32:
                # Printable ASCII or higher
                result.append(char)
            # Skip other control characters (0x01-0x1F except 0x09, 0x0A)
        return ''.join(result)
