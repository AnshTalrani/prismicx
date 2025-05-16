"""
Service type enum.
"""
from enum import Enum
from typing import Optional

class ServiceType(Enum):
    """
    Enum representing different service types.
    """
    
    GENERATIVE = "GENERATIVE"
    ANALYSIS = "ANALYSIS"
    COMMUNICATION = "COMMUNICATION"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['ServiceType']:
        """
        Convert string to enum value.
        
        Args:
            value: String value
            
        Returns:
            Enum value or None if not found
        """
        try:
            return cls(value.upper())
        except (ValueError, AttributeError):
            return None
    
    def __str__(self) -> str:
        """
        Convert enum to string.
        
        Returns:
            String representation
        """
        return self.value 