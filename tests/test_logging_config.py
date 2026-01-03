"""
Tests for the logging_config module.
Verifies that the logging system is properly configured and functions correctly.
"""

import importlib.util
import logging
import os
import tempfile
from unittest.mock import MagicMock, patch


_MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logging_config.py")


def load_logging_config():
    """Load a fresh copy of the logging_config module."""
    spec = importlib.util.spec_from_file_location("logging_config", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestLoggingConfigConstants:
    """Test logging configuration constants."""

    def test_default_log_level_is_warning(self):
        """Default log level should be WARNING for production use."""
        logging_config = load_logging_config()
        assert logging_config.DEFAULT_LOG_LEVEL == "WARNING"

    def test_default_max_log_size_is_sensible(self):
        """Default max log size should be reasonable (5MB)."""
        logging_config = load_logging_config()
        assert logging_config.DEFAULT_MAX_LOG_SIZE_MB == 5

    def test_default_backup_count_is_sensible(self):
        """Default backup count should be reasonable (3 files)."""
        logging_config = load_logging_config()
        assert logging_config.DEFAULT_LOG_BACKUP_COUNT == 3

    def test_log_filename_is_descriptive(self):
        """Log filename should be descriptive."""
        logging_config = load_logging_config()
        assert "edge_tts" in logging_config.LOG_FILENAME
        assert logging_config.LOG_FILENAME.endswith(".log")


class TestGetLogLevel:
    """Test log level string to constant conversion."""

    def test_converts_debug_level(self):
        """Should convert DEBUG string to logging.DEBUG."""
        logging_config = load_logging_config()
        assert logging_config._get_log_level("DEBUG") == logging.DEBUG

    def test_converts_info_level(self):
        """Should convert INFO string to logging.INFO."""
        logging_config = load_logging_config()
        assert logging_config._get_log_level("INFO") == logging.INFO

    def test_converts_warning_level(self):
        """Should convert WARNING string to logging.WARNING."""
        logging_config = load_logging_config()
        assert logging_config._get_log_level("WARNING") == logging.WARNING

    def test_converts_error_level(self):
        """Should convert ERROR string to logging.ERROR."""
        logging_config = load_logging_config()
        assert logging_config._get_log_level("ERROR") == logging.ERROR

    def test_converts_critical_level(self):
        """Should convert CRITICAL string to logging.CRITICAL."""
        logging_config = load_logging_config()
        assert logging_config._get_log_level("CRITICAL") == logging.CRITICAL

    def test_case_insensitive_conversion(self):
        """Should handle case-insensitive level strings."""
        logging_config = load_logging_config()
        assert logging_config._get_log_level("debug") == logging.DEBUG
        assert logging_config._get_log_level("Debug") == logging.DEBUG
        assert logging_config._get_log_level("DEBUG") == logging.DEBUG

    def test_defaults_to_warning_for_invalid_level(self):
        """Should default to WARNING for invalid level strings."""
        logging_config = load_logging_config()
        assert logging_config._get_log_level("INVALID") == logging.WARNING
        assert logging_config._get_log_level("") == logging.WARNING


class TestGetLogger:
    """Test the get_logger function."""

    def test_returns_logger_instance(self):
        """Should return a logging.Logger instance."""
        logging_config = load_logging_config()
        logger = logging_config.get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_normalizes_module_names(self):
        """Should normalize module names under add-on namespace."""
        logging_config = load_logging_config()

        # Test with leading dots (relative import style)
        logger = logging_config.get_logger(".edge_tts_gen")
        assert "edge_tts_generate" in logger.name

    def test_handles_main_module_name(self):
        """Should handle __main__ module name."""
        logging_config = load_logging_config()
        logger = logging_config.get_logger("__main__")
        assert "edge_tts_generate" in logger.name

    def test_handles_external_runner_name(self):
        """Should handle external_tts_runner module name."""
        logging_config = load_logging_config()
        logger = logging_config.get_logger("external_tts_runner")
        assert "edge_tts_generate" in logger.name

    def test_caches_logger_instances(self):
        """Should cache and return same logger for same name."""
        logging_config = load_logging_config()
        logger1 = logging_config.get_logger("test_module")
        logger2 = logging_config.get_logger("test_module")
        # Both should be the same logger object
        assert logger1 is logger2


class TestGetLogFilePath:
    """Test the get_log_file_path function."""

    def test_returns_absolute_path(self):
        """Should return an absolute path."""
        logging_config = load_logging_config()
        path = logging_config.get_log_file_path()
        assert os.path.isabs(path)

    def test_path_ends_with_log_extension(self):
        """Should return path ending with .log."""
        logging_config = load_logging_config()
        path = logging_config.get_log_file_path()
        assert path.endswith(".log")

    def test_path_in_addon_directory(self):
        """Should return path in the add-on directory."""
        logging_config = load_logging_config()
        path = logging_config.get_log_file_path()
        addon_dir = os.path.dirname(_MODULE_PATH)
        assert path.startswith(addon_dir)


class TestSetLogLevel:
    """Test the set_log_level function."""

    def test_updates_root_logger_level(self):
        """Should update the root logger level."""
        logging_config = load_logging_config()

        # Get the root logger
        root_logger = logging.getLogger("edge_tts_generate")

        # Set to DEBUG level
        logging_config.set_log_level("DEBUG")

        # Verify level was updated
        assert root_logger.level == logging.DEBUG


class TestLoggingState:
    """Test the _LoggingState class."""

    def test_state_class_exists(self):
        """Should have _LoggingState class for configuration state."""
        logging_config = load_logging_config()
        assert hasattr(logging_config, "_LoggingState")

    def test_state_has_handler_configured_attribute(self):
        """State should have handler_configured attribute."""
        logging_config = load_logging_config()
        state = logging_config._LoggingState()
        assert hasattr(state, "handler_configured")
        assert state.handler_configured is False


class TestConfigureLogging:
    """Test the configure_logging function."""

    def test_accepts_custom_log_level(self):
        """Should accept custom log level parameter."""
        logging_config = load_logging_config()
        # This should not raise an error
        logging_config.configure_logging(log_level="DEBUG")

    def test_accepts_custom_max_size(self):
        """Should accept custom max log size parameter."""
        logging_config = load_logging_config()
        # This should not raise an error
        logging_config.configure_logging(max_log_size_mb=10.0)

    def test_accepts_custom_backup_count(self):
        """Should accept custom backup count parameter."""
        logging_config = load_logging_config()
        # This should not raise an error
        logging_config.configure_logging(backup_count=5)
