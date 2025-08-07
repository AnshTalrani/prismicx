"""
Logging configuration for the outreach system.

This module provides structured logging setup with JSON formatting,
log levels, and proper error handling.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from .settings import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs."""
    
    SENSITIVE_FIELDS = {
        "password", "token", "api_key", "secret", "authorization",
        "x-api-key", "bearer", "auth"
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and mask sensitive data in log messages."""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            # Simple masking for sensitive data
            for field in self.SENSITIVE_FIELDS:
                if field.lower() in record.msg.lower():
                    record.msg = record.msg.replace(field, f"{field}_MASKED")
        
        return True


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_json: bool = True
) -> None:
    """Set up logging configuration."""
    
    # Use settings if not provided
    log_level = log_level or settings.log_level
    log_format = log_format or settings.log_format
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on format preference
    if enable_json and log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    
    # Add sensitive data filter
    console_handler.addFilter(SensitiveDataFilter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin to add logging capabilities to classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")


def log_function_call(func):
    """Decorator to log function calls with parameters."""
    def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        
        # Log function call
        logger.debug(
            f"Function call: {func.__name__}",
            extra={
                "extra_fields": {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
            }
        )
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(
                f"Function {func.__name__} failed: {str(e)}",
                exc_info=True
            )
            raise
    
    return wrapper


def log_performance(func):
    """Decorator to log function performance."""
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"Function {func.__name__} executed in {execution_time:.4f}s",
                extra={
                    "extra_fields": {
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                }
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.4f}s: {str(e)}",
                extra={
                    "extra_fields": {
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "status": "error",
                        "error": str(e)
                    }
                },
                exc_info=True
            )
            raise
    
    return wrapper


# Initialize logging on module import
setup_logging() 