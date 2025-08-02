"""
Service exception classes.
"""

class ServiceError(Exception):
    """Base exception for service errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ValidationError(ServiceError):
    """Exception for validation errors."""
    pass

class ResourceNotFoundError(ServiceError):
    """Exception for resource not found errors."""
    pass

class AuthorizationError(ServiceError):
    """Exception for authorization errors."""
    pass

class DependencyError(ServiceError):
    """Exception for service dependency errors."""
    pass

class ConfigurationError(ServiceError):
    """Exception for configuration errors."""
    pass

class ExternalServiceError(ServiceError):
    """Exception for external service errors."""
    
    def __init__(self, message: str, service_name: str = None):
        self.service_name = service_name
        message_with_service = f"{message} (Service: {service_name})" if service_name else message
        super().__init__(message_with_service)

class RateLimitExceededError(ServiceError):
    """Exception for rate limit exceeded errors."""
    
    def __init__(self, message: str, retry_after: int = None):
        self.retry_after = retry_after
        message_with_retry = f"{message} (Retry after: {retry_after}s)" if retry_after else message
        super().__init__(message_with_retry)

class TimeoutError(ServiceError):
    """Exception for timeout errors."""
    pass 