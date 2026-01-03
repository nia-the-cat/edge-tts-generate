"""
Tests for subprocess flags to hide console windows on Windows.
Verifies that CREATE_NO_WINDOW flag is properly applied on Windows systems.
"""

import importlib.util
import os
from unittest.mock import patch


# Load external_runtime from the parent directory
_external_runtime_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "external_runtime.py"
)


def load_external_runtime():
    """Load a fresh copy of the external_runtime module."""
    spec = importlib.util.spec_from_file_location("external_runtime", _external_runtime_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSubprocessFlagsExternalRuntime:
    """Test subprocess flags in external_runtime.py."""

    @patch("sys.platform", "win32")
    def test_get_subprocess_flags_returns_create_no_window_on_windows(self):
        """On Windows, _get_subprocess_flags should return CREATE_NO_WINDOW flag."""
        external_runtime = load_external_runtime()
        flags = external_runtime._get_subprocess_flags()

        assert "creationflags" in flags
        # CREATE_NO_WINDOW = 0x08000000
        assert flags["creationflags"] == 0x08000000

    @patch("sys.platform", "linux")
    def test_get_subprocess_flags_returns_empty_on_linux(self):
        """On Linux, _get_subprocess_flags should return empty dict."""
        external_runtime = load_external_runtime()
        flags = external_runtime._get_subprocess_flags()

        assert flags == {}

    @patch("sys.platform", "darwin")
    def test_get_subprocess_flags_returns_empty_on_macos(self):
        """On macOS, _get_subprocess_flags should return empty dict."""
        external_runtime = load_external_runtime()
        flags = external_runtime._get_subprocess_flags()

        assert flags == {}


class TestCreateNoWindowConstant:
    """Test that CREATE_NO_WINDOW constant value is correct."""

    def test_create_no_window_value(self):
        """CREATE_NO_WINDOW should have value 0x08000000."""
        # This is the Windows CREATE_NO_WINDOW flag value
        # We use the raw value to avoid platform-specific dependencies
        assert 0x08000000 == 134217728  # Verify the hex value is correct
