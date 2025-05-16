"""Error handler interface for the application layer."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from domain.value_objects.error_types import ErrorType

class IErrorHandler(ABC):
    """Interface for error handling operations."""
    
    @abstractmethod
    def handle(self, error_type: ErrorType, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an error with appropriate strategy.
        
        Args:
            error_type: Type of error that occurred
            context: Context data related to the error
            
        Returns:
            Updated context with error handling results
        """
        pass
    
    @abstractmethod
    def should_retry(self, error_type: ErrorType, context: Dict[str, Any]) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            error_type: Type of error that occurred
            context: Context data including retry count
            
        Returns:
            Boolean indicating if retry should be attempted
        """
        pass
    
    @abstractmethod
    def log_error(self, error_type: ErrorType, message: str, details: Dict[str, Any] = None) -> None:
        """
        Log an error with appropriate severity.
        
        Args:
            error_type: Type of error that occurred
            message: Error message
            details: Additional error details
        """
        pass
    
    @abstractmethod
    def format_error_response(self, error_type: ErrorType, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format an error response for API consumers.
        
        Args:
            error_type: Type of error that occurred
            message: Error message
            details: Additional error details
            
        Returns:
            Formatted error response
        """
        pass 