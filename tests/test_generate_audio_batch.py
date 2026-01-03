"""Tests for GenerateAudioBatch error handling."""

import importlib.util
import os
import sys
from unittest.mock import patch


_MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "edge_tts_gen.py")


def _load_edge_tts_gen():
    """Load the edge_tts_gen module as part of a synthetic package for testing."""

    package_name = "edge_tts_generate"
    package = sys.modules.setdefault(package_name, type(sys)(package_name))
    package.__path__ = [os.path.dirname(_MODULE_PATH)]

    spec = importlib.util.spec_from_file_location(f"{package_name}.edge_tts_gen", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_audio_batch_reports_item_errors(monkeypatch):
    """An error entry in the batch result should be returned for caller handling."""

    edge_tts_gen = _load_edge_tts_gen()

    # Mock the bundled_tts module's synthesize_batch function
    from bundled_tts import TTSResult

    mock_results = [
        TTSResult(identifier="note-123", error="Service unavailable"),
        TTSResult(identifier="note-456", audio=None, error=None),  # Missing audio data
    ]

    with patch.object(edge_tts_gen, "synthesize_batch", return_value=mock_results):
        result = edge_tts_gen.GenerateAudioBatch([("note-123", "text", "voice")], {})

    assert result.audio_map == {}
    assert len(result.item_errors) == 2
    assert result.item_errors[0].identifier == "note-123"
    assert result.item_errors[0].reason == "Service unavailable"
    assert result.item_errors[1].identifier == "note-456"
    assert "Missing audio data" in result.item_errors[1].reason


def test_generate_audio_batch_returns_audio_on_success(monkeypatch):
    """Successful audio generation should return audio bytes in audio_map."""

    edge_tts_gen = _load_edge_tts_gen()

    from bundled_tts import TTSResult

    mock_audio = b"fake audio data"
    mock_results = [
        TTSResult(identifier="note-123", audio=mock_audio),
    ]

    with patch.object(edge_tts_gen, "synthesize_batch", return_value=mock_results):
        result = edge_tts_gen.GenerateAudioBatch([("note-123", "text", "voice")], {})

    assert "note-123" in result.audio_map
    assert result.audio_map["note-123"] == mock_audio
    assert len(result.item_errors) == 0


def test_generate_audio_batch_handles_empty_items():
    """Empty items list should return empty result."""

    edge_tts_gen = _load_edge_tts_gen()

    result = edge_tts_gen.GenerateAudioBatch([], {})

    assert result.audio_map == {}
    assert result.item_errors == []
