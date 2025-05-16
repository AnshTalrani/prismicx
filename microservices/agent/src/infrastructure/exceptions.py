"""
Infrastructure layer exceptions.

DEPRECATED: This module is deprecated. Use src.exceptions module instead.
"""
import warnings
from src.exceptions import (
    InfrastructureError, RepositoryError, ExternalServiceError, 
    DatabaseError, CommunicationError, ConfigurationError, FeatureFlagError, ErrorType
)

# Issue a deprecation warning
warnings.warn(
    "The module 'infrastructure/exceptions.py' is deprecated. Use 'src.exceptions' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backwards compatibility
__all__ = [
    'InfrastructureError', 'RepositoryError', 'ExternalServiceError', 
    'DatabaseError', 'CommunicationError', 'ConfigurationError', 'FeatureFlagError', 'ErrorType'
]

# Original code below for backwards compatibility
from typing import Dict, Any, Optional


class InfrastructureError(Exception):
    """Base class for all infrastructure layer exceptions."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize infrastructure error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ServiceError(InfrastructureError):
    """Base class for all service errors."""
    
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
        super().__init__(message, details)


class ConnectionError(ServiceError):
    """Error connecting to a service."""
    pass


class TimeoutError(ServiceError):
    """Service request timed out."""
    pass


class AuthenticationError(ServiceError):
    """Service authentication error."""
    pass


class PermissionError(ServiceError):
    """Service permission error."""
    pass


class ResourceNotFoundError(ServiceError):
    """Service resource not found error."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize resource not found error.
        
        Args:
            message: Error message
            service_name: Name of the service that raised the error
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
        
        super().__init__(message, service_name, details)


class ValidationError(ServiceError):
    """Service validation error."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        validation_errors: Dict[str, str],
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            service_name: Name of the service that raised the error
            validation_errors: Dictionary mapping field names to error messages
            details: Optional additional error details
        """
        self.validation_errors = validation_errors
        
        details = details or {}
        details.update({
            "validation_errors": validation_errors
        })
        
        super().__init__(message, service_name, details)


class RepositoryError(InfrastructureError):
    """Base class for all repository errors."""
    
    def __init__(
        self,
        message: str,
        repository_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize repository error.
        
        Args:
            message: Error message
            repository_name: Name of the repository that raised the error
            details: Optional additional error details
        """
        self.repository_name = repository_name
        
        details = details or {}
        details.update({
            "repository_name": repository_name
        })
        
        super().__init__(message, details)


class EntityNotFoundError(RepositoryError):
    """Repository entity not found error."""
    
    def __init__(
        self,
        message: str,
        repository_name: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize entity not found error.
        
        Args:
            message: Error message
            repository_name: Name of the repository that raised the error
            entity_type: Type of entity that was not found
            entity_id: ID of entity that was not found
            details: Optional additional error details
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        
        details = details or {}
        details.update({
            "entity_type": entity_type,
            "entity_id": entity_id
        })
        
        super().__init__(message, repository_name, details)


class DuplicateEntityError(RepositoryError):
    """Repository duplicate entity error."""
    
    def __init__(
        self,
        message: str,
        repository_name: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize duplicate entity error.
        
        Args:
            message: Error message
            repository_name: Name of the repository that raised the error
            entity_type: Type of entity that was duplicated
            entity_id: ID of entity that was duplicated
            details: Optional additional error details
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        
        details = details or {}
        details.update({
            "entity_type": entity_type,
            "entity_id": entity_id
        })
        
        super().__init__(message, repository_name, details)


class ConcurrencyError(RepositoryError):
    """Repository concurrency error."""
    pass


class PersistenceError(RepositoryError):
    """Repository persistence error."""
    pass 