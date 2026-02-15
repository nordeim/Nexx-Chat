"""Tests for message rendering and XSS protection."""

import pytest
from decimal import Decimal

from neural_terminal.components.message_renderer import (
    MessageSanitizer,
    CodeBlockParser,
    CodeBlock,
    MessageRenderer,
    StreamingMessageRenderer,
    ALLOWED_TAGS,
    ALLOWED_ATTRIBUTES,
    render_message,
    sanitize_html,
    escape_html,
)


class TestMessageSanitizer:
    """Tests for MessageSanitizer."""
    
    def test_sanitize_removes_script_tags(self):
        """Sanitizer removes script tags."""
        sanitizer = MessageSanitizer()
        
        dirty = '<script>alert("xss")</script>Hello'
        clean = sanitizer.sanitize(dirty)
        
        assert "<script>" not in clean
        # Bleach removes tags but may keep text content
        assert "Hello" in clean
    
    def test_sanitize_allows_safe_tags(self):
        """Sanitizer allows safe HTML tags."""
        sanitizer = MessageSanitizer()
        
        safe = '<p>Hello <strong>world</strong></p>'
        result = sanitizer.sanitize(safe)
        
        assert "<p>" in result
        assert "<strong>" in result
    
    def test_sanitize_removes_unsafe_attributes(self):
        """Sanitizer removes unsafe attributes."""
        sanitizer = MessageSanitizer()
        
        dirty = '<p onclick="alert(1)">Hello</p>'
        clean = sanitizer.sanitize(dirty)
        
        assert "onclick" not in clean
        assert "<p>" in clean
    
    def test_sanitize_allows_link_attributes(self):
        """Sanitizer allows safe link attributes."""
        sanitizer = MessageSanitizer()
        
        safe = '<a href="https://example.com" title="Link">Click</a>'
        result = sanitizer.sanitize(safe)
        
        assert 'href="https://example.com"' in result
        assert 'title="Link"' in result
    
    def test_sanitize_blocks_javascript_protocol(self):
        """Sanitizer blocks javascript: URLs."""
        sanitizer = MessageSanitizer()
        
        dirty = '<a href="javascript:alert(1)">Click</a>'
        clean = sanitizer.sanitize(dirty)
        
        assert "javascript:" not in clean
    
    def test_sanitize_empty_string(self):
        """Sanitizer handles empty strings."""
        sanitizer = MessageSanitizer()
        
        assert sanitizer.sanitize("") == ""
        assert sanitizer.sanitize(None) == ""  # type: ignore
    
    def test_escape_text_escapes_all_html(self):
        """escape_text escapes all HTML entities."""
        sanitizer = MessageSanitizer()
        
        text = '<script>alert("xss")</script>'
        escaped = sanitizer.escape_text(text)
        
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
    
    def test_custom_allowlist(self):
        """Can use custom tag allowlist."""
        sanitizer = MessageSanitizer(allowed_tags=['p'])
        
        text = '<p>Hello</p><strong>World</strong>'
        result = sanitizer.sanitize(text)
        
        assert "<p>" in result
        assert "<strong>" not in result


