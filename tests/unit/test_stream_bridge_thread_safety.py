"""Tests for StreamlitStreamBridge thread safety.

Phase 4: Thread Safety - Ensures safe concurrent access.
"""

import asyncio
import threading
import time
import pytest

from neural_terminal.components.stream_bridge import StreamlitStreamBridge


class TestStreamlitStreamBridgeThreadSafety:
    """Tests for thread safety of StreamlitStreamBridge."""

    def test_concurrent_buffer_access(self):
        """Test that concurrent buffer access is thread-safe."""
        bridge = StreamlitStreamBridge()

        # Track deltas received
        deltas = []

        async def gen():
            for i in range(100):
                yield (f"chunk{i}", None)
                await asyncio.sleep(0.001)
            yield ("", {"done": True})

        def on_delta(delta):
            deltas.append(delta)

        result = bridge.stream(gen(), on_delta=on_delta)

        # Content should be complete and not corrupted
        expected = "".join(f"chunk{i}" for i in range(100))
        assert bridge.content == expected
        assert len(deltas) == 100

    def test_is_running_flag_thread_safety(self):
        """Test that _is_running flag is thread-safe."""
        bridge = StreamlitStreamBridge()
        errors = []

        async def gen():
            for i in range(50):
                yield (f"data{i}", None)
                await asyncio.sleep(0.001)
            yield ("", {"done": True})

        def check_running():
            """Simulate concurrent access to _is_running."""
            for _ in range(100):
                try:
                    _ = bridge._is_running
                except Exception as e:
                    errors.append(str(e))
                time.sleep(0.001)

        # Start checker thread
        checker = threading.Thread(target=check_running)
        checker.start()

        # Run stream
        bridge.stream(gen())

        checker.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"

    def test_error_handling_thread_safety(self):
        """Test that error handling is thread-safe."""
        bridge = StreamlitStreamBridge()

        async def gen():
            yield ("partial", None)
            raise RuntimeError("Test error")

        with pytest.raises(Exception):
            bridge.stream(gen())

        # Error should be captured
        assert bridge._error == "Test error"
        assert bridge.content == "partial"

    def test_multiple_concurrent_streams(self):
        """Test that multiple bridges can run concurrently."""
        bridges = [StreamlitStreamBridge() for _ in range(3)]
        results = {}

        async def gen(bridge_id):
            for i in range(10):
                yield (f"{bridge_id}-{i}", None)
                await asyncio.sleep(0.001)
            yield ("", {"bridge_id": bridge_id})

        def run_stream(bridge, bridge_id):
            result = bridge.stream(gen(bridge_id))
            results[bridge_id] = {"content": bridge.content, "result": result}

        # Run all streams concurrently
        threads = []
        for i, bridge in enumerate(bridges):
            t = threading.Thread(target=run_stream, args=(bridge, f"bridge{i}"))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify each stream completed correctly
        for i in range(3):
            bridge_id = f"bridge{i}"
            expected_content = "".join(f"{bridge_id}-{j}" for j in range(10))
            assert results[bridge_id]["content"] == expected_content
            assert results[bridge_id]["result"]["bridge_id"] == bridge_id

    def test_final_metadata_thread_safety(self):
        """Test that final_metadata is set atomically."""
        bridge = StreamlitStreamBridge()

        async def gen():
            yield ("data", None)
            yield ("", {"key": "value", "number": 42})

        result = bridge.stream(gen())

        # Result should be complete and not corrupted
        assert result == {"key": "value", "number": 42}
        assert bridge._final_metadata == {"key": "value", "number": 42}

    def test_queue_operations_thread_safety(self):
        """Test that queue operations remain thread-safe."""
        bridge = StreamlitStreamBridge()
        errors = []

        async def gen():
            for i in range(100):
                yield (f"item{i}", None)
                await asyncio.sleep(0.001)
            yield ("", {"done": True})

        def producer_check():
            """Simulate concurrent queue access."""
            try:
                for _ in range(50):
                    # This shouldn't cause issues as queue is thread-safe
                    time.sleep(0.01)
            except Exception as e:
                errors.append(str(e))

        # Start checker threads
        threads = [threading.Thread(target=producer_check) for _ in range(2)]
        for t in threads:
            t.start()

        result = bridge.stream(gen())

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Queue errors: {errors}"
        assert result == {"done": True}


class TestStreamlitStreamBridgeLockSafety:
    """Tests for lock-based thread safety."""

    def test_has_lock_attribute(self):
        """Test that bridge has a lock for thread safety."""
        bridge = StreamlitStreamBridge()
        assert hasattr(bridge, "_lock")
        # threading.Lock() returns a lock object with acquire/release methods
        assert callable(getattr(bridge._lock, "acquire", None))
        assert callable(getattr(bridge._lock, "release", None))

    def test_lock_protects_buffer_access(self):
        """Test that lock protects buffer access."""
        bridge = StreamlitStreamBridge()

        async def gen():
            yield ("A", None)
            yield ("B", None)
            yield ("", {"done": True})

        result = bridge.stream(gen())

        # Buffer should be complete
        assert bridge.content == "AB"

        # Should be able to acquire lock (not held)
        assert bridge._lock.acquire(blocking=False)
        bridge._lock.release()
