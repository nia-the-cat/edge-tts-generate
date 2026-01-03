"""Tests for GenerateAudioBatch error handling."""

import importlib.util
import json
import os
import sys
from types import SimpleNamespace


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

    monkeypatch.setattr(edge_tts_gen, "get_external_python", lambda _addon_dir: "python")

    batch_response = json.dumps(
        [
            {"id": "note-123", "error": "Service unavailable"},
            {"id": "note-456", "audio": ""},
        ]
    )

    mock_completed = SimpleNamespace(stdout=batch_response, stderr="", returncode=0)

    monkeypatch.setattr(edge_tts_gen.subprocess, "run", lambda *args, **kwargs: mock_completed)

    result = edge_tts_gen.GenerateAudioBatch([("note-123", "text", "voice")], {})

    assert result.audio_map == {}
    assert len(result.item_errors) == 2
    assert result.item_errors[0].identifier == "note-123"
    assert result.item_errors[0].reason == "Service unavailable"
    assert result.item_errors[1].identifier == "note-456"
    assert "Missing audio data" in result.item_errors[1].reason
