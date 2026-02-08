"""
Logging Configuration

Centralized logging setup for the trading bot.
Provides both console and file logging with rotation.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = 'INFO',
    log_file: str = 'bot.log',
    log_dir: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_level: Optional[str] = None,
    file_level: Optional[str] = None
) -> logging.Logger:
    """
    Set up centralized logging configuration.
    
    Args:
        log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of log file
        log_dir: Directory for log files (default: logs/ in current directory)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        console_level: Console log level (default: INFO)
        file_level: File log level (default: DEBUG)
        
    Returns:
        Configured root logger
        
    Log Level Guidelines:
        - DEBUG: API calls, cache hits, detailed operations
        - INFO: Opportunities found, trades executed, important events
        - WARNING: Discrepancies, rate limits approaching, non-critical issues
        - ERROR: API failures, calculation errors, failed operations
        - CRITICAL: System failures, unrecoverable errors
    """
    # Create log directory if it doesn't exist
    if log_dir is None:
        log_dir = 'logs'
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Set up log levels
    console_level = console_level or 'INFO'
    file_level = file_level or 'DEBUG'
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler (INFO level by default)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Rotating file handler (DEBUG level by default)
    log_file_path = log_path / log_file
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Log initialization
    root_logger.info(f"Logging initialized - Console: {console_level}, File: {file_level}")
    root_logger.debug(f"Log file: {log_file_path.absolute()}")
    
    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(logger: logging.Logger, level: str):
    """
    Change log level for a specific logger.
    
    Args:
        logger: Logger instance
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.setLevel(getattr(logging, level.upper()))


def add_handler(
    logger: logging.Logger,
    handler: logging.Handler,
    level: str = 'DEBUG',
    formatter: Optional[logging.Formatter] = None
):
    """
    Add a custom handler to a logger.
    
    Args:
        logger: Logger instance
        handler: Handler to add
        level: Log level for the handler
        formatter: Optional custom formatter
    """
    handler.setLevel(getattr(logging, level.upper()))
    
    if formatter:
        handler.setFormatter(formatter)
    
    logger.addHandler(handler)


class LoggerContext:
    """
    Context manager for temporary log level changes.
    
    Example:
        with LoggerContext('my.module', 'DEBUG'):
            # Code that needs debug logging
            pass
    """
    
    def __init__(self, logger_name: str, level: str):
        """
        Initialize logger context.
        
        Args:
            logger_name: Name of logger to modify
            level: Temporary log level
        """
        self.logger = logging.getLogger(logger_name)
        self.original_level = self.logger.level
        self.new_level = getattr(logging, level.upper())
    
    def __enter__(self):
        """Enter context - set new log level."""
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore original log level."""
        self.logger.setLevel(self.original_level)


def silence_logger(logger_name: str):
    """
    Silence a specific logger (set to CRITICAL to suppress most messages).
    
    Args:
        logger_name: Name of logger to silence
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)


def configure_third_party_loggers():
    """
    Configure log levels for common third-party libraries.
    Reduces noise from verbose libraries.
    """
    # Suppress verbose third-party loggers
    silence_logger('urllib3')
    silence_logger('requests')
    silence_logger('werkzeug')
    
    # Set reasonable levels for other common libraries
    logging.getLogger('flask').setLevel(logging.WARNING)
    logging.getLogger('flask_cors').setLevel(logging.WARNING)
