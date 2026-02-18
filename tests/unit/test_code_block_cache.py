"""Tests for CodeBlockParser bounded cache implementation.

Phase 3: Bounded Cache - Prevents unbounded memory growth.
"""

import pytest
from neural_terminal.components.message_renderer import CodeBlockParser, CodeBlock


class TestCodeBlockCacheBounded:
    """Tests for bounded cache implementation."""

    def test_cache_has_max_size_limit(self):
        """Test that cache has a maximum size limit."""
        parser = CodeBlockParser(max_cache_size=3)

        # Parse 5 different texts
        for i in range(5):
            parser.parse_fenced_blocks(f"```python\ncode{i}\n```")

        # Cache should only contain 3 items
        assert len(parser._fenced_cache) == 3

    def test_cache_uses_lru_eviction(self):
        """Test that LRU eviction is used when cache is full."""
        parser = CodeBlockParser(max_cache_size=2)

        # Add first item
        parser.parse_fenced_blocks("```\ncode1\n```")
        assert "```\ncode1\n```" in parser._fenced_cache

        # Add second item
        parser.parse_fenced_blocks("```\ncode2\n```")
        assert "```\ncode1\n```" in parser._fenced_cache
        assert "```\ncode2\n```" in parser._fenced_cache

        # Add third item - should evict first
        parser.parse_fenced_blocks("```\ncode3\n```")
        assert "```\ncode1\n```" not in parser._fenced_cache
        assert "```\ncode2\n```" in parser._fenced_cache
        assert "```\ncode3\n```" in parser._fenced_cache

    def test_accessing_cached_item_updates_lru(self):
        """Test that accessing an item updates its LRU position."""
        parser = CodeBlockParser(max_cache_size=2)

        # Add two items
        parser.parse_fenced_blocks("```\ncode1\n```")
        parser.parse_fenced_blocks("```\ncode2\n```")

        # Access first item (updates LRU) - must use parse_fenced_blocks
        # to trigger the LRU update logic
        parser.parse_fenced_blocks("```\ncode1\n```")

        # Add third item - should evict code2, not code1
        parser.parse_fenced_blocks("```\ncode3\n```")
        assert "```\ncode1\n```" in parser._fenced_cache
        assert "```\ncode2\n```" not in parser._fenced_cache

    def test_default_max_cache_size(self):
        """Test that default max cache size is reasonable."""
        parser = CodeBlockParser()
        assert parser._max_cache_size == 100  # Default should be 100

    def test_cache_can_be_disabled(self):
        """Test that cache can be disabled with size 0."""
        parser = CodeBlockParser(max_cache_size=0)

        parser.parse_fenced_blocks("```\ncode\n```")

        # Cache should be empty when disabled
        assert len(parser._fenced_cache) == 0

    def test_cache_size_validation(self):
        """Test that negative cache size raises error."""
        with pytest.raises(ValueError):
            CodeBlockParser(max_cache_size=-1)

    def test_cache_clear_resets_to_zero(self):
        """Test that clearing cache removes all items."""
        parser = CodeBlockParser(max_cache_size=5)

        parser.parse_fenced_blocks("```\ncode1\n```")
        parser.parse_fenced_blocks("```\ncode2\n```")

        assert len(parser._fenced_cache) == 2

        parser.clear_cache()

        assert len(parser._fenced_cache) == 0

    def test_cache_performance_with_repeated_texts(self):
        """Test that repeated texts use cache."""
        parser = CodeBlockParser(max_cache_size=3)

        text = "```python\ndef hello():\n    pass\n```"

        # First parse
        result1 = parser.parse_fenced_blocks(text)

        # Second parse - should return cached result
        result2 = parser.parse_fenced_blocks(text)

        # Should be the same object (cached)
        assert result1 is result2

    def test_cache_stores_correct_data(self):
        """Test that cache stores correct parsed blocks."""
        parser = CodeBlockParser(max_cache_size=1)

        text = "```python\nprint('hello')\n```"
        result = parser.parse_fenced_blocks(text)

        assert text in parser._fenced_cache
        cached_result = parser._fenced_cache[text]
        assert len(cached_result) == 1
        assert cached_result[0].language == "python"
        assert cached_result[0].code == "print('hello')"


class TestCodeBlockCacheConfiguration:
    """Tests for cache configuration."""

    def test_custom_max_cache_size(self):
        """Test custom max cache size."""
        parser = CodeBlockParser(max_cache_size=50)
        assert parser._max_cache_size == 50

    def test_large_max_cache_size(self):
        """Test large max cache size."""
        parser = CodeBlockParser(max_cache_size=1000)
        assert parser._max_cache_size == 1000

    def test_small_max_cache_size(self):
        """Test small max cache size."""
        parser = CodeBlockParser(max_cache_size=1)
        assert parser._max_cache_size == 1
