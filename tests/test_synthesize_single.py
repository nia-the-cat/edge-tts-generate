"""
Tests for synthesize_single function in bundled_tts.py.

This module tests the single-text synthesis functionality.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from unittest.mock import patch

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


class TestSynthesizeSingle:
    """Test synthesize_single function."""

    def test_calls_synthesize_batch_with_single_item(self):
        """synthesize_single should call synthesize_batch with one item."""
        bundled_tts = _load_bundled_tts()

        mock_result = bundled_tts.TTSResult(identifier="0", audio=b"audio_data")

        with patch.object(bundled_tts, "synthesize_batch", return_value=[mock_result]) as mock_batch:
            config = bundled_tts.TTSConfig(
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )
            bundled_tts.synthesize_single("Hello world", config)

            # Verify synthesize_batch was called
            mock_batch.assert_called_once()
            call_args = mock_batch.call_args
            items = call_args[0][0]
            assert len(items) == 1
            assert items[0].identifier == "0"
            assert items[0].text == "Hello world"

    def test_returns_audio_bytes_on_success(self):
        """Should return audio bytes when synthesis succeeds."""
        bundled_tts = _load_bundled_tts()

        expected_audio = b"fake audio bytes"
        mock_result = bundled_tts.TTSResult(identifier="0", audio=expected_audio)

        with patch.object(bundled_tts, "synthesize_batch", return_value=[mock_result]):
            config = bundled_tts.TTSConfig(
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )
            result = bundled_tts.synthesize_single("Test text", config)

            assert result == expected_audio

    def test_raises_on_error_result(self):
        """Should raise RuntimeError when result contains error."""
        bundled_tts = _load_bundled_tts()

        mock_result = bundled_tts.TTSResult(identifier="0", error="Synthesis failed")

        with patch.object(bundled_tts, "synthesize_batch", return_value=[mock_result]):
            config = bundled_tts.TTSConfig(
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            with pytest.raises(RuntimeError) as exc_info:
                bundled_tts.synthesize_single("Test text", config)

            assert "Synthesis failed" in str(exc_info.value)

    def test_raises_when_no_audio_returned(self):
        """Should raise RuntimeError when no audio is returned."""
        bundled_tts = _load_bundled_tts()

        # Result with neither audio nor error
        mock_result = bundled_tts.TTSResult(identifier="0")

        with patch.object(bundled_tts, "synthesize_batch", return_value=[mock_result]):
            config = bundled_tts.TTSConfig(
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            with pytest.raises(RuntimeError) as exc_info:
                bundled_tts.synthesize_single("Test text", config)

            assert "No audio returned" in str(exc_info.value)

    def test_raises_on_empty_results(self):
        """Should raise RuntimeError when results list is empty."""
        bundled_tts = _load_bundled_tts()

        with patch.object(bundled_tts, "synthesize_batch", return_value=[]):
            config = bundled_tts.TTSConfig(
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )

            with pytest.raises(RuntimeError):
                bundled_tts.synthesize_single("Test text", config)


class TestSynthesizeSingleWithConfig:
    """Test that synthesize_single properly passes config."""

    def test_passes_voice_config(self):
        """Should pass voice from config to batch synthesis."""
        bundled_tts = _load_bundled_tts()

        mock_result = bundled_tts.TTSResult(identifier="0", audio=b"audio")
        captured_config = None

        def capture_config(items, config):
            nonlocal captured_config
            captured_config = config
            return [mock_result]

        with patch.object(bundled_tts, "synthesize_batch", side_effect=capture_config):
            config = bundled_tts.TTSConfig(
                voice="ja-JP-NanamiNeural",
                pitch="+10Hz",
                rate="-5%",
                volume="+20%",
            )
            bundled_tts.synthesize_single("こんにちは", config)

            assert captured_config.voice == "ja-JP-NanamiNeural"
            assert captured_config.pitch == "+10Hz"
            assert captured_config.rate == "-5%"
            assert captured_config.volume == "+20%"

    def test_passes_timeout_config(self):
        """Should pass timeout settings from config."""
        bundled_tts = _load_bundled_tts()

        mock_result = bundled_tts.TTSResult(identifier="0", audio=b"audio")
        captured_config = None

        def capture_config(items, config):
            nonlocal captured_config
            captured_config = config
            return [mock_result]

        with patch.object(bundled_tts, "synthesize_batch", side_effect=capture_config):
            config = bundled_tts.TTSConfig(
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
                stream_timeout=60.0,
                stream_timeout_retries=3,
            )
            bundled_tts.synthesize_single("Hello", config)

            assert captured_config.stream_timeout == 60.0
            assert captured_config.stream_timeout_retries == 3


class TestSynthesizeSingleIdentifier:
    """Test identifier handling in synthesize_single."""

    def test_uses_identifier_zero(self):
        """synthesize_single should always use identifier '0'."""
        bundled_tts = _load_bundled_tts()

        mock_result = bundled_tts.TTSResult(identifier="0", audio=b"audio")
        captured_items = None

        def capture_items(items, config):
            nonlocal captured_items
            captured_items = items
            return [mock_result]

        with patch.object(bundled_tts, "synthesize_batch", side_effect=capture_items):
            config = bundled_tts.TTSConfig(
                voice="en-US-JennyNeural",
                pitch="+0Hz",
                rate="+0%",
                volume="+0%",
            )
            bundled_tts.synthesize_single("Test", config)

            assert len(captured_items) == 1
            assert captured_items[0].identifier == "0"
