"""
Tests for bundled_tts.py - TTS synthesis module using bundled edge-tts library.

These tests cover:
- Dataclasses (TTSConfig, TTSItem, TTSResult)
- Utility functions (results_to_json_list)
- Module constants and configuration
"""

from __future__ import annotations

import base64
import importlib.util
import os
import sys


_BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODULE_PATH = os.path.join(_BASE_PATH, "bundled_tts.py")


def _setup_bundled_tts_env():
    """Set up the environment for importing bundled_tts."""
    # Force pure Python mode for all packages
    os.environ["AIOHTTP_NO_EXTENSIONS"] = "1"
    os.environ["FROZENLIST_NO_EXTENSIONS"] = "1"
    os.environ["MULTIDICT_NO_EXTENSIONS"] = "1"
    os.environ["YARL_NO_EXTENSIONS"] = "1"
    os.environ["PROPCACHE_NO_EXTENSIONS"] = "1"

    # Add vendor directory to sys.path
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


class TestModuleConstants:
    """Test module constants and configuration values."""

    def test_batch_concurrency_limit_is_sensible(self):
        """Batch concurrency limit should be reasonable."""
        bundled_tts = _load_bundled_tts()
        assert bundled_tts.BATCH_CONCURRENCY_LIMIT >= 1
        assert bundled_tts.BATCH_CONCURRENCY_LIMIT <= 20

    def test_stream_timeout_default_is_sensible(self):
        """Default stream timeout should be reasonable."""
        bundled_tts = _load_bundled_tts()
        assert bundled_tts.STREAM_TIMEOUT_SECONDS_DEFAULT >= 10.0
        assert bundled_tts.STREAM_TIMEOUT_SECONDS_DEFAULT <= 120.0

    def test_stream_timeout_retries_default_is_sensible(self):
        """Default retry count should be reasonable."""
        bundled_tts = _load_bundled_tts()
        assert bundled_tts.STREAM_TIMEOUT_RETRIES_DEFAULT >= 0
        assert bundled_tts.STREAM_TIMEOUT_RETRIES_DEFAULT <= 5


class TestTTSConfigDataclass:
    """Test TTSConfig dataclass functionality."""

    def test_can_create_with_required_fields(self):
        """Should create TTSConfig with required fields."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
        )

        assert config.voice == "en-US-JennyNeural"
        assert config.pitch == "+0Hz"
        assert config.rate == "+0%"
        assert config.volume == "+0%"

    def test_has_default_stream_timeout(self):
        """TTSConfig should have default stream_timeout."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
        )

        assert config.stream_timeout == bundled_tts.STREAM_TIMEOUT_SECONDS_DEFAULT

    def test_has_default_stream_timeout_retries(self):
        """TTSConfig should have default stream_timeout_retries."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
        )

        assert config.stream_timeout_retries == bundled_tts.STREAM_TIMEOUT_RETRIES_DEFAULT

    def test_can_override_defaults(self):
        """Should be able to override default values."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="+0%",
            stream_timeout=60.0,
            stream_timeout_retries=3,
        )

        assert config.stream_timeout == 60.0
        assert config.stream_timeout_retries == 3


class TestTTSItemDataclass:
    """Test TTSItem dataclass functionality."""

    def test_can_create_with_required_fields(self):
        """Should create TTSItem with required fields."""
        bundled_tts = _load_bundled_tts()

        item = bundled_tts.TTSItem(identifier="item-1", text="Hello world")

        assert item.identifier == "item-1"
        assert item.text == "Hello world"

    def test_has_optional_voice_field(self):
        """TTSItem should have optional voice field."""
        bundled_tts = _load_bundled_tts()

        item = bundled_tts.TTSItem(identifier="item-1", text="Hello")
        assert item.voice is None

        item_with_voice = bundled_tts.TTSItem(
            identifier="item-2", text="Hello", voice="en-US-GuyNeural"
        )
        assert item_with_voice.voice == "en-US-GuyNeural"

    def test_identifier_can_be_any_string(self):
        """Identifier can be any string format."""
        bundled_tts = _load_bundled_tts()

        # UUID-like
        item1 = bundled_tts.TTSItem(identifier="123e4567-e89b-12d3-a456", text="Test")
        assert item1.identifier == "123e4567-e89b-12d3-a456"

        # Note ID-like
        item2 = bundled_tts.TTSItem(identifier="note-12345", text="Test")
        assert item2.identifier == "note-12345"

        # Simple number string
        item3 = bundled_tts.TTSItem(identifier="0", text="Test")
        assert item3.identifier == "0"


