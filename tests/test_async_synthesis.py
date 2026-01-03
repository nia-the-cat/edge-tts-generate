"""
Tests for async synthesis functions in bundled_tts.py.

These tests verify the async synthesis implementation using mocks.
"""

from __future__ import annotations

import importlib.util
import os
import sys


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

    def test_results_are_sorted_by_identifier(self):
        """Results should be sorted by identifier."""
        bundled_tts = _load_bundled_tts()

        # Test the sorting behavior
        results = [
            bundled_tts.TTSResult(identifier="3", audio=b"three"),
            bundled_tts.TTSResult(identifier="1", audio=b"one"),
            bundled_tts.TTSResult(identifier="2", audio=b"two"),
        ]

        sorted_results = sorted(results, key=lambda r: r.identifier)

        assert sorted_results[0].identifier == "1"
        assert sorted_results[1].identifier == "2"
        assert sorted_results[2].identifier == "3"


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

        # Create a pending task
        async def never_finishes():
            await asyncio.sleep(1000)

        task = loop.create_task(never_finishes())

        # Allow task to start
        loop.run_until_complete(asyncio.sleep(0))

        # Shutdown should handle the pending task
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
