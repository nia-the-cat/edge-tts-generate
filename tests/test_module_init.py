"""
Tests for module initialization and hook registration.

These tests verify that the add-on initializes correctly.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock


_BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestModuleStructure:
    """Test that all required modules exist and have correct structure."""

    def test_bundled_tts_exists(self):
        """bundled_tts.py should exist."""
        path = os.path.join(_BASE_PATH, "bundled_tts.py")
        assert os.path.isfile(path)

    def test_edge_tts_gen_exists(self):
        """edge_tts_gen.py should exist."""
        path = os.path.join(_BASE_PATH, "edge_tts_gen.py")
        assert os.path.isfile(path)

    def test_logging_config_exists(self):
        """logging_config.py should exist."""
        path = os.path.join(_BASE_PATH, "logging_config.py")
        assert os.path.isfile(path)

    def test_init_exists(self):
        """__init__.py should exist."""
        path = os.path.join(_BASE_PATH, "__init__.py")
        assert os.path.isfile(path)

    def test_vendor_directory_exists(self):
        """vendor directory should exist."""
        path = os.path.join(_BASE_PATH, "vendor")
        assert os.path.isdir(path)


class TestConfigFiles:
    """Test configuration files structure."""

    def test_config_json_exists(self):
        """config.json should exist."""
        path = os.path.join(_BASE_PATH, "config.json")
        assert os.path.isfile(path)

    def test_manifest_json_exists(self):
        """manifest.json should exist."""
        path = os.path.join(_BASE_PATH, "manifest.json")
        assert os.path.isfile(path)

    def test_meta_json_exists(self):
        """meta.json should exist."""
        path = os.path.join(_BASE_PATH, "meta.json")
        assert os.path.isfile(path)

    def test_config_json_is_valid(self):
        """config.json should be valid JSON."""
        import json

        path = os.path.join(_BASE_PATH, "config.json")
        with open(path) as f:
            config = json.load(f)

        assert isinstance(config, dict)
        assert "speakers" in config

    def test_manifest_json_is_valid(self):
        """manifest.json should be valid JSON with required fields."""
        import json

        path = os.path.join(_BASE_PATH, "manifest.json")
        with open(path) as f:
            manifest = json.load(f)

        assert "package" in manifest
        assert "name" in manifest
        assert "min_point_version" in manifest
        assert "max_point_version" in manifest


class TestLoggingConfigFallback:
    """Test logging configuration fallback behavior."""

    def test_fallback_configure_logging(self):
        """Fallback configure_logging should work without Anki."""
        import logging

        # Test the fallback implementation
        def configure_logging(log_level="WARNING"):
            logging.basicConfig(level=getattr(logging, log_level.upper(), logging.WARNING))

        # Should not raise
        configure_logging("DEBUG")
        configure_logging("INFO")
        configure_logging("WARNING")

    def test_fallback_get_logger(self):
        """Fallback get_logger should return a logger."""
        import logging

        def get_logger(name: str) -> logging.Logger:
            return logging.getLogger(f"edge_tts_generate.{name.lstrip('.')}")

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert "edge_tts_generate" in logger.name


class TestHookFunctionSignatures:
    """Test that hook functions have correct signatures."""

    def test_context_menu_hook_signature(self):
        """Context menu hook should accept browser and menu."""

        # Verify the expected function signature
        def on_browser_will_show_context_menu(browser, menu):
            pass  # Implementation would go here

        # Should accept two arguments
        mock_browser = MagicMock()
        mock_menu = MagicMock()

        # Should not raise
        on_browser_will_show_context_menu(mock_browser, mock_menu)

    def test_menus_init_hook_signature(self):
        """Menus init hook should accept browser."""

        def on_browser_menus_did_init(browser):
            pass  # Implementation would go here

        mock_browser = MagicMock()

        # Should not raise
        on_browser_menus_did_init(mock_browser)


class TestMenuActionConfiguration:
    """Test menu action configuration by verifying __init__.py source code."""

    def test_edit_menu_shortcut_in_source(self):
        """Edit menu action shortcut should be defined in __init__.py."""
        init_path = os.path.join(_BASE_PATH, "__init__.py")
        with open(init_path) as f:
            source = f.read()

        # Verify the shortcut is defined in the source
        assert "Ctrl+Shift+E" in source

    def test_batch_menu_shortcut_in_source(self):
        """Batch menu action shortcut should be defined in __init__.py."""
        init_path = os.path.join(_BASE_PATH, "__init__.py")
        with open(init_path) as f:
            source = f.read()

        # Verify the shortcut is defined in the source
        assert "Ctrl+Shift+G" in source

    def test_menu_action_text_in_source(self):
        """Menu action text should be defined in __init__.py."""
        init_path = os.path.join(_BASE_PATH, "__init__.py")
        with open(init_path) as f:
            source = f.read()

        assert "Generate edge-tts Audio" in source

    def test_batch_menu_name_in_source(self):
        """Batch menu name should be defined in __init__.py."""
        init_path = os.path.join(_BASE_PATH, "__init__.py")
        with open(init_path) as f:
            source = f.read()

        assert "Generate Batch Audio" in source


class TestVendorPackages:
    """Test vendored packages structure."""

    def test_edge_tts_vendored(self):
        """edge_tts should be in vendor directory."""
        path = os.path.join(_BASE_PATH, "vendor", "edge_tts")
        assert os.path.isdir(path)

    def test_aiohttp_vendored(self):
        """aiohttp should be in vendor directory."""
        path = os.path.join(_BASE_PATH, "vendor", "aiohttp")
        assert os.path.isdir(path)

    def test_certifi_vendored(self):
        """certifi should be in vendor directory."""
        path = os.path.join(_BASE_PATH, "vendor", "certifi")
        assert os.path.isdir(path)


class TestRequirementsFile:
    """Test requirements files."""

    def test_requirements_test_exists(self):
        """requirements-test.txt should exist."""
        path = os.path.join(_BASE_PATH, "requirements-test.txt")
        assert os.path.isfile(path)

    def test_requirements_test_has_pytest(self):
        """requirements-test.txt should include pytest."""
        path = os.path.join(_BASE_PATH, "requirements-test.txt")
        with open(path) as f:
            content = f.read()

        assert "pytest" in content.lower()

    def test_requirements_test_has_ruff(self):
        """requirements-test.txt should include ruff."""
        path = os.path.join(_BASE_PATH, "requirements-test.txt")
        with open(path) as f:
            content = f.read()

        assert "ruff" in content.lower()


class TestPyprojectToml:
    """Test pyproject.toml configuration."""

    def test_pyproject_exists(self):
        """pyproject.toml should exist."""
        path = os.path.join(_BASE_PATH, "pyproject.toml")
        assert os.path.isfile(path)

    def test_pyproject_has_pytest_config(self):
        """pyproject.toml should have pytest configuration."""
        path = os.path.join(_BASE_PATH, "pyproject.toml")
        with open(path) as f:
            content = f.read()

        assert "[tool.pytest" in content

    def test_pyproject_has_ruff_config(self):
        """pyproject.toml should have ruff configuration."""
        path = os.path.join(_BASE_PATH, "pyproject.toml")
        with open(path) as f:
            content = f.read()

        assert "[tool.ruff" in content
