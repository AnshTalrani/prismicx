"""Error type value object module."""
from enum import Enum, auto

class ErrorType(Enum):
    """Defines the different error types that can occur in the agent."""
    
    # Data validation errors
    VALIDATION_ERROR = auto()
    MISSING_REQUIRED_FIELD = auto()
    INVALID_FORMAT = auto()
    
    # Template errors
    TEMPLATE_NOT_FOUND = auto()
    INVALID_TEMPLATE = auto()
    
    # Processing errors
    PROCESSING_ERROR = auto()
    EXECUTION_TIMEOUT = auto()
    
    # Service communication errors
    SERVICE_UNAVAILABLE = auto()
    SERVICE_TIMEOUT = auto()
    COMMUNICATION_ERROR = auto()
    
    # Authorization errors
    UNAUTHORIZED = auto()
    FORBIDDEN = auto()
    
    # Other errors
    UNKNOWN_ERROR = auto()
    
    def is_retriable(self) -> bool:
        """
        Determine if an error type is retriable.
        
        Returns:
            Boolean indicating if retry is appropriate for this error type
        """
        retriable_errors = {
            self.SERVICE_UNAVAILABLE,
            self.SERVICE_TIMEOUT,
            self.COMMUNICATION_ERROR,
            self.EXECUTION_TIMEOUT
        }
        
        return self in retriable_errors 