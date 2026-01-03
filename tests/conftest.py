"""
Pytest configuration for edge-tts-generate tests.

This module provides:
- Mock Anki modules for testing without Anki installed
- Shared fixtures for test data
- Test configuration and markers
"""

import os
import sys
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    """Configure pytest to mock Anki modules before tests run."""
    # Mock Anki modules that are not available in the test environment
    # This prevents import errors when tests try to import the addon modules
    mock_modules = [
        "aqt",
        "aqt.qt",
        "aqt.browser",
        "aqt.gui_hooks",
        "aqt.sound",
        "aqt.utils",
    ]

    for module_name in mock_modules:
        sys.modules[module_name] = MagicMock()


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return {
        "last_destination_field": "Audio",
        "last_source_field": "Front",
        "last_speaker_name": "en-US-JennyNeural",
        "pitch_slider_value": 0,
        "speakers": ["en-US-JennyNeural", "en-US-GuyNeural"],
        "speed_slider_value": 0,
        "volume_slider_value": 0,
        "ignore_brackets_enabled": True,
        "last_audio_handling": "append",
    }


@pytest.fixture
def sample_voices():
    """Provide a list of sample voice names for testing."""
    return [
        "en-US-JennyNeural",
        "en-US-GuyNeural",
        "ja-JP-NanamiNeural",
        "zh-CN-XiaoxiaoNeural",
        "de-DE-KatjaNeural",
    ]


@pytest.fixture
def base_path():
    """Return the base path of the addon."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def mock_note():
    """Provide a mock Anki note object."""
    note = MagicMock()
    note.__getitem__ = MagicMock(return_value="Sample text content")
    note.note_type.return_value = {"id": 1, "flds": [{"name": "Front"}, {"name": "Back"}, {"name": "Audio"}]}
    return note
