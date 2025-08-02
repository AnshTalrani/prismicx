"""
Execution status value object.
"""
from enum import Enum
from typing import Optional

class ExecutionStatus(Enum):
    """
    Enum representing different execution statuses.
    """
    
    CREATED = "created"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['ExecutionStatus']:
        """
        Convert string to enum value.
        
        Args:
            value: String value
            
        Returns:
            Enum value or None if not found
        """
        try:
            return cls(value.lower())
        except (ValueError, AttributeError):
            return None
    
    def __str__(self) -> str:
        """
        Convert enum to string.
        
        Returns:
            String representation
        """
        return self.value 