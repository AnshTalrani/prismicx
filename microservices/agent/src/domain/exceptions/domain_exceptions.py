"""Domain-specific exceptions module."""
from domain.value_objects.error_types import ErrorType

class AgentException(Exception):
    """Base exception class for all agent domain exceptions."""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR):
        """
        Initialize agent exception.
        
        Args:
            message: Error message
            error_type: Type of error
        """
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class TemplateNotFoundException(AgentException):
    """Exception raised when a template is not found."""
    
    def __init__(self, template_id: str):
        """
        Initialize template not found exception.
        
        Args:
            template_id: ID of template that wasn't found
        """
        super().__init__(
            f"Template with ID '{template_id}' not found", 
            ErrorType.TEMPLATE_NOT_FOUND
        )
        self.template_id = template_id


class InvalidTemplateException(AgentException):
    """Exception raised when a template is invalid."""
    
    def __init__(self, template_id: str, reason: str):
        """
        Initialize invalid template exception.
        
        Args:
            template_id: ID of invalid template
            reason: Reason why template is invalid
        """
        super().__init__(
            f"Template with ID '{template_id}' is invalid: {reason}", 
            ErrorType.INVALID_TEMPLATE
        )
        self.template_id = template_id
        self.reason = reason


class MissingRequiredFieldException(AgentException):
    """Exception raised when a required field is missing."""
    
    def __init__(self, field_name: str):
        """
        Initialize missing required field exception.
        
        Args:
            field_name: Name of missing field
        """
        super().__init__(
            f"Required field '{field_name}' is missing", 
            ErrorType.MISSING_REQUIRED_FIELD
        )
        self.field_name = field_name


class ServiceUnavailableException(AgentException):
    """Exception raised when a required service is unavailable."""
    
    def __init__(self, service_name: str):
        """
        Initialize service unavailable exception.
        
        Args:
            service_name: Name of unavailable service
        """
        super().__init__(
            f"Service '{service_name}' is unavailable", 
            ErrorType.SERVICE_UNAVAILABLE
        )
        self.service_name = service_name


class UnauthorizedException(AgentException):
    """Exception raised when a request is unauthorized."""
    
    def __init__(self):
        """Initialize unauthorized exception."""
        super().__init__(
            "Request is unauthorized", 
            ErrorType.UNAUTHORIZED
        ) 