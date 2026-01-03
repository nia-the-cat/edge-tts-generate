"""Tests for GenerateAudioBatch error handling."""

import json
import os
import importlib.util
import sys
from types import SimpleNamespace

import pytest


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
    """An error entry in the batch result should raise an item-specific exception."""

    edge_tts_gen = _load_edge_tts_gen()

    monkeypatch.setattr(edge_tts_gen, "get_external_python", lambda _addon_dir: "python")

    batch_response = json.dumps([
        {"id": "note-123", "error": "Service unavailable"},
        {"id": "note-456", "audio": ""},
    ])

    mock_completed = SimpleNamespace(stdout=batch_response, stderr="", returncode=0)

    monkeypatch.setattr(edge_tts_gen.subprocess, "run", lambda *args, **kwargs: mock_completed)

    with pytest.raises(Exception) as excinfo:
        edge_tts_gen.GenerateAudioBatch([("note-123", "text", "voice")], {})

    assert "note-123" in str(excinfo.value)
    assert "Service unavailable" in str(excinfo.value)
    assert "note-456" in str(excinfo.value)
    assert "Missing audio data" in str(excinfo.value)
