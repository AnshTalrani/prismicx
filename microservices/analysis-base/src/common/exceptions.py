"""
Exceptions Module for Analysis Base

This module defines custom exceptions used throughout the analysis microservice.
"""

from typing import Optional, Any


class ProcessingError(Exception):
    """
    Error occurring during processing.
    
    Attributes:
        message: Error message
        component: Component where error occurred
        retry_recommended: Whether a retry is recommended
        original_error: Original exception that caused this error
    """
    
    def __init__(
        self,
        message: str,
        component: str = "unknown",
        retry_recommended: bool = True,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.component = component
        self.retry_recommended = retry_recommended
        self.original_error = original_error
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"{self.message} (component: {self.component}, retry: {self.retry_recommended})"
    
    def to_dict(self) -> dict:
        """Convert the error to a dictionary representation."""
        return {
            "message": self.message,
            "component": self.component,
            "retry_recommended": self.retry_recommended,
            "original_error": str(self.original_error) if self.original_error else None
        }


class ConfigurationError(Exception):
    """
    Error occurring during configuration loading or validation.
    
    Attributes:
        message: Error message
        config_key: Configuration key that caused the error
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.message = message
        self.config_key = config_key
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.config_key:
            return f"Configuration error for '{self.config_key}': {self.message}"
        return f"Configuration error: {self.message}"
    
    def to_dict(self) -> dict:
        """Convert the error to a dictionary representation."""
        return {
            "message": self.message,
            "config_key": self.config_key
        }


class RepositoryError(Exception):
    """
    Exception raised when there is an error accessing the data repository.
    
    This exception wraps database and storage errors with more context.
    """
    
    def __init__(self, message: str, operation: str, original_error: Optional[Exception] = None):
        """
        Initialize a RepositoryError.
        
        Args:
            message: Human-readable error message
            operation: The repository operation that failed
            original_error: The original exception from the database driver
        """
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.original_error = original_error


class ValidationError(Exception):
    """
    Error occurring during data validation.
    
    Attributes:
        message: Error message
        field: Field that failed validation
        value: Invalid value
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.field:
            return f"Validation error for field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"
    
    def to_dict(self) -> dict:
        """Convert the error to a dictionary representation."""
        return {
            "message": self.message,
            "field": self.field,
            "value": str(self.value) if self.value is not None else None
        } 