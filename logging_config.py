"""
Logging configuration for the Edge TTS add-on.

This module provides a centralized logging system for bug reports and debugging.
Logs are written to a rotating file in the add-on directory and optionally to console.

Usage:
    from .logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Message")
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


# Default configuration values
DEFAULT_LOG_LEVEL = "WARNING"
DEFAULT_MAX_LOG_SIZE_MB = 5
DEFAULT_LOG_BACKUP_COUNT = 3
LOG_FILENAME = "edge_tts.log"

# Logger instances cache
_loggers: dict[str, logging.Logger] = {}


class _LoggingState:
    """Container for logging configuration state."""

    handler_configured: bool = False


_state = _LoggingState()


def _get_addon_log_path() -> str:
    """Get the path to the log file in the add-on directory."""
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(addon_dir, LOG_FILENAME)


def _get_log_level(level_str: str) -> int:
    """Convert log level string to logging constant."""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str.upper(), logging.WARNING)


def configure_logging(
    log_level: str = DEFAULT_LOG_LEVEL,
    max_log_size_mb: float = DEFAULT_MAX_LOG_SIZE_MB,
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
) -> None:
    """
    Configure the logging system for the add-on.

    If logging has already been configured, this function updates the log level
    for the root logger and all existing handlers, allowing user preferences
    to take effect even if logging was initialized before the config was loaded.

    Args:
        log_level: The minimum log level to record (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_log_size_mb: Maximum size of each log file in MB before rotation
        backup_count: Number of backup log files to keep
    """
    level = _get_log_level(log_level)
    root_logger = logging.getLogger("edge_tts_generate")

    # If already configured, just update the log level and return
    if _state.handler_configured or root_logger.handlers:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)
        _state.handler_configured = True
        return

    log_path = _get_addon_log_path()

    # Set the log level on the root logger
    root_logger.setLevel(level)

    # Create rotating file handler
    max_bytes = int(max_log_size_mb * 1024 * 1024)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    _state.handler_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: The name for the logger (typically __name__)

    Returns:
        A configured logger instance
    """
    # Ensure logging is configured
    if not _state.handler_configured:
        configure_logging()

    # Normalize the logger name to be under the add-on namespace
    if name.startswith("edge_tts_generate."):
        logger_name = name
    elif name in {"__main__", "external_tts_runner"}:
        # External runner module runs in isolated Python
        logger_name = f"edge_tts_generate.{name}"
    else:
        # Strip leading dots for relative imports within the package
        clean_name = name.lstrip(".")
        logger_name = f"edge_tts_generate.{clean_name}"

    if logger_name not in _loggers:
        _loggers[logger_name] = logging.getLogger(logger_name)

    return _loggers[logger_name]


def get_log_file_path() -> str:
    """
    Get the path to the current log file.

    Returns:
        The absolute path to the log file
    """
    return _get_addon_log_path()


def set_log_level(level: str) -> None:
    """
    Update the log level for all loggers.

    Args:
        level: The new log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = _get_log_level(level)
    root_logger = logging.getLogger("edge_tts_generate")
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers:
        handler.setLevel(log_level)
