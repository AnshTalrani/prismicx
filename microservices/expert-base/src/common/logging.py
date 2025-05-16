"""
Logging module for the Expert Base microservice.

This module configures logging for the application.
"""

import sys
import logging
from loguru import logger

from src.common.config import settings


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages toward Loguru.
    
    This allows using loguru as a handler for the standard logging module.
    """
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
            
        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
            
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    """
    Configure logging for the application.
    
    This function sets up loguru as the main logging handler and configures
    the log level based on the LOG_LEVEL environment variable.
    """
    # Remove default loguru handler
    logger.remove()
    
    # Add new handler with specified format
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Intercept standard logging messages
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    
    # Update logging level for other libraries
    for lib_logger in [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ]:
        logging.getLogger(lib_logger).handlers = [InterceptHandler()]
        
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")
    
    return logger 