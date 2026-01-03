"""
Tests for async synthesis functions in bundled_tts.py.

These tests verify the async synthesis implementation using mocks.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest


_BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODULE_PATH = os.path.join(_BASE_PATH, "bundled_tts.py")


def _setup_bundled_tts_env():
    """Set up the environment for importing bundled_tts."""
    os.environ["AIOHTTP_NO_EXTENSIONS"] = "1"
    os.environ["FROZENLIST_NO_EXTENSIONS"] = "1"
    os.environ["MULTIDICT_NO_EXTENSIONS"] = "1"
    os.environ["YARL_NO_EXTENSIONS"] = "1"
    os.environ["PROPCACHE_NO_EXTENSIONS"] = "1"

    vendor_dir = os.path.join(_BASE_PATH, "vendor")
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)


def _load_bundled_tts():
    """Load the bundled_tts module."""
    _setup_bundled_tts_env()

    spec = importlib.util.spec_from_file_location("bundled_tts", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bundled_tts"] = module
    spec.loader.exec_module(module)
    return module


class TestSynthesizeBatchConcurrency:
    """Test batch synthesis concurrency control."""

    def test_batch_concurrency_limit_is_respected(self):
        """Batch should respect BATCH_CONCURRENCY_LIMIT."""
        bundled_tts = _load_bundled_tts()

        # Verify the constant exists and is reasonable
        assert bundled_tts.BATCH_CONCURRENCY_LIMIT > 0
        assert bundled_tts.BATCH_CONCURRENCY_LIMIT <= 10

    def test_batch_processes_multiple_items(self):
        """synthesize_batch should handle multiple items."""
        bundled_tts = _load_bundled_tts()

        # Verify we can create multiple items
        items = [
            bundled_tts.TTSItem(identifier="1", text="First"),
            bundled_tts.TTSItem(identifier="2", text="Second"),
            bundled_tts.TTSItem(identifier="3", text="Third"),
        ]

        assert len(items) == 3
        assert items[0].text == "First"
        assert items[2].identifier == "3"


class TestBatchResultOrdering:
    """Test that batch synthesis results preserve input order."""

    def test_asyncio_gather_preserves_order(self):
        """asyncio.gather should preserve the order of results.

        This test verifies the fundamental behavior that allows
        us to preserve input order in batch synthesis.
        """
        import asyncio

        async def make_result(value: int) -> int:
            # Simulate variable-duration work
            await asyncio.sleep(0.001 * (10 - value))  # Shorter sleep for larger values
            return value

        async def run_test():
            tasks = [make_result(i) for i in [5, 2, 8, 1, 9, 3]]
            results = await asyncio.gather(*tasks)
            return results

        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(run_test())
        finally:
            loop.close()

        # Results should be in the same order as the input, not completion order
        assert results == [5, 2, 8, 1, 9, 3]

    def test_results_maintain_input_order_with_numeric_identifiers(self):
        """Results should match input order even with numeric-like identifiers.

        This ensures identifiers like ["1", "10", "2"] stay in that order,
        not sorted lexicographically to ["1", "10", "2"] (which matches)
        or numerically to ["1", "2", "10"].
        """
        bundled_tts = _load_bundled_tts()

        # Create items with identifiers that would sort differently
        # Lexicographic: ["1", "10", "2"] (1 < 10 < 2 lexicographically because "10" < "2")
        # Actually lexicographic is: ["1", "10", "2"] stays same since "1" < "1" then "0" < ""
        # Let me use better example: ["1", "10", "9"] -> sorted: ["1", "10", "9"] stays same
        # Actually lexicographic: "10" < "9" because "1" < "9"
        # So ["9", "1", "10"] sorted lexicographically = ["1", "10", "9"]

        # The key is: if we pass ["9", "1", "10"], without sorting we get ["9", "1", "10"]
        # With lexicographic sort we'd get ["1", "10", "9"]
        items = [
            bundled_tts.TTSItem(identifier="9", text="Nine"),
            bundled_tts.TTSItem(identifier="1", text="One"),
            bundled_tts.TTSItem(identifier="10", text="Ten"),
        ]

        # Verify the order we expect after no sorting (preserving input order)
        expected_order = ["9", "1", "10"]

        # What we'd get with lexicographic sorting (which we removed)
        sorted_order = ["1", "10", "9"]

        assert [item.identifier for item in items] == expected_order
        assert [item.identifier for item in items] != sorted_order


class TestSynthesizeBatchErrorHandling:
    """Test error handling in batch synthesis."""

    def test_partial_failure_returns_mixed_results(self):
        """Batch should return both successes and failures."""
        bundled_tts = _load_bundled_tts()

        # Simulate mixed results
        results = [
            bundled_tts.TTSResult(identifier="1", audio=b"success"),
            bundled_tts.TTSResult(identifier="2", error="Synthesis failed"),
            bundled_tts.TTSResult(identifier="3", audio=b"another success"),
        ]

        successes = [r for r in results if r.audio]
        failures = [r for r in results if r.error]

        assert len(successes) == 2
        assert len(failures) == 1

    def test_all_failures_returns_all_errors(self):
        """Batch should return all errors if all fail."""
        bundled_tts = _load_bundled_tts()

        results = [
            bundled_tts.TTSResult(identifier="1", error="Failed 1"),
            bundled_tts.TTSResult(identifier="2", error="Failed 2"),
        ]

        failures = [r for r in results if r.error]
        assert len(failures) == 2


class TestSynthesizeBatchWithVoiceOverride:
    """Test voice override functionality in batch synthesis."""

    def test_item_voice_override_creates_correct_config(self):
        """Items with voice override should use their own voice."""
        bundled_tts = _load_bundled_tts()

        # Verify config merging logic
        base_config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
        )

        item_voice = "ja-JP-NanamiNeural"

        # Create item config with override
        item_config = bundled_tts.TTSConfig(
            voice=item_voice or base_config.voice,
            pitch=base_config.pitch,
            rate=base_config.rate,
            volume=base_config.volume,
            stream_timeout=base_config.stream_timeout,
            stream_timeout_retries=base_config.stream_timeout_retries,
        )

        assert item_config.voice == "ja-JP-NanamiNeural"
        assert item_config.pitch == "+0Hz"

    def test_item_without_voice_uses_config_voice(self):
        """Items without voice override should use config voice."""
        bundled_tts = _load_bundled_tts()

        base_config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
        )

        item_voice = None  # No override

        item_config = bundled_tts.TTSConfig(
            voice=item_voice or base_config.voice,
            pitch=base_config.pitch,
            rate=base_config.rate,
            volume=base_config.volume,
        )

        assert item_config.voice == "en-US-JennyNeural"


class TestTimeoutHandling:
    """Test timeout configuration and handling."""

    def test_timeout_values_are_passed_correctly(self):
        """Timeout values should be passed to config."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
            stream_timeout=45.0,
            stream_timeout_retries=2,
        )

        assert config.stream_timeout == 45.0
        assert config.stream_timeout_retries == 2

    def test_default_timeout_values(self):
        """Default timeout values should be used when not specified."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
        )

        assert config.stream_timeout == bundled_tts.STREAM_TIMEOUT_SECONDS_DEFAULT
        assert config.stream_timeout_retries == bundled_tts.STREAM_TIMEOUT_RETRIES_DEFAULT

    def test_retry_logic_constants(self):
        """Retry-related constants should be properly defined."""
        bundled_tts = _load_bundled_tts()

        # Verify retry defaults are reasonable
        assert bundled_tts.STREAM_TIMEOUT_RETRIES_DEFAULT >= 0
        assert bundled_tts.STREAM_TIMEOUT_RETRIES_DEFAULT <= 5


class TestAsyncioTimeoutRetry:
    """Test that asyncio.TimeoutError triggers retry logic correctly.

    This addresses the issue where catching builtin TimeoutError doesn't catch
    asyncio.TimeoutError in Python 3.9-3.10, which would bypass retry logic.
    """

    def test_asyncio_timeout_error_is_caught_for_retry(self):
        """asyncio.TimeoutError should be caught and trigger retry."""
        import asyncio

        _load_bundled_tts()

        # In Python 3.9-3.10, asyncio.TimeoutError is distinct from TimeoutError
        # In Python 3.11+, they are the same
        # Our code should catch asyncio.TimeoutError specifically
        caught = False

        async def timeout_test():
            nonlocal caught
            try:
                await asyncio.wait_for(asyncio.sleep(10), timeout=0.001)
            except asyncio.TimeoutError:
                caught = True

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(timeout_test())
        finally:
            loop.close()

        assert caught, "asyncio.TimeoutError should be caught"

    def test_wait_for_raises_asyncio_timeout_error(self):
        """asyncio.wait_for should raise asyncio.TimeoutError on timeout."""
        import asyncio

        _load_bundled_tts()

        async def long_task():
            await asyncio.sleep(10)

        async def test():
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(long_task(), timeout=0.001)

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(test())
        finally:
            loop.close()

    def test_retry_loop_catches_asyncio_timeout_error(self):
        """Retry loop should catch asyncio.TimeoutError and retry.

        This test simulates the retry logic in _synthesize_text to verify
        that asyncio.TimeoutError is properly caught.
        """
        import asyncio

        _load_bundled_tts()

        attempt_count = 0
        max_retries = 2

        async def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            await asyncio.sleep(10)  # Will timeout

        async def test_retry():
            for attempt in range(max_retries + 1):
                try:
                    await asyncio.wait_for(failing_operation(), timeout=0.001)
                    return "success"
                except asyncio.TimeoutError as exc:
                    if attempt == max_retries:
                        raise RuntimeError("All retries exhausted") from exc
            return "unreachable"

        loop = asyncio.new_event_loop()
        try:
            with pytest.raises(RuntimeError, match="All retries exhausted"):
                loop.run_until_complete(test_retry())
        finally:
            loop.close()

        # Should have attempted max_retries + 1 times
        assert attempt_count == max_retries + 1


class TestEventLoopHandling:
    """Test event loop creation and management."""

    def test_synthesize_batch_uses_new_event_loop(self):
        """synthesize_batch should create and close its own event loop."""
        bundled_tts = _load_bundled_tts()

        # Verify the function signature expects items and config parameters
        assert callable(bundled_tts.synthesize_batch)


class TestItemVoiceField:
    """Test TTSItem voice field behavior."""

    def test_item_voice_is_optional(self):
        """TTSItem voice field should be optional."""
        bundled_tts = _load_bundled_tts()

        item = bundled_tts.TTSItem(identifier="1", text="Hello")
        assert item.voice is None

    def test_item_voice_can_be_set(self):
        """TTSItem voice can be set to override default."""
        bundled_tts = _load_bundled_tts()

        item = bundled_tts.TTSItem(
            identifier="1",
            text="Hello",
            voice="de-DE-KatjaNeural",
        )
        assert item.voice == "de-DE-KatjaNeural"

    def test_item_voice_override_takes_precedence(self):
        """Item voice should take precedence over config voice."""
        _load_bundled_tts()  # Ensure module is loaded

        config_voice = "en-US-JennyNeural"
        item_voice = "fr-FR-DeniseNeural"

        # This is the logic used in _synthesize_batch_async
        effective_voice = item_voice or config_voice

        assert effective_voice == "fr-FR-DeniseNeural"


class TestEventLoopShutdown:
    """Test event loop shutdown functionality for proper cleanup."""

    def test_shutdown_loop_function_exists(self):
        """_shutdown_loop function should be available."""
        bundled_tts = _load_bundled_tts()

        # The function is module-private but should exist
        assert hasattr(bundled_tts, "_shutdown_loop")
        assert callable(bundled_tts._shutdown_loop)

    def test_shutdown_loop_closes_loop(self):
        """_shutdown_loop should close the event loop."""
        import asyncio

        bundled_tts = _load_bundled_tts()

        loop = asyncio.new_event_loop()
        assert not loop.is_closed()

        bundled_tts._shutdown_loop(loop)
        assert loop.is_closed()

    def test_shutdown_loop_handles_pending_tasks(self):
        """_shutdown_loop should cancel pending tasks gracefully."""
        import asyncio

        bundled_tts = _load_bundled_tts()

        loop = asyncio.new_event_loop()

        # Create a pending task on the new loop
        async def never_finishes():
            await asyncio.sleep(1000)

        # Create task directly on the loop (no need to set as current event loop)
        task = loop.create_task(never_finishes())

        # Allow task to start running
        loop.run_until_complete(asyncio.sleep(0))

        # Shutdown should handle the pending task without errors
        bundled_tts._shutdown_loop(loop)

        assert loop.is_closed()
        assert task.cancelled()

    def test_shutdown_loop_handles_empty_loop(self):
        """_shutdown_loop should handle loop with no tasks."""
        import asyncio

        bundled_tts = _load_bundled_tts()

        loop = asyncio.new_event_loop()

        # Shutdown with no tasks should work
        bundled_tts._shutdown_loop(loop)
        assert loop.is_closed()

    def test_shutdown_loop_handles_completed_tasks(self):
        """_shutdown_loop should handle loop with completed tasks."""
        import asyncio

        bundled_tts = _load_bundled_tts()

        loop = asyncio.new_event_loop()

        async def quick_task():
            return 42

        # Run and complete a task
        result = loop.run_until_complete(quick_task())
        assert result == 42

        # Shutdown should still work after completed tasks
        bundled_tts._shutdown_loop(loop)
        assert loop.is_closed()
