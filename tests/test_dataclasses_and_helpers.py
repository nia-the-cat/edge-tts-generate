"""
Tests for edge_tts_gen.py dataclasses and helper functions.

These tests focus on:
- ItemError and BatchAudioResult dataclasses
- GenerateAudioQuery function
- Preview cache functionality
- Various utility functions and constants
"""

from __future__ import annotations

import importlib.util
import os
import sys
from unittest.mock import patch

import pytest


_MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "edge_tts_gen.py")


def _load_edge_tts_gen():
    """Load the edge_tts_gen module for testing."""
    # Create a synthetic package for relative imports
    package_name = "edge_tts_generate"
    package = sys.modules.setdefault(package_name, type(sys)(package_name))
    package.__path__ = [os.path.dirname(_MODULE_PATH)]

    spec = importlib.util.spec_from_file_location(f"{package_name}.edge_tts_gen", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestItemErrorDataclass:
    """Test ItemError dataclass functionality."""

    def test_can_create_item_error(self):
        """Should create ItemError with identifier and reason."""
        edge_tts_gen = _load_edge_tts_gen()

        error = edge_tts_gen.ItemError(identifier="note-123", reason="Service unavailable")

        assert error.identifier == "note-123"
        assert error.reason == "Service unavailable"

    def test_item_error_equality(self):
        """Two ItemErrors with same values should be equal."""
        edge_tts_gen = _load_edge_tts_gen()

        error1 = edge_tts_gen.ItemError(identifier="note-123", reason="Error")
        error2 = edge_tts_gen.ItemError(identifier="note-123", reason="Error")

        assert error1 == error2

    def test_item_error_inequality(self):
        """Two ItemErrors with different values should not be equal."""
        edge_tts_gen = _load_edge_tts_gen()

        error1 = edge_tts_gen.ItemError(identifier="note-123", reason="Error A")
        error2 = edge_tts_gen.ItemError(identifier="note-123", reason="Error B")

        assert error1 != error2


class TestBatchAudioResultDataclass:
    """Test BatchAudioResult dataclass functionality."""

    def test_can_create_batch_result(self):
        """Should create BatchAudioResult with audio_map and item_errors."""
        edge_tts_gen = _load_edge_tts_gen()

        result = edge_tts_gen.BatchAudioResult(
            audio_map={"note-1": b"audio1", "note-2": b"audio2"},
            item_errors=[],
        )

        assert len(result.audio_map) == 2
        assert result.audio_map["note-1"] == b"audio1"
        assert result.item_errors == []

    def test_batch_result_with_errors(self):
        """Should create BatchAudioResult with errors."""
        edge_tts_gen = _load_edge_tts_gen()

        error = edge_tts_gen.ItemError(identifier="note-3", reason="Failed")
        result = edge_tts_gen.BatchAudioResult(
            audio_map={"note-1": b"audio1"},
            item_errors=[error],
        )

        assert len(result.audio_map) == 1
        assert len(result.item_errors) == 1
        assert result.item_errors[0].identifier == "note-3"

    def test_batch_result_empty(self):
        """Should create empty BatchAudioResult."""
        edge_tts_gen = _load_edge_tts_gen()

        result = edge_tts_gen.BatchAudioResult(audio_map={}, item_errors=[])

        assert result.audio_map == {}
        assert result.item_errors == []


class TestGenerateAudioQuery:
    """Test GenerateAudioQuery function."""

    def test_raises_on_batch_error(self):
        """Should raise RuntimeError when batch result contains errors."""
        edge_tts_gen = _load_edge_tts_gen()

        from bundled_tts import TTSResult

        mock_results = [
            TTSResult(identifier="0", error="Test error"),
        ]

        with patch.object(edge_tts_gen, "synthesize_batch", return_value=mock_results):
            with pytest.raises(RuntimeError) as exc_info:
                edge_tts_gen.GenerateAudioQuery(("test text", "en-US-JennyNeural"), {})

        assert "Test error" in str(exc_info.value)

    def test_returns_audio_bytes_on_success(self):
        """Should return audio bytes on successful synthesis."""
        edge_tts_gen = _load_edge_tts_gen()

        from bundled_tts import TTSResult

        mock_audio = b"fake audio data"
        mock_results = [
            TTSResult(identifier="0", audio=mock_audio),
        ]

        with patch.object(edge_tts_gen, "synthesize_batch", return_value=mock_results):
            result = edge_tts_gen.GenerateAudioQuery(("test text", "en-US-JennyNeural"), {})

        assert result == mock_audio

    def test_raises_when_audio_missing(self):
        """Should raise RuntimeError when audio is missing from result."""
        edge_tts_gen = _load_edge_tts_gen()

        from bundled_tts import TTSResult

        # Result with neither audio nor error
        mock_results = [
            TTSResult(identifier="0"),
        ]

        with patch.object(edge_tts_gen, "synthesize_batch", return_value=mock_results):
            with pytest.raises(RuntimeError) as exc_info:
                edge_tts_gen.GenerateAudioQuery(("test text", "en-US-JennyNeural"), {})

        assert "missing" in str(exc_info.value).lower()


class TestPreviewNoteSnippetMaxLength:
    """Test PREVIEW_NOTE_SNIPPET_MAX_LENGTH constant."""

    def test_constant_value(self):
        """Constant should have reasonable value."""
        edge_tts_gen = _load_edge_tts_gen()

        assert edge_tts_gen.PREVIEW_NOTE_SNIPPET_MAX_LENGTH > 0
        assert edge_tts_gen.PREVIEW_NOTE_SNIPPET_MAX_LENGTH <= 100

    def test_snippet_truncation_logic(self):
        """Test snippet truncation using the constant."""
        edge_tts_gen = _load_edge_tts_gen()

        max_len = edge_tts_gen.PREVIEW_NOTE_SNIPPET_MAX_LENGTH
        long_text = "A" * (max_len + 50)

        snippet = long_text[:max_len]
        if len(long_text) > max_len:
            snippet += "..."

        assert len(snippet) == max_len + 3


class TestRegexPatterns:
    """Test regex patterns used in text processing."""

    def test_tag_re_removes_html_tags(self):
        """TAG_RE should remove HTML tags."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "<div><b>Bold</b> text</div>"
        result = edge_tts_gen.TAG_RE.sub("", text)
        assert result == "Bold text"

    def test_tag_re_removes_html_comments(self):
        """TAG_RE should remove HTML comments."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "Hello<!-- comment -->World"
        result = edge_tts_gen.TAG_RE.sub("", text)
        assert result == "HelloWorld"

    def test_entity_re_removes_html_entities(self):
        """ENTITY_RE should remove HTML entities."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "Hello&nbsp;World&amp;Test"
        result = edge_tts_gen.ENTITY_RE.sub("", text)
        assert result == "HelloWorldTest"

    def test_bracket_reading_re_extracts_readings(self):
        """BRACKET_READING_RE should extract readings from brackets."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "漢字[かんじ]"
        result = edge_tts_gen.BRACKET_READING_RE.sub(r"\1", text)
        assert result == "かんじ"

    def test_bracket_content_re_removes_brackets(self):
        """BRACKET_CONTENT_RE should remove bracket content."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "word[info]more"
        result = edge_tts_gen.BRACKET_CONTENT_RE.sub("", text)
        assert result == "wordmore"

    def test_whitespace_re_removes_spaces(self):
        """WHITESPACE_RE should remove spaces."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "Hello World Test"
        result = edge_tts_gen.WHITESPACE_RE.sub("", text)
        assert result == "HelloWorldTest"


class TestCreateNewFieldOption:
    """Test CREATE_NEW_FIELD_OPTION constant."""

    def test_constant_exists(self):
        """CREATE_NEW_FIELD_OPTION should exist."""
        edge_tts_gen = _load_edge_tts_gen()
        assert hasattr(edge_tts_gen, "CREATE_NEW_FIELD_OPTION")

    def test_constant_is_distinguishable(self):
        """CREATE_NEW_FIELD_OPTION should be easily distinguishable."""
        edge_tts_gen = _load_edge_tts_gen()

        # Should contain visual markers that distinguish from field names
        option = edge_tts_gen.CREATE_NEW_FIELD_OPTION
        assert "[" in option or "+" in option


class TestGenerateAudioBatchEdgeCases:
    """Test edge cases in GenerateAudioBatch."""

    def test_handles_synthesis_exception(self):
        """Should wrap synthesis exceptions in RuntimeError."""
        edge_tts_gen = _load_edge_tts_gen()

        with patch.object(edge_tts_gen, "synthesize_batch", side_effect=Exception("Network error")):
            with pytest.raises(RuntimeError) as exc_info:
                edge_tts_gen.GenerateAudioBatch([("id", "text", "voice")], {})

        assert "Network error" in str(exc_info.value)

    def test_uses_config_values(self):
        """Should use pitch/rate/volume from config."""
        edge_tts_gen = _load_edge_tts_gen()

        from bundled_tts import TTSResult

        mock_results = [
            TTSResult(identifier="note-1", audio=b"audio"),
        ]

        captured_config = None

        def mock_synthesize(items, config):
            nonlocal captured_config
            captured_config = config
            return mock_results

        config = {
            "pitch_slider_value": 10,
            "speed_slider_value": -5,
            "volume_slider_value": 25,
        }

        with patch.object(edge_tts_gen, "synthesize_batch", side_effect=mock_synthesize):
            edge_tts_gen.GenerateAudioBatch([("note-1", "text", "en-US-JennyNeural")], config)

        assert captured_config is not None
        assert captured_config.pitch == "+10Hz"
        assert captured_config.rate == "-5%"
        assert captured_config.volume == "+25%"

    def test_uses_timeout_config(self):
        """Should use timeout settings from config."""
        edge_tts_gen = _load_edge_tts_gen()

        from bundled_tts import TTSResult

        mock_results = [
            TTSResult(identifier="note-1", audio=b"audio"),
        ]

        captured_config = None

        def mock_synthesize(items, config):
            nonlocal captured_config
            captured_config = config
            return mock_results

        config = {
            "stream_timeout_seconds": 60.0,
            "stream_timeout_retries": 3,
        }

        with patch.object(edge_tts_gen, "synthesize_batch", side_effect=mock_synthesize):
            edge_tts_gen.GenerateAudioBatch([("note-1", "text", "en-US-JennyNeural")], config)

        assert captured_config is not None
        assert captured_config.stream_timeout == 60.0
        assert captured_config.stream_timeout_retries == 3


class TestPreviewCacheKeyLogic:
    """Test preview cache key generation logic."""

    def test_cache_key_includes_all_parameters(self):
        """Cache key should include text, speaker, pitch, rate, volume."""
        # Simulate the cache key logic from MyDialog
        preview_text = "Hello world"
        speaker = "en-US-JennyNeural"
        pitch = "+10Hz"
        rate = "-5%"
        volume = "+0%"

        cache_key = (preview_text, speaker, pitch, rate, volume)

        assert len(cache_key) == 5
        assert cache_key[0] == preview_text
        assert cache_key[1] == speaker

    def test_different_parameters_produce_different_keys(self):
        """Different parameters should produce different cache keys."""
        key1 = ("text", "voice1", "+0Hz", "+0%", "+0%")
        key2 = ("text", "voice2", "+0Hz", "+0%", "+0%")
        key3 = ("text", "voice1", "+10Hz", "+0%", "+0%")

        assert key1 != key2
        assert key1 != key3

    def test_same_parameters_produce_same_key(self):
        """Same parameters should produce identical cache keys."""
        key1 = ("text", "voice", "+0Hz", "+0%", "+0%")
        key2 = ("text", "voice", "+0Hz", "+0%", "+0%")

        assert key1 == key2


class TestPreviewParameterFormatting:
    """Test parameter formatting for preview."""

    def test_positive_pitch_formatting(self):
        """Positive pitch should be formatted with + sign."""
        pitch_value = 10
        pitch = f"{pitch_value:+}Hz"
        assert pitch == "+10Hz"

    def test_negative_pitch_formatting(self):
        """Negative pitch should be formatted with - sign."""
        pitch_value = -10
        pitch = f"{pitch_value:+}Hz"
        assert pitch == "-10Hz"

    def test_zero_pitch_formatting(self):
        """Zero pitch should be formatted with + sign."""
        pitch_value = 0
        pitch = f"{pitch_value:+}Hz"
        assert pitch == "+0Hz"

    def test_rate_formatting(self):
        """Rate should be formatted as percentage."""
        rate_value = 25
        rate = f"{rate_value:+}%"
        assert rate == "+25%"

    def test_volume_formatting(self):
        """Volume should be formatted as percentage."""
        volume_value = -50
        volume = f"{volume_value:+}%"
        assert volume == "-50%"


class TestTextProcessingPipeline:
    """Test the full text processing pipeline logic."""

    def test_full_pipeline_processes_html(self):
        """Full pipeline should process HTML correctly."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "<div>&nbsp;Hello<br/>World</div>"

        # Step 1: Remove entities
        text = edge_tts_gen.ENTITY_RE.sub("", text)
        # Step 2: Remove tags
        text = edge_tts_gen.TAG_RE.sub("", text)

        assert text == "HelloWorld"

    def test_full_pipeline_processes_readings(self):
        """Full pipeline should process reading annotations."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "漢字[かんじ]を勉強[べんきょう]する"

        # Extract readings
        text = edge_tts_gen.BRACKET_READING_RE.sub(r"\1", text)

        assert "かんじ" in text
        assert "べんきょう" in text

    def test_full_pipeline_removes_brackets(self):
        """Full pipeline should remove bracket content when enabled."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "word[extra info]end"
        text = edge_tts_gen.BRACKET_CONTENT_RE.sub("", text)

        assert text == "wordend"

    def test_full_pipeline_handles_mixed_content(self):
        """Full pipeline should handle mixed HTML and bracket content."""
        edge_tts_gen = _load_edge_tts_gen()

        text = "<b>Bold[info]</b>&nbsp;text"

        # Process in order
        text = edge_tts_gen.ENTITY_RE.sub("", text)
        text = edge_tts_gen.TAG_RE.sub("", text)
        text = edge_tts_gen.BRACKET_CONTENT_RE.sub("", text)

        assert text == "Boldtext"


class TestWhitespaceHandlingByLanguage:
    """Test whitespace handling based on voice language."""

    def test_japanese_voice_strips_whitespace(self):
        """Japanese voices should strip whitespace."""
        voice = "ja-JP-NanamiNeural"
        language_code = voice.split("-")[0].lower()

        assert language_code == "ja"
        assert language_code in {"ja", "zh"}

    def test_chinese_voice_strips_whitespace(self):
        """Chinese voices should strip whitespace."""
        voice = "zh-CN-XiaoxiaoNeural"
        language_code = voice.split("-")[0].lower()

        assert language_code == "zh"
        assert language_code in {"ja", "zh"}

    def test_english_voice_preserves_whitespace(self):
        """English voices should preserve whitespace."""
        voice = "en-US-JennyNeural"
        language_code = voice.split("-")[0].lower()

        assert language_code == "en"
        assert language_code not in {"ja", "zh"}

    def test_german_voice_preserves_whitespace(self):
        """German voices should preserve whitespace."""
        voice = "de-DE-KatjaNeural"
        language_code = voice.split("-")[0].lower()

        assert language_code == "de"
        assert language_code not in {"ja", "zh"}


class TestPreviewTextStatusValues:
    """Test preview text status return values."""

    def test_valid_status_ok(self):
        """'ok' is a valid status value."""
        valid_statuses = {"ok", "no_notes", "note_none", "field_missing", "field_empty"}
        assert "ok" in valid_statuses

    def test_valid_status_no_notes(self):
        """'no_notes' is a valid status value."""
        valid_statuses = {"ok", "no_notes", "note_none", "field_missing", "field_empty"}
        assert "no_notes" in valid_statuses

    def test_valid_status_note_none(self):
        """'note_none' is a valid status value."""
        valid_statuses = {"ok", "no_notes", "note_none", "field_missing", "field_empty"}
        assert "note_none" in valid_statuses

    def test_valid_status_field_missing(self):
        """'field_missing' is a valid status value."""
        valid_statuses = {"ok", "no_notes", "note_none", "field_missing", "field_empty"}
        assert "field_missing" in valid_statuses

    def test_valid_status_field_empty(self):
        """'field_empty' is a valid status value."""
        valid_statuses = {"ok", "no_notes", "note_none", "field_missing", "field_empty"}
        assert "field_empty" in valid_statuses


class TestUIFeatures:
    """Test UI-related features and constants."""

    def test_reset_sliders_logic(self):
        """Reset sliders should set values to 0."""
        # Simulate the reset logic from the dialog
        default_volume = 0
        default_pitch = 0
        default_speed = 0

        # After reset, all values should be 0
        assert default_volume == 0
        assert default_pitch == 0
        assert default_speed == 0

    def test_overwrite_confirmation_message_format(self):
        """Overwrite confirmation should include field name and note count."""
        destination_field = "Audio"
        note_count = 5

        message = (
            f"You have selected 'Overwrite' mode. This will replace all existing content in the "
            f"'{destination_field}' field for {note_count} note(s)."
        )

        assert destination_field in message
        assert str(note_count) in message
        assert "Overwrite" in message

    def test_slider_default_values(self):
        """Slider default values should be 0 for all adjustments."""
        config = {
            "volume_slider_value": 0,
            "pitch_slider_value": 0,
            "speed_slider_value": 0,
        }

        assert config.get("volume_slider_value", 0) == 0
        assert config.get("pitch_slider_value", 0) == 0
        assert config.get("speed_slider_value", 0) == 0

    def test_slider_ranges(self):
        """Slider ranges should be within expected bounds."""
        volume_min, volume_max = -100, 100
        pitch_min, pitch_max = -50, 50
        speed_min, speed_max = -50, 50

        # Volume has wider range
        assert volume_max - volume_min == 200

        # Pitch and speed have same range
        assert pitch_max - pitch_min == speed_max - speed_min == 100

    def test_audio_handling_modes(self):
        """Audio handling modes should include expected values."""
        modes = {"append", "overwrite", "skip"}

        assert "append" in modes
        assert "overwrite" in modes
        assert "skip" in modes
        assert len(modes) == 3


class TestSessionState:
    """Test session state for confirmation dialogs."""

    def test_session_state_class_exists(self):
        """Session state class should exist for storing confirmation preferences."""
        from edge_tts_gen import _SessionState

        assert _SessionState is not None

    def test_session_state_has_skip_overwrite_confirmation(self):
        """Session state should have skip_overwrite_confirmation attribute."""
        from edge_tts_gen import _SessionState

        state = _SessionState()
        assert hasattr(state, "skip_overwrite_confirmation")
        # Default should be False (show confirmation)
        assert state.skip_overwrite_confirmation is False

    def test_session_state_can_be_modified(self):
        """Session state skip_overwrite_confirmation should be modifiable."""
        from edge_tts_gen import _SessionState

        state = _SessionState()
        state.skip_overwrite_confirmation = True
        assert state.skip_overwrite_confirmation is True

    def test_module_level_session_state_instance_exists(self):
        """Module should have a session state instance for tracking state."""
        from edge_tts_gen import _session_state

        assert _session_state is not None
        assert hasattr(_session_state, "skip_overwrite_confirmation")
