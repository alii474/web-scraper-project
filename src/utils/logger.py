"""
Advanced Logging System for Web Scraper

Provides comprehensive logging with multiple handlers, rotation, and structured output.
Follows Python logging best practices with clean architecture.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

from .config import CONFIG


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data)


class ScraperLogger:
    """
    Advanced logging system for the web scraper.
    Provides multiple handlers, rotation, and structured output.
    """
    
    def __init__(self, name: str = 'scraper', level: str = None):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level or CONFIG.LOG_LEVEL))
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_json_handler()
        self._setup_error_handler()
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _setup_console_handler(self):
        """Setup console handler with colored output."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Use colored formatter for console
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt=CONFIG.LOG_DATE_FORMAT
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Setup rotating file handler for general logs."""
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        log_file = logs_dir / 'scraper.log'
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=CONFIG.LOG_MAX_SIZE,
            backupCount=CONFIG.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            fmt=CONFIG.LOG_FORMAT,
            datefmt=CONFIG.LOG_DATE_FORMAT
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
    
    def _setup_json_handler(self):
        """Setup JSON file handler for structured logging."""
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        json_file = logs_dir / 'scraper.json'
        json_handler = logging.handlers.RotatingFileHandler(
            filename=json_file,
            maxBytes=CONFIG.LOG_MAX_SIZE,
            backupCount=CONFIG.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        
        self.logger.addHandler(json_handler)
    
    def _setup_error_handler(self):
        """Setup separate handler for errors only."""
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        error_file = logs_dir / 'errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_file,
            maxBytes=CONFIG.LOG_MAX_SIZE,
            backupCount=CONFIG.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        error_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
                'File: %(pathname)s:%(lineno)d\n'
                'Function: %(funcName)s\n',
            datefmt=CONFIG.LOG_DATE_FORMAT
        )
        error_handler.setFormatter(error_formatter)
        
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_extra(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_extra(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_extra(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_extra(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log_with_extra(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self._log_with_extra(logging.ERROR, message, exc_info=True, **kwargs)
    
    def _log_with_extra(self, level: int, message: str, **kwargs):
        """Log message with extra fields."""
        extra = {k: v for k, v in kwargs.items() if k != 'exc_info'}
        self.logger.log(level, message, extra=extra, exc_info=kwargs.get('exc_info', False))
    
    def log_scraping_start(self, url: str, pages: int, **kwargs):
        """Log scraping session start."""
        self.info(
            f"Starting scraping session",
            url=url,
            pages=pages,
            session_id=kwargs.get('session_id'),
            **kwargs
        )
    
    def log_scraping_end(self, total_items: int, duration: float, **kwargs):
        """Log scraping session end."""
        self.info(
            f"Scraping session completed",
            total_items=total_items,
            duration_seconds=duration,
            items_per_second=total_items / duration if duration > 0 else 0,
            **kwargs
        )
    
    def log_request(self, url: str, status_code: int, response_time: float, **kwargs):
        """Log HTTP request details."""
        level = logging.INFO if 200 <= status_code < 300 else logging.WARNING
        self._log_with_extra(
            level,
            f"HTTP request: {status_code} for {url}",
            url=url,
            status_code=status_code,
            response_time=response_time,
            **kwargs
        )
    
    def log_data_saved(self, format_type: str, file_path: str, record_count: int, **kwargs):
        """Log data saving operation."""
        self.info(
            f"Data saved to {format_type.upper()}",
            format=format_type,
            file_path=str(file_path),
            record_count=record_count,
            **kwargs
        )
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any], **kwargs):
        """Log error with context information."""
        self.exception(
            f"Error occurred: {str(error)}",
            error_type=type(error).__name__,
            context=context,
            **kwargs
        )


# Global logger instance
logger = ScraperLogger()


def get_logger(name: str = None) -> ScraperLogger:
    """
    Get logger instance.
    
    Args:
        name: Logger name (optional)
    
    Returns:
        ScraperLogger instance
    """
    if name:
        return ScraperLogger(name)
    return logger


def setup_logging(level: str = None, log_file: str = None):
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        log_file: Custom log file path
    """
    global logger
    
    if level:
        logger.logger.setLevel(getattr(logging, level))
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update file handler
        for handler in logger.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler) and handler.baseFilename.endswith('scraper.log'):
                handler.baseFilename = str(log_path)
                break


class PerformanceLogger:
    """Logger for performance monitoring and metrics."""
    
    def __init__(self):
        self.logger = get_logger('performance')
        self.metrics = {}
    
    def log_timing(self, operation: str, duration: float, **kwargs):
        """Log operation timing."""
        self.logger.info(
            f"Operation '{operation}' completed in {duration:.2f}s",
            operation=operation,
            duration=duration,
            **kwargs
        )
    
    def log_memory_usage(self, operation: str, memory_mb: float, **kwargs):
        """Log memory usage."""
        self.logger.info(
            f"Memory usage for '{operation}': {memory_mb:.2f} MB",
            operation=operation,
            memory_mb=memory_mb,
            **kwargs
        )
    
    def log_rate_limit(self, url: str, wait_time: float, **kwargs):
        """Log rate limiting."""
        self.logger.info(
            f"Rate limiting: waiting {wait_time:.2f}s for {url}",
            url=url,
            wait_time=wait_time,
            **kwargs
        )


# Performance logger instance
performance_logger = PerformanceLogger()
