"""
Logging configuration module.

This module provides structured logging configuration that follows the 
recommendations in the microservice_readme.md document.
"""

import logging
import os
import sys
import json
from datetime import datetime
import structlog
from typing import Dict, Any
from ..multitenant.context.tenant_context import TenantContext

# Get log level from environment or use default
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging():
    """
    Configure structured logging.
    
    Sets up structlog with proper formatting for console and file output.
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, LOG_LEVEL),
    )

    # Configure structlog processors
    processors = [
        # Add log level name as a key to the event dict
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add caller information 
        structlog.processors.StackInfoRenderer(),
        # Format any exceptions
        structlog.processors.format_exc_info,
        # Add tenant ID from context if available
        _add_tenant_context,
        # Format the final message
        structlog.processors.JSONRenderer()
    ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _add_tenant_context(logger, method_name, event_dict):
    """
    Add tenant context to log event.
    
    This processor adds the current tenant ID to the log event if available.
    """
    tenant_id = TenantContext.get_current_tenant()
    if tenant_id:
        event_dict["tenant_id"] = tenant_id
    
    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger.
    
    Args:
        name: Logger name, typically the module name
        
    Returns:
        A structured logger instance
    """
    return structlog.get_logger(name)


class LoggingMiddleware:
    """Middleware for request logging with tenant context."""
    
    def __init__(self, app):
        """Initialize middleware with app."""
        self.app = app
        self.logger = get_logger("request")
    
    async def __call__(self, scope, receive, send):
        """Process a request and log information about it."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        start_time = datetime.now()
        
        # Create a wrapper for send that logs the response status
        async def logging_send(message):
            if message["type"] == "http.response.start":
                # Calculate request duration
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                # Get request info
                method = scope.get("method", "UNKNOWN")
                path = scope.get("path", "UNKNOWN")
                status = message.get("status", 0)
                
                # Log the request
                self.logger.info(
                    "HTTP request", 
                    method=method,
                    path=path,
                    status=status,
                    duration_ms=round(duration_ms, 2)
                )
                
            await send(message)
        
        await self.app(scope, receive, logging_send) 