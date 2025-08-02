"""
Exceptions module for the Expert Base microservice.

This module defines custom exceptions used across the application.
"""

from typing import Any, Dict, Optional


class ExpertBaseException(Exception):
    """Base exception for all Expert Base exceptions."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ExpertNotFoundException(ExpertBaseException):
    """Exception raised when an expert is not found."""
    
    def __init__(self, expert_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Expert '{expert_id}' not found"
        super().__init__(message, status_code=404, details=details)


class IntentNotSupportedException(ExpertBaseException):
    """Exception raised when an intent is not supported by an expert."""
    
    def __init__(self, expert_id: str, intent: str, details: Optional[Dict[str, Any]] = None):
        message = f"Intent '{intent}' not supported by expert '{expert_id}'"
        super().__init__(message, status_code=400, details=details)


class ProcessingException(ExpertBaseException):
    """Exception raised when processing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ConfigurationException(ExpertBaseException):
    """Exception raised when there's an issue with configuration."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ValidationException(ExpertBaseException):
    """Exception raised when there's a validation error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class AuthenticationException(ExpertBaseException):
    """Exception raised when there's an authentication error."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class UnauthorizedException(ExpertBaseException):
    """Exception raised when a request is unauthorized."""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class VectorDBException(ExpertBaseException):
    """Exception raised when there's an issue with the vector database."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ModelProviderException(ExpertBaseException):
    """Exception raised when there's an issue with the model provider."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details) 