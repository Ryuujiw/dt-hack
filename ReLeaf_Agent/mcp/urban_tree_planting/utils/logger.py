"""
Logging configuration for urban tree planting analysis

Provides consistent logging across all modules.
"""

import logging
import sys
from ..config.settings import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL


# Create logger instance
logger = logging.getLogger('urban_tree_planting')


def setup_logger(verbose=False, log_file=None):
    """
    Setup logging configuration

    Args:
        verbose: If True, set log level to DEBUG, else use LOG_LEVEL from settings
        log_file: Optional file path to write logs to (in addition to console)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Clear any existing handlers
    logger.handlers.clear()

    # Set log level
    if verbose:
        level = logging.DEBUG
    else:
        level = getattr(logging, LOG_LEVEL, logging.INFO)

    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    logger.info(f"Logger initialized (level={logging.getLevelName(level)})")

    return logger


# Default setup (can be overridden by calling setup_logger)
setup_logger()
