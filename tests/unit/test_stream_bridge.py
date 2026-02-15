"""Unit tests for Streamlit stream bridge.

Tests for Phase 3: Async-to-sync bridge for Streamlit.
"""
import asyncio
import pytest

from neural_terminal.components.stream_bridge import StreamlitStreamBridge, run_async


async def mock_async_generator(chunks):
    """Helper to create mock async generator."""
    for chunk in chunks:
        await asyncio.sleep(0.01)  # Simulate async work
        yield chunk


class TestRunAsync:
    """Tests for run_async helper."""

    def test_run_async_executes_coroutine(self):
        """Test that run_async executes coroutine and returns result."""
        async def coro():
            await asyncio.sleep(0.01)
            return "result"
        
        result = run_async(coro())
        
        assert result == "result"
    
    def test_run_async_propagates_exception(self):
        """Test that run_async propagates exceptions."""
        async def failing_coro():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            run_async(failing_coro())
    
    def test_run_async_with_existing_loop(self):
        """Test run_async when already in an event loop."""
        # This would be the case when called from within Streamlit
        async def inner():
            async def coro():
                return "nested result"
            return run_async(coro())
        
        # This simulates being inside an event loop
        result = asyncio.run(inner())
        assert result == "nested result"


class TestStreamlitStreamBridge:
    """Tests for StreamlitStreamBridge."""

    def test_stream_consumes_generator(self):
        """Test that stream consumes async generator."""
        bridge = StreamlitStreamBridge()
        
        async def gen():
            yield ("Hello", None)
            yield (" ", None)
            yield ("world", None)
            yield ("", {"done": True})
        
        result = bridge.stream(gen())
        
        assert bridge.content == "Hello world"
        assert result == {"done": True}
    
    def test_stream_calls_on_delta(self):
        """Test that on_delta callback is called for each delta."""
        bridge = StreamlitStreamBridge()
        deltas = []
        
        async def gen():
            yield ("chunk1", None)
            yield ("chunk2", None)
            yield ("", {"done": True})
        
        def on_delta(delta):
            deltas.append(delta)
        
        bridge.stream(gen(), on_delta=on_delta)
        
        assert deltas == ["chunk1", "chunk2"]
    
    def test_stream_calls_on_complete(self):
        """Test that on_complete callback is called with metadata."""
        bridge = StreamlitStreamBridge()
        complete_meta = None
        
        async def gen():
            yield ("data", None)
            yield ("", {"cost": "0.01", "tokens": 100})
        
        def on_complete(meta):
            nonlocal complete_meta
            complete_meta = meta
        
        bridge.stream(gen(), on_complete=on_complete)
        
        assert complete_meta == {"cost": "0.01", "tokens": 100}
    
    def test_stream_propagates_errors(self):
        """Test that errors in generator are propagated."""
        bridge = StreamlitStreamBridge()
        
        async def failing_gen():
            yield ("partial", None)
            raise RuntimeError("Stream error")
        
        with pytest.raises(Exception, match="Stream error"):
            bridge.stream(failing_gen())
        
        # Partial content should still be available
        assert bridge.content == "partial"
    
    def test_stream_content_property(self):
        """Test content property returns accumulated text."""
        bridge = StreamlitStreamBridge()
        
        async def gen():
            yield ("A", None)
            yield ("B", None)
            yield ("C", None)
            yield ("", None)
        
        bridge.stream(gen())
        
        assert bridge.content == "ABC"
    
    def test_stream_empty_generator(self):
        """Test stream handles empty generator."""
        bridge = StreamlitStreamBridge()
        
        async def empty_gen():
            yield ("", {"empty": True})
        
        result = bridge.stream(empty_gen())
        
        assert bridge.content == ""
        assert result == {"empty": True}
    
    def test_stream_multiple_metadata(self):
        """Test stream handles multiple metadata emissions."""
        bridge = StreamlitStreamBridge()
        metas = []
        
        async def gen():
            yield ("", {"progress": 0.5})
            yield ("", {"progress": 1.0})
            yield ("", {"final": True})
        
        def on_complete(meta):
            metas.append(meta)
        
        bridge.stream(gen(), on_complete=on_complete)
        
        # Should be called for each metadata
        assert len(metas) == 3
        assert metas[-1] == {"final": True}
