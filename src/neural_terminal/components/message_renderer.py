"""XSS-safe message rendering with Bleach sanitization.

Provides secure HTML rendering for chat messages with configurable
allowlists and automatic code block detection.
"""

import re
import html
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from decimal import Decimal

import bleach
from markdown import markdown


# Default allowed tags for Bleach
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "code",
    "pre",
    "ul",
    "ol",
    "li",
    "a",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "hr",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]

# Default allowed attributes
ALLOWED_ATTRIBUTES: Dict[str, List[str]] = {
    "a": ["href", "title"],
    "code": ["class"],
    "pre": ["class"],
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


@dataclass(frozen=True)
class CodeBlock:
    """Represents a detected code block."""

    language: Optional[str]
    code: str
    start: int
    end: int


class MessageSanitizer:
    """XSS-safe message sanitizer using Bleach."""

    def __init__(
        self,
        allowed_tags: Optional[List[str]] = None,
        allowed_attributes: Optional[Dict[str, List[str]]] = None,
        allowed_protocols: Optional[List[str]] = None,
    ):
        """Initialize sanitizer with allowlists.

        Args:
            allowed_tags: HTML tags to allow (defaults to ALLOWED_TAGS)
            allowed_attributes: Attributes to allow per tag
            allowed_protocols: URL protocols to allow in links
        """
        self._tags = allowed_tags or ALLOWED_TAGS
        self._attrs = allowed_attributes or ALLOWED_ATTRIBUTES
        self._protocols = allowed_protocols or ALLOWED_PROTOCOLS

    def sanitize(self, text: str) -> str:
        """Sanitize text using Bleach.

        Removes all HTML tags not in the allowlist and escapes
        any remaining unsafe content.

        Args:
            text: Raw text to sanitize

        Returns:
            Sanitized HTML string
        """
        if not text:
            return ""

        return bleach.clean(
            text,
            tags=self._tags,
            attributes=self._attrs,
            protocols=self._protocols,
            strip=True,  # Remove disallowed tags entirely
        )

    def escape_text(self, text: str) -> str:
        """Escape all HTML in text.

        Args:
            text: Raw text to escape

        Returns:
            HTML-escaped string
        """
        return html.escape(text)


class CodeBlockParser:
    """Parser for detecting and extracting code blocks.

    Features a bounded LRU cache to prevent unbounded memory growth.
    """

    # Pattern for fenced code blocks (```lang\ncode\n```)
    FENCED_PATTERN = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

    # Pattern for inline code (`code`)
    INLINE_PATTERN = re.compile(r"`([^`]+)`")

    def __init__(self, max_cache_size: int = 100):
        """Initialize code block parser.

        Args:
            max_cache_size: Maximum number of entries in cache (0 to disable)

        Raises:
            ValueError: If max_cache_size is negative
        """
        if max_cache_size < 0:
            raise ValueError("max_cache_size must be non-negative")

        self._max_cache_size = max_cache_size
        # Use OrderedDict for LRU behavior
        self._fenced_cache: Dict[str, List[CodeBlock]] = {}

    def parse_fenced_blocks(self, text: str) -> List[CodeBlock]:
        """Extract fenced code blocks from text.

        Args:
            text: Text to parse

        Returns:
            List of detected code blocks
        """
        # Check cache first
        if text in self._fenced_cache:
            # Move to end (most recently used)
            result = self._fenced_cache[text]
            del self._fenced_cache[text]
            self._fenced_cache[text] = result
            return result

        # Parse blocks
        blocks = []
        for match in self.FENCED_PATTERN.finditer(text):
            language = match.group(1).strip() or None
            code = match.group(2).strip()

            blocks.append(
                CodeBlock(
                    language=language,
                    code=code,
                    start=match.start(),
                    end=match.end(),
                )
            )

        # Cache the result if caching is enabled
        if self._max_cache_size > 0:
            self._fenced_cache[text] = blocks

            # LRU eviction: remove oldest items if over limit
            while len(self._fenced_cache) > self._max_cache_size:
                # Remove first item (oldest)
                first_key = next(iter(self._fenced_cache))
                del self._fenced_cache[first_key]

        return blocks

    def parse_inline_code(self, text: str) -> List[CodeBlock]:
        """Extract inline code snippets from text.

        Args:
            text: Text to parse

        Returns:
            List of inline code blocks
        """
        blocks = []
        for match in self.INLINE_PATTERN.finditer(text):
            blocks.append(
                CodeBlock(
                    language=None,
                    code=match.group(1),
                    start=match.start(),
                    end=match.end(),
                )
            )
        return blocks

    def split_code_and_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into alternating code and text segments.

        Args:
            text: Text to split

        Returns:
            List of segments with 'type' and 'content' keys
        """
        blocks = self.parse_fenced_blocks(text)

        if not blocks:
            return [{"type": "text", "content": text}]

        segments = []
        last_end = 0

        for block in blocks:
            # Add text before code block
            if block.start > last_end:
                segments.append(
                    {
                        "type": "text",
                        "content": text[last_end : block.start],
                    }
                )

            # Add code block
            segments.append(
                {
                    "type": "code",
                    "language": block.language,
                    "content": block.code,
                }
            )

            last_end = block.end

        # Add remaining text
        if last_end < len(text):
            segments.append(
                {
                    "type": "text",
                    "content": text[last_end:],
                }
            )

        return segments

    def clear_cache(self) -> None:
        """Clear the fenced block cache."""
        self._fenced_cache.clear()


class MessageRenderer:
    """Renders messages with XSS protection and code highlighting."""

    # Language aliases for common cases
    LANGUAGE_ALIASES = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "sh": "bash",
        "shell": "bash",
        "yml": "yaml",
        "json": "json",
        "md": "markdown",
        "rb": "ruby",
        "rs": "rust",
        "go": "go",
        "cpp": "cpp",
        "c++": "cpp",
        "cs": "csharp",
        "kt": "kotlin",
        "swift": "swift",
    }

    def __init__(
        self,
        sanitizer: Optional[MessageSanitizer] = None,
        code_parser: Optional[CodeBlockParser] = None,
    ):
        """Initialize message renderer.

        Args:
            sanitizer: Message sanitizer instance
            code_parser: Code block parser instance
        """
        self._sanitizer = sanitizer or MessageSanitizer()
        self._code_parser = code_parser or CodeBlockParser()

    def _normalize_language(self, lang: Optional[str]) -> str:
        """Normalize language identifier.

        Args:
            lang: Raw language string

        Returns:
            Normalized language name
        """
        if not lang:
            return "text"

        lang = lang.lower().strip()
        return self.LANGUAGE_ALIASES.get(lang, lang)

    def _render_code_block(
        self,
        code: str,
        language: Optional[str] = None,
    ) -> str:
        """Render a code block with syntax highlighting classes.

        Args:
            code: Code content
            language: Programming language

        Returns:
            HTML for code block
        """
        lang = self._normalize_language(language)
        escaped_code = html.escape(code)

        # Use simple pre/code with language class
        # Full syntax highlighting would require a library like Pygments
        return (
            f'<div class="nt-code-block" data-language="{lang}">\n'
            f'  <div class="nt-code-header">\n'
            f'    <span class="nt-code-lang">{lang}</span>\n'
            f'    <button class="nt-code-copy" onclick="copyCode(this)">Copy</button>\n'
            f"  </div>\n"
            f'  <pre><code class="language-{lang}">{escaped_code}</code></pre>\n'
            f"</div>"
        )

    def _render_inline_code(self, code: str) -> str:
        """Render inline code.

        Args:
            code: Code content

        Returns:
            HTML for inline code
        """
        escaped = html.escape(code)
        return f"<code>{escaped}</code>"

    def _render_markdown(self, text: str) -> str:
        """Render markdown to HTML with sanitization.

        Args:
            text: Markdown text

        Returns:
            Sanitized HTML
        """
        # Convert markdown to HTML
        html_content = markdown(
            text,
            extensions=["fenced_code", "tables", "toc"],
            safe_mode="escape",
        )

        # Sanitize the result
        return self._sanitizer.sanitize(html_content)

    def render(
        self,
        content: str,
        role: str = "assistant",
        render_markdown: bool = True,
    ) -> str:
        """Render message content safely.

        Args:
            content: Raw message content
            role: Message role (user, assistant, system)
            render_markdown: Whether to render markdown

        Returns:
            Safe HTML string
        """
        if not content:
            return ""

        # Split into code and text segments
        segments = self._code_parser.split_code_and_text(content)

        rendered_parts = []

        for segment in segments:
            if segment["type"] == "code":
                # Render code block
                rendered = self._render_code_block(
                    segment["content"],
                    segment.get("language"),
                )
                rendered_parts.append(rendered)
            else:
                # Render text
                text = segment["content"]

                if render_markdown:
                    # Convert markdown and sanitize
                    rendered = self._render_markdown(text)
                else:
                    # Just escape and convert newlines
                    escaped = html.escape(text)
                    rendered = escaped.replace("\n", "<br>")

                rendered_parts.append(rendered)

        # Combine all parts
        return "".join(rendered_parts)

    def render_text_only(self, content: str) -> str:
        """Render as plain text only (no markdown, no code blocks).

        Args:
            content: Raw content

        Returns:
            Escaped text with newlines preserved
        """
        if not content:
            return ""

        escaped = html.escape(content)
        return escaped.replace("\n", "<br>")

    def render_error(self, message: str) -> str:
        """Render an error message.

        Args:
            message: Error message

        Returns:
            HTML for error display
        """
        escaped = html.escape(message)
        return f'<div class="nt-error-message">{escaped}</div>'

    def render_system_message(self, content: str) -> str:
        """Render a system message.

        Args:
            content: System message content

        Returns:
            HTML for system message
        """
        escaped = html.escape(content)
        return f'<div class="nt-system-message">{escaped}</div>'

    def render_cost_info(
        self,
        cost: Decimal,
        tokens: int,
        latency_ms: Optional[int] = None,
    ) -> str:
        """Render cost and token metadata.

        Args:
            cost: Message cost
            tokens: Token count
            latency_ms: Response latency in milliseconds

        Returns:
            HTML for metadata display
        """
        parts = [
            f'<span class="nt-message-cost">${float(cost):.4f}</span>',
            f'<span class="nt-message-tokens">{tokens} tokens</span>',
        ]

        if latency_ms is not None:
            parts.append(f'<span class="nt-message-latency">{latency_ms}ms</span>')

        return f'<div class="nt-message-meta">{" | ".join(parts)}</div>'


class StreamingMessageRenderer:
    """Renderer for streaming message content."""

    def __init__(self, renderer: Optional[MessageRenderer] = None):
        """Initialize streaming renderer.

        Args:
            renderer: Base message renderer
        """
        self._renderer = renderer or MessageRenderer()
        self._buffer = ""

    def append(self, chunk: str) -> str:
        """Append a chunk and return updated render.

        Args:
            chunk: New text chunk

        Returns:
            Updated HTML
        """
        self._buffer += chunk
        return self._renderer.render(self._buffer, render_markdown=False)

    def get_current(self) -> str:
        """Get current rendered content.

        Returns:
            Current HTML
        """
        return self._renderer.render(self._buffer, render_markdown=False)

    def finalize(self) -> str:
        """Finalize rendering with full markdown processing.

        Returns:
            Final HTML
        """
        return self._renderer.render(self._buffer, render_markdown=True)

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer = ""

    @property
    def buffer(self) -> str:
        """Get raw buffer content."""
        return self._buffer


# Convenience functions for direct use
def render_message(content: str, role: str = "assistant", **kwargs) -> str:
    """Render a message with default settings.

    Args:
        content: Message content
        role: Message role
        **kwargs: Additional renderer options

    Returns:
        Safe HTML string
    """
    renderer = MessageRenderer()
    return renderer.render(content, role, **kwargs)


def sanitize_html(text: str) -> str:
    """Sanitize HTML using default settings.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized HTML
    """
    sanitizer = MessageSanitizer()
    return sanitizer.sanitize(text)


def escape_html(text: str) -> str:
    """Escape all HTML entities.

    Args:
        text: Text to escape

    Returns:
        Escaped HTML
    """
    return html.escape(text)
