"""
File-based logging for VoiceFlow.
Logs are stored in ~/.VoiceFlow/logs/ with automatic rotation.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Global logger instance
_logger = None


def get_log_dir() -> Path:
    """Get the log directory path."""
    log_dir = Path.home() / ".VoiceFlow" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger() -> logging.Logger:
    """Setup and return the application logger."""
    global _logger

    if _logger is not None:
        return _logger

    _logger = logging.getLogger("VoiceFlow")
    _logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    _logger.handlers.clear()

    # File handler with rotation (5MB max, keep 3 backups)
    log_dir = get_log_dir()
    log_file = log_dir / "voiceflow.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Also log to stderr (visible in dev mode)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)

    # Format: timestamp - level - message
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)

    # Log startup
    _logger.info("=" * 60)
    _logger.info(f"VoiceFlow started at {datetime.now().isoformat()}")
    _logger.info(f"Log file: {log_file}")
    _logger.info("=" * 60)

    return _logger


def get_logger() -> logging.Logger:
    """Get the application logger (setup if needed)."""
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger


# Convenience functions
def debug(msg: str, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """Log an exception with traceback."""
    get_logger().exception(msg, *args, **kwargs)