class TestTTSResultDataclass:
    """Test TTSResult dataclass functionality."""

    def test_can_create_with_identifier_only(self):
        """Should create TTSResult with just identifier."""
        bundled_tts = _load_bundled_tts()

        result = bundled_tts.TTSResult(identifier="result-1")

        assert result.identifier == "result-1"
        assert result.audio is None
        assert result.error is None

    def test_can_create_successful_result(self):
        """Should create TTSResult with audio data."""
        bundled_tts = _load_bundled_tts()

        result = bundled_tts.TTSResult(identifier="result-1", audio=b"audio_data")

        assert result.identifier == "result-1"
        assert result.audio == b"audio_data"
        assert result.error is None

    def test_can_create_error_result(self):
        """Should create TTSResult with error."""
        bundled_tts = _load_bundled_tts()

        result = bundled_tts.TTSResult(identifier="result-1", error="Service unavailable")

        assert result.identifier == "result-1"
        assert result.audio is None
        assert result.error == "Service unavailable"


class TestResultsToJsonList:
    """Test results_to_json_list utility function."""

    def test_converts_successful_result(self):
        """Should convert successful result to JSON format with base64 audio."""
        bundled_tts = _load_bundled_tts()

        audio_data = b"fake audio content"
        result = bundled_tts.TTSResult(identifier="item-1", audio=audio_data)
        json_list = bundled_tts.results_to_json_list([result])

        assert len(json_list) == 1
        assert json_list[0]["id"] == "item-1"
        assert "audio" in json_list[0]
        # Verify base64 encoding
        decoded = base64.b64decode(json_list[0]["audio"])
        assert decoded == audio_data

    def test_converts_error_result(self):
        """Should convert error result to JSON format."""
        bundled_tts = _load_bundled_tts()

        result = bundled_tts.TTSResult(identifier="item-1", error="Test error")
        json_list = bundled_tts.results_to_json_list([result])

        assert len(json_list) == 1
        assert json_list[0]["id"] == "item-1"
        assert json_list[0]["error"] == "Test error"

    def test_converts_mixed_results(self):
        """Should convert a mix of successful and error results."""
        bundled_tts = _load_bundled_tts()

        results = [
            bundled_tts.TTSResult(identifier="item-1", audio=b"audio1"),
            bundled_tts.TTSResult(identifier="item-2", error="Error for item 2"),
            bundled_tts.TTSResult(identifier="item-3", audio=b"audio3"),
        ]
        json_list = bundled_tts.results_to_json_list(results)

        assert len(json_list) == 3
        assert "audio" in json_list[0]
        assert "error" in json_list[1]
        assert "audio" in json_list[2]

    def test_handles_empty_list(self):
        """Should handle empty results list."""
        bundled_tts = _load_bundled_tts()

        json_list = bundled_tts.results_to_json_list([])
        assert json_list == []

    def test_skips_results_with_neither_audio_nor_error(self):
        """Should skip results that have neither audio nor error."""
        bundled_tts = _load_bundled_tts()

        # This shouldn't normally happen, but the function handles it
        result = bundled_tts.TTSResult(identifier="item-1")
        json_list = bundled_tts.results_to_json_list([result])

        assert json_list == []


class TestVendorPathSetup:
    """Test that vendor path setup works correctly."""

    def test_vendor_directory_exists(self):
        """Vendor directory should exist."""
        vendor_dir = os.path.join(_BASE_PATH, "vendor")
        assert os.path.isdir(vendor_dir)

    def test_edge_tts_package_is_vendored(self):
        """edge_tts package should be in vendor directory."""
        edge_tts_dir = os.path.join(_BASE_PATH, "vendor", "edge_tts")
        assert os.path.isdir(edge_tts_dir)

    def test_can_import_edge_tts_after_setup(self):
        """Should be able to import edge_tts after setting up vendor path."""
        _setup_bundled_tts_env()
        import edge_tts

        assert edge_tts is not None


