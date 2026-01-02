"""
Pytest configuration for edge-tts-generate tests.
"""

import sys
from unittest.mock import MagicMock


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
    ]

    for module_name in mock_modules:
        sys.modules[module_name] = MagicMock()