class TestCodeBlockParser:
    """Tests for CodeBlockParser."""
    
    def test_parse_fenced_block_with_language(self):
        """Parser extracts code blocks with language."""
        parser = CodeBlockParser()
        
        text = '```python\nprint("hello")\n```'
        blocks = parser.parse_fenced_blocks(text)
        
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert blocks[0].code == 'print("hello")'
    
    def test_parse_fenced_block_without_language(self):
        """Parser extracts code blocks without language."""
        parser = CodeBlockParser()
        
        text = '```\nsome code\n```'
        blocks = parser.parse_fenced_blocks(text)
        
        assert len(blocks) == 1
        assert blocks[0].language is None
        assert blocks[0].code == "some code"
    
    def test_parse_multiple_blocks(self):
        """Parser extracts multiple code blocks."""
        parser = CodeBlockParser()
        
        text = '''```python
print(1)
```

Some text

```javascript
console.log(2);
```'''
        blocks = parser.parse_fenced_blocks(text)
        
        assert len(blocks) == 2
        assert blocks[0].language == "python"
        assert blocks[1].language == "javascript"
    
    def test_parse_inline_code(self):
        """Parser extracts inline code."""
        parser = CodeBlockParser()
        
        text = 'Use `print()` function'
        blocks = parser.parse_inline_code(text)
        
        assert len(blocks) == 1
        assert blocks[0].code == "print()"
        assert blocks[0].language is None
    
    def test_parse_no_blocks(self):
        """Parser returns empty list for plain text."""
        parser = CodeBlockParser()
        
        text = "Just plain text"
        blocks = parser.parse_fenced_blocks(text)
        
        assert blocks == []
    
    def test_split_code_and_text(self):
        """Parser splits text and code segments."""
        parser = CodeBlockParser()
        
        text = 'Hello\n```python\ncode\n```\nWorld'
        segments = parser.split_code_and_text(text)
        
        assert len(segments) == 3
        assert segments[0]['type'] == 'text'
        assert segments[0]['content'] == 'Hello\n'
        assert segments[1]['type'] == 'code'
        assert segments[1]['language'] == 'python'
        assert segments[2]['type'] == 'text'
        assert segments[2]['content'] == '\nWorld'
    
    def test_split_no_code(self):
        """Parser returns single text segment for plain text."""
        parser = CodeBlockParser()
        
        text = "Just text"
        segments = parser.split_code_and_text(text)
        
        assert len(segments) == 1
        assert segments[0]['type'] == 'text'
        assert segments[0]['content'] == "Just text"
    
    def test_cache_works(self):
        """Parser caches parsed results."""
        parser = CodeBlockParser()
        
        text = '```python\ncode\n```'
        
        # First parse
        blocks1 = parser.parse_fenced_blocks(text)
        # Second parse (should use cache)
        blocks2 = parser.parse_fenced_blocks(text)
        
        assert blocks1 is blocks2  # Same object from cache
    
    def test_clear_cache(self):
        """Parser cache can be cleared."""
        parser = CodeBlockParser()
        
        text = '```python\ncode\n```'
        parser.parse_fenced_blocks(text)
        
        parser.clear_cache()
        
        assert len(parser._fenced_cache) == 0


class TestMessageRenderer:
    """Tests for MessageRenderer."""
    
    def test_render_escapes_xss(self):
        """Renderer escapes XSS attempts."""
        renderer = MessageRenderer()
        
        dirty = '<script>alert("xss")</script>'
        result = renderer.render(dirty)
        
        assert "<script>" not in result
    
    def test_render_code_block(self):
        """Renderer formats code blocks."""
        renderer = MessageRenderer()
        
        text = '```python\nprint("hello")\n```'
        result = renderer.render(text)
        
        assert "nt-code-block" in result
        assert "language-python" in result
        assert "print" in result
    
    def test_render_inline_code(self):
        """Renderer formats inline code when markdown enabled."""
        renderer = MessageRenderer()
        
        text = 'Use `print()` function'
        # With markdown rendering, backticks become <code> tags
        result = renderer.render(text, render_markdown=True)
        
        assert "<code>" in result
        assert "print()" in result
    
    def test_render_markdown_formatting(self):
        """Renderer processes markdown."""
        renderer = MessageRenderer()
        
        text = '**bold** and *italic*'
        result = renderer.render(text)
        
        assert "<strong>" in result or "<b>" in result
        assert "<em>" in result or "<i>" in result
    
    def test_render_text_only(self):
        """text_only mode escapes all HTML."""
        renderer = MessageRenderer()
        
        text = '<b>Bold</b> text'
        result = renderer.render_text_only(text)
        
        assert "<b>" not in result
        assert "&lt;b&gt;" in result
    
    def test_render_error(self):
        """Error rendering creates error div."""
        renderer = MessageRenderer()
        
        result = renderer.render_error("Something went wrong")
        
        assert "nt-error-message" in result
        assert "Something went wrong" in result
    
    def test_render_system_message(self):
        """System message rendering."""
        renderer = MessageRenderer()
        
        result = renderer.render_system_message("System notification")
        
        assert "nt-system-message" in result
        assert "System notification" in result
    
    def test_render_cost_info(self):
        """Cost info rendering."""
        renderer = MessageRenderer()
        
        result = renderer.render_cost_info(
            cost=Decimal("0.0012"),
            tokens=150,
            latency_ms=500,
        )
        
        assert "nt-message-meta" in result
        assert "$0.0012" in result
        assert "150 tokens" in result
        assert "500ms" in result
    
    def test_render_cost_info_without_latency(self):
        """Cost info rendering without latency."""
        renderer = MessageRenderer()
        
        result = renderer.render_cost_info(
            cost=Decimal("0.0012"),
            tokens=150,
        )
        
        assert "nt-message-meta" in result
        assert "$0.0012" in result
        assert "ms" not in result
    
    def test_normalize_language(self):
        """Language normalization works."""
        renderer = MessageRenderer()
        
        assert renderer._normalize_language("py") == "python"
        assert renderer._normalize_language("js") == "javascript"
        assert renderer._normalize_language("python") == "python"
        assert renderer._normalize_language(None) == "text"
        assert renderer._normalize_language("") == "text"
    
    def test_render_empty_content(self):
        """Renderer handles empty content."""
        renderer = MessageRenderer()
        
        assert renderer.render("") == ""
        assert renderer.render(None) == ""  # type: ignore


