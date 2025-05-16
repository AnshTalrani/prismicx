"""
Centralized exceptions module.

This module re-exports all exceptions from the various layers of the application,
making it easier to import and use them.
"""
from enum import Enum, auto
from typing import Optional, Dict, Any

# Base exception classes
class ApplicationError(Exception):
    """Base class for all application exceptions."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize ApplicationError.
        
        Args:
            message: Error message
            details: Optional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

class DomainError(ApplicationError):
    """Base class for domain layer exceptions."""
    pass

class ApplicationServiceError(ApplicationError):
    """Base class for application service layer exceptions."""
    pass

class InfrastructureError(ApplicationError):
    """Base class for infrastructure layer exceptions."""
    pass

class InterfaceError(ApplicationError):
    """Base class for interface layer exceptions."""
    pass

# Error types enum
class ErrorType(Enum):
    """Enumeration of error types across the application."""
    # General errors
    UNKNOWN_ERROR = auto()
    VALIDATION_ERROR = auto()
    NOT_FOUND_ERROR = auto()
    UNAUTHORIZED_ERROR = auto()
    FORBIDDEN_ERROR = auto()
    CONFLICT_ERROR = auto()
    
    # Domain errors
    DOMAIN_VALIDATION_ERROR = auto()
    DOMAIN_LOGIC_ERROR = auto()
    
    # Service errors
    SERVICE_ERROR = auto()
    SERVICE_UNAVAILABLE_ERROR = auto()
    
    # Data errors
    REPOSITORY_ERROR = auto()
    DATA_INTEGRITY_ERROR = auto()
    
    # Template errors
    TEMPLATE_NOT_FOUND_ERROR = auto()
    TEMPLATE_VALIDATION_ERROR = auto()
    
    # Request errors
    REQUEST_VALIDATION_ERROR = auto()
    REQUEST_PROCESSING_ERROR = auto()
    
    # Infrastructure errors
    EXTERNAL_SERVICE_ERROR = auto()
    COMMUNICATION_ERROR = auto()
    DATABASE_ERROR = auto()
    CACHE_ERROR = auto()
    
    # Configuration errors
    CONFIGURATION_ERROR = auto()
    FEATURE_FLAG_ERROR = auto()

# Domain layer exceptions
class ValidationError(DomainError):
    """Exception raised when domain validation fails."""
    error_type = ErrorType.DOMAIN_VALIDATION_ERROR

class ResourceNotFoundError(DomainError):
    """Exception raised when a requested resource is not found."""
    error_type = ErrorType.NOT_FOUND_ERROR

class BusinessRuleViolationError(DomainError):
    """Exception raised when a business rule is violated."""
    error_type = ErrorType.DOMAIN_LOGIC_ERROR

# Application layer exceptions
class ServiceError(ApplicationServiceError):
    """Exception raised when a service operation fails."""
    error_type = ErrorType.SERVICE_ERROR

class RequestValidationError(ApplicationServiceError):
    """Exception raised when request validation fails."""
    error_type = ErrorType.REQUEST_VALIDATION_ERROR

class TemplateNotFoundError(ApplicationServiceError):
    """Exception raised when a template is not found."""
    error_type = ErrorType.TEMPLATE_NOT_FOUND_ERROR

class TemplateValidationError(ApplicationServiceError):
    """Exception raised when template validation fails."""
    error_type = ErrorType.TEMPLATE_VALIDATION_ERROR

# Infrastructure layer exceptions
class RepositoryError(InfrastructureError):
    """Exception raised when a repository operation fails."""
    error_type = ErrorType.REPOSITORY_ERROR

class ExternalServiceError(InfrastructureError):
    """Exception raised when an external service call fails."""
    error_type = ErrorType.EXTERNAL_SERVICE_ERROR

class DatabaseError(InfrastructureError):
    """Exception raised when a database operation fails."""
    error_type = ErrorType.DATABASE_ERROR

class CommunicationError(InfrastructureError):
    """Exception raised when communication with external systems fails."""
    error_type = ErrorType.COMMUNICATION_ERROR

class ConfigurationError(InfrastructureError):
    """Exception raised when a configuration error occurs."""
    error_type = ErrorType.CONFIGURATION_ERROR

class FeatureFlagError(InfrastructureError):
    """Exception raised when a feature flag error occurs."""
    error_type = ErrorType.FEATURE_FLAG_ERROR

# Interface layer exceptions
class ApiError(InterfaceError):
    """Exception raised for API-related errors."""
    error_type = ErrorType.EXTERNAL_SERVICE_ERROR 