class TestEnvironmentVariables:
    """Test that environment variables are properly set."""

    def test_aiohttp_no_extensions_is_set(self):
        """AIOHTTP_NO_EXTENSIONS should be set."""
        _setup_bundled_tts_env()
        assert os.environ.get("AIOHTTP_NO_EXTENSIONS") == "1"

    def test_frozenlist_no_extensions_is_set(self):
        """FROZENLIST_NO_EXTENSIONS should be set."""
        _setup_bundled_tts_env()
        assert os.environ.get("FROZENLIST_NO_EXTENSIONS") == "1"

    def test_multidict_no_extensions_is_set(self):
        """MULTIDICT_NO_EXTENSIONS should be set."""
        _setup_bundled_tts_env()
        assert os.environ.get("MULTIDICT_NO_EXTENSIONS") == "1"

    def test_yarl_no_extensions_is_set(self):
        """YARL_NO_EXTENSIONS should be set."""
        _setup_bundled_tts_env()
        assert os.environ.get("YARL_NO_EXTENSIONS") == "1"

    def test_propcache_no_extensions_is_set(self):
        """PROPCACHE_NO_EXTENSIONS should be set."""
        _setup_bundled_tts_env()
        assert os.environ.get("PROPCACHE_NO_EXTENSIONS") == "1"


class TestTTSConfigEquality:
    """Test TTSConfig dataclass equality behavior."""

    def test_equal_configs_are_equal(self):
        """Two TTSConfig instances with same values should be equal."""
        bundled_tts = _load_bundled_tts()

        config1 = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural", pitch="+0Hz", rate="+0%", volume="+0%"
        )
        config2 = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural", pitch="+0Hz", rate="+0%", volume="+0%"
        )

        assert config1 == config2

    def test_different_configs_are_not_equal(self):
        """Two TTSConfig instances with different values should not be equal."""
        bundled_tts = _load_bundled_tts()

        config1 = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural", pitch="+0Hz", rate="+0%", volume="+0%"
        )
        config2 = bundled_tts.TTSConfig(
            voice="en-US-GuyNeural", pitch="+0Hz", rate="+0%", volume="+0%"
        )

        assert config1 != config2


class TestTTSItemEquality:
    """Test TTSItem dataclass equality behavior."""

    def test_equal_items_are_equal(self):
        """Two TTSItem instances with same values should be equal."""
        bundled_tts = _load_bundled_tts()

        item1 = bundled_tts.TTSItem(identifier="1", text="Hello")
        item2 = bundled_tts.TTSItem(identifier="1", text="Hello")

        assert item1 == item2

    def test_different_items_are_not_equal(self):
        """Two TTSItem instances with different values should not be equal."""
        bundled_tts = _load_bundled_tts()

        item1 = bundled_tts.TTSItem(identifier="1", text="Hello")
        item2 = bundled_tts.TTSItem(identifier="2", text="Hello")

        assert item1 != item2


class TestTTSResultEquality:
    """Test TTSResult dataclass equality behavior."""

    def test_equal_results_are_equal(self):
        """Two TTSResult instances with same values should be equal."""
        bundled_tts = _load_bundled_tts()

        result1 = bundled_tts.TTSResult(identifier="1", audio=b"data")
        result2 = bundled_tts.TTSResult(identifier="1", audio=b"data")

        assert result1 == result2

    def test_different_results_are_not_equal(self):
        """Two TTSResult instances with different values should not be equal."""
        bundled_tts = _load_bundled_tts()

        result1 = bundled_tts.TTSResult(identifier="1", audio=b"data")
        result2 = bundled_tts.TTSResult(identifier="1", error="error")

        assert result1 != result2


class TestVoiceParameterFormats:
    """Test voice parameter formatting for TTSConfig."""

    def test_positive_pitch_format(self):
        """Positive pitch values should use +Hz format."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+10Hz",
            rate="+0%",
            volume="+0%",
        )

        assert config.pitch == "+10Hz"
        assert config.pitch.startswith("+")
        assert config.pitch.endswith("Hz")

    def test_negative_pitch_format(self):
        """Negative pitch values should use -Hz format."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="-10Hz",
            rate="+0%",
            volume="+0%",
        )

        assert config.pitch == "-10Hz"
        assert config.pitch.startswith("-")
        assert config.pitch.endswith("Hz")

    def test_rate_percentage_format(self):
        """Rate should use percentage format."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+25%",
            volume="+0%",
        )

        assert config.rate == "+25%"
        assert config.rate.endswith("%")

    def test_volume_percentage_format(self):
        """Volume should use percentage format."""
        bundled_tts = _load_bundled_tts()

        config = bundled_tts.TTSConfig(
            voice="en-US-JennyNeural",
            pitch="+0Hz",
            rate="+0%",
            volume="-50%",
        )

        assert config.volume == "-50%"
        assert config.volume.endswith("%")