class TestStreamingMessageRenderer:
    """Tests for StreamingMessageRenderer."""
    
    def test_append_adds_to_buffer(self):
        """Append adds chunks to buffer."""
        streamer = StreamingMessageRenderer()
        
        streamer.append("Hello")
        streamer.append(" World")
        
        assert streamer.buffer == "Hello World"
    
    def test_get_current_renders_buffer(self):
        """get_current returns rendered buffer."""
        streamer = StreamingMessageRenderer()
        
        streamer.append("Hello")
        result = streamer.get_current()
        
        assert "Hello" in result
    
    def test_finalize_uses_markdown(self):
        """finalize applies markdown rendering."""
        streamer = StreamingMessageRenderer()
        
        streamer.append("**bold**")
        result = streamer.finalize()
        
        assert "<strong>" in result or "<b>" in result
    
    def test_clear_empties_buffer(self):
        """Clear empties the buffer."""
        streamer = StreamingMessageRenderer()
        
        streamer.append("Hello")
        streamer.clear()
        
        assert streamer.buffer == ""


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_render_message(self):
        """render_message function works."""
        result = render_message("Hello **world**")
        
        assert "world" in result
    
    def test_sanitize_html(self):
        """sanitize_html function works."""
        result = sanitize_html('<script>alert(1)</script>')
        
        assert "<script>" not in result
    
    def test_escape_html(self):
        """escape_html function works."""
        result = escape_html('<b>test</b>')
        
        assert result == "&lt;b&gt;test&lt;/b&gt;"


class TestXSSProtection:
    """XSS protection integration tests."""
    
    def test_xss_in_code_block_not_executed(self):
        """XSS in code blocks is escaped."""
        renderer = MessageRenderer()
        
        text = '```\n<script>alert(1)</script>\n```'
        result = renderer.render(text)
        
        # Script tag should be escaped in code block
        assert "<script>" not in result or "&lt;script&gt;" in result
    
    def test_xss_in_inline_code_not_executed(self):
        """XSS in inline code is escaped."""
        renderer = MessageRenderer()
        
        text = '`<script>alert(1)</script>`'
        result = renderer.render(text, render_markdown=False)
        
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_event_handlers_removed(self):
        """Event handlers are removed from output."""
        renderer = MessageRenderer()
        
        text = '<p onload="alert(1)" onclick="alert(2)">Hello</p>'
        result = renderer.render(text)
        
        assert "onload" not in result
        assert "onclick" not in result
    
    def test_javascript_urls_removed(self):
        """javascript: URLs are removed."""
        renderer = MessageRenderer()
        
        text = '[Click me](javascript:alert(1))'
        result = renderer.render(text)
        
        assert "javascript:" not in result
