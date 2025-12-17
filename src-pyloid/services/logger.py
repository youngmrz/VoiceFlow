"""
Domain-based logging for VoiceFlow.

Hybrid format: [timestamp] [LEVEL] [domain] message | {structured data}
File: ~/.VoiceFlow/VoiceFlow.log
Rotation: 100MB max, 1 backup (.log.1)
Domains: model, audio, hotkey, settings, database, clipboard, window

Usage:
    from services.logger import get_logger
    log = get_logger("model")
    log.info("Loading whisper-small")
    log.error("Download failed", error="Network timeout", url="https://...")
"""
import logging
import json
import sys
from pathlib import Path
from typing import Optional, Any
from logging.handlers import RotatingFileHandler


# Configuration constants
LOG_MAX_BYTES = 100 * 1024 * 1024  # 100MB
LOG_BACKUP_COUNT = 1

# Valid domains
VALID_DOMAINS = {"model", "audio", "hotkey", "settings", "database", "clipboard", "window"}

# Global state
_initialized = False
_log_file: Optional[Path] = None
_domain_loggers: dict[str, "DomainLogger"] = {}
_file_handler: Optional[RotatingFileHandler] = None
_console_handler: Optional[logging.StreamHandler] = None


def get_default_log_path() -> Path:
    """Get the default log file path."""
    return Path.home() / ".VoiceFlow" / "VoiceFlow.log"


class HybridFormatter(logging.Formatter):
    """
    Formatter that produces hybrid format:
    [timestamp] [LEVEL] [domain] message | {structured data}

    The structured data is stored in the 'structured_data' attribute of the LogRecord.
    """

    def __init__(self):
        super().__init__()
        self.datefmt = '%Y-%m-%d %H:%M:%S'

    def format(self, record: logging.LogRecord) -> str:
        # Format timestamp
        timestamp = self.formatTime(record, self.datefmt)

        # Map level names (WARNING -> WARN for consistency with design)
        level = record.levelname
        if level == "WARNING":
            level = "WARN"

        # Get domain from logger name (format: VoiceFlow.domain)
        parts = record.name.split('.')
        domain = parts[1] if len(parts) > 1 else "app"

        # Build base message
        base = f"[{timestamp}] [{level}] [{domain}] {record.getMessage()}"

        # Add structured data if present
        structured_data = getattr(record, 'structured_data', None)
        if structured_data:
            json_str = json.dumps(structured_data, ensure_ascii=False)
            return f"{base} | {json_str}"

        return base


class DomainLogger:
    """
    A logger for a specific domain that supports structured data via kwargs.

    Usage:
        log = get_logger("model")
        log.info("Loading model", model_name="small", load_time_ms=1234)
    """

    def __init__(self, domain: str, logger: logging.Logger):
        self._domain = domain
        self._logger = logger

    def _log(self, level: int, message: str, **kwargs):
        """Log a message with optional structured data."""
        # Create a LogRecord with structured data
        if kwargs:
            # Store kwargs as structured data
            extra = {'structured_data': kwargs}
        else:
            extra = {'structured_data': None}

        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log an error message."""
        self._log(logging.ERROR, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log an exception with traceback."""
        self._log(logging.ERROR, message, **kwargs)
        # The traceback will be handled by the exception info in the log record


def setup_logging(
    log_file: Optional[Path] = None,
    max_bytes: int = LOG_MAX_BYTES,
    backup_count: int = LOG_BACKUP_COUNT
) -> None:
    """
    Initialize the logging system.

    Args:
        log_file: Path to log file. Defaults to ~/.VoiceFlow/VoiceFlow.log
        max_bytes: Maximum file size before rotation. Defaults to 100MB.
        backup_count: Number of backup files to keep. Defaults to 1.
    """
    global _initialized, _log_file, _file_handler, _console_handler

    if log_file is None:
        log_file = get_default_log_path()

    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    _log_file = log_file

    # Create formatter
    formatter = HybridFormatter()

    # Create file handler with rotation
    _file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(formatter)

    # Create console handler for development
    _console_handler = logging.StreamHandler(sys.stderr)
    _console_handler.setLevel(logging.DEBUG)
    _console_handler.setFormatter(formatter)

    # Set up root logger for VoiceFlow
    root_logger = logging.getLogger("VoiceFlow")
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(_file_handler)
    root_logger.addHandler(_console_handler)

    _initialized = True


def reset_logging() -> None:
    """
    Reset the logging system. Used for test isolation.
    """
    global _initialized, _log_file, _domain_loggers, _file_handler, _console_handler

    # Close handlers
    if _file_handler:
        _file_handler.close()
    if _console_handler:
        _console_handler.close()

    # Clear root logger
    root_logger = logging.getLogger("VoiceFlow")
    root_logger.handlers.clear()

    # Clear all domain loggers
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if name.startswith("VoiceFlow."):
            logger = logging.getLogger(name)
            logger.handlers.clear()

    # Reset state
    _initialized = False
    _log_file = None
    _domain_loggers.clear()
    _file_handler = None
    _console_handler = None


def get_logger(domain: str) -> DomainLogger:
    """
    Get a logger for a specific domain.

    Args:
        domain: One of the valid domains (model, audio, hotkey, settings, database, clipboard, window)

    Returns:
        A DomainLogger instance for the specified domain.
    """
    global _domain_loggers

    # Return cached logger if exists
    if domain in _domain_loggers:
        return _domain_loggers[domain]

    # Auto-initialize if not done
    if not _initialized:
        setup_logging()

    # Create underlying Python logger
    logger_name = f"VoiceFlow.{domain}"
    py_logger = logging.getLogger(logger_name)
    py_logger.setLevel(logging.DEBUG)

    # Create domain logger wrapper
    domain_logger = DomainLogger(domain, py_logger)
    _domain_loggers[domain] = domain_logger

    return domain_logger


# Legacy API compatibility - these are used by existing code
def debug(msg: str, *args, **kwargs):
    """Legacy debug function for backward compatibility."""
    get_logger("app").debug(msg)


def info(msg: str, *args, **kwargs):
    """Legacy info function for backward compatibility."""
    get_logger("app").info(msg)


def warning(msg: str, *args, **kwargs):
    """Legacy warning function for backward compatibility."""
    get_logger("app").warning(msg)


def error(msg: str, *args, **kwargs):
    """Legacy error function for backward compatibility."""
    get_logger("app").error(msg)


def exception(msg: str, *args, **kwargs):
    """Legacy exception function for backward compatibility."""
    get_logger("app").exception(msg)


# Legacy setup function
def setup_logger() -> logging.Logger:
    """Legacy setup function for backward compatibility."""
    setup_logging()
    return logging.getLogger("VoiceFlow")


def get_log_dir() -> Path:
    """Legacy function to get log directory."""
    log_dir = Path.home() / ".VoiceFlow"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
