"""
Application layer exceptions.

DEPRECATED: This module is deprecated. Use src.exceptions module instead.
"""
import warnings
from src.exceptions import (
    ApplicationServiceError, ServiceError, RequestValidationError, 
    TemplateNotFoundError, TemplateValidationError, ErrorType
)

# Issue a deprecation warning
warnings.warn(
    "The module 'application/exceptions.py' is deprecated. Use 'src.exceptions' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backwards compatibility
__all__ = [
    'ApplicationServiceError', 'ServiceError', 'RequestValidationError', 
    'TemplateNotFoundError', 'TemplateValidationError', 'ErrorType'
]

# Original code below for backwards compatibility
from typing import Dict, Any, Optional


class ApplicationError(Exception):
    """Base class for all application layer exceptions."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize application error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ServiceError(ApplicationError):
    """Base class for all application service errors."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize service error.
        
        Args:
            message: Error message
            service_name: Name of the service that raised the error
            details: Optional additional error details
        """
        self.service_name = service_name
        
        details = details or {}
        details.update({
            "service_name": service_name
        })
        
        super().__init__(message, details)


class ValidationError(ApplicationError):
    """Application validation error."""
    
    def __init__(
        self,
        message: str,
        validation_errors: Dict[str, str],
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            validation_errors: Dictionary mapping field names to error messages
            details: Optional additional error details
        """
        self.validation_errors = validation_errors
        
        details = details or {}
        details.update({
            "validation_errors": validation_errors
        })
        
        super().__init__(message, details)


class ResourceNotFoundError(ApplicationError):
    """Application resource not found error."""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize resource not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource that was not found
            resource_id: ID of resource that was not found
            details: Optional additional error details
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        details = details or {}
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        
        super().__init__(message, details)


class AuthorizationError(ApplicationError):
    """Application authorization error."""
    
    def __init__(
        self,
        message: str,
        user_id: str,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authorization error.
        
        Args:
            message: Error message
            user_id: ID of the user that was not authorized
            resource_type: Optional type of resource that access was denied to
            action: Optional action that was denied
            details: Optional additional error details
        """
        self.user_id = user_id
        self.resource_type = resource_type
        self.action = action
        
        details = details or {}
        details.update({
            "user_id": user_id
        })
        
        if resource_type:
            details["resource_type"] = resource_type
        
        if action:
            details["action"] = action
        
        super().__init__(message, details)


class DuplicateResourceError(ApplicationError):
    """Application duplicate resource error."""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize duplicate resource error.
        
        Args:
            message: Error message
            resource_type: Type of resource that was duplicated
            resource_id: ID of resource that was duplicated
            details: Optional additional error details
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        details = details or {}
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        
        super().__init__(message, details)


class ConfigurationError(ApplicationError):
    """Application configuration error."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Optional key of the configuration that caused the error
            details: Optional additional error details
        """
        self.config_key = config_key
        
        details = details or {}
        
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(message, details)


class BusinessRuleError(ApplicationError):
    """Application business rule violation error."""
    
    def __init__(
        self,
        message: str,
        rule_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize business rule error.
        
        Args:
            message: Error message
            rule_name: Name of the business rule that was violated
            details: Optional additional error details
        """
        self.rule_name = rule_name
        
        details = details or {}
        details.update({
            "rule_name": rule_name
        })
        
        super().__init__(message, details) 