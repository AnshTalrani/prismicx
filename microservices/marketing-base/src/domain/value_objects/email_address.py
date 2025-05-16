"""
Email address value object.

This module defines a value object for email addresses with validation.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailAddress:
    """
    Value object representing a valid email address.
    Ensures email addresses are properly formatted.
    """
    
    address: str
    
    def __post_init__(self):
        """Validate the email address format after initialization."""
        if not self.is_valid(self.address):
            raise ValueError(f"Invalid email address: {self.address}")
        
        # Convert address to lowercase for consistent comparison
        object.__setattr__(self, 'address', self.address.lower())
    
    @staticmethod
    def is_valid(email: str) -> bool:
        """
        Validate if a string is a properly formatted email address.
        
        Args:
            email: The email address to validate
            
        Returns:
            True if the email is valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
            
        # Simple regex for email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def __str__(self) -> str:
        """Return the string representation of the email address."""
        return self.address
        
    def __eq__(self, other) -> bool:
        """Compare email addresses (case-insensitive)."""
        if isinstance(other, EmailAddress):
            return self.address == other.address
        elif isinstance(other, str):
            return self.address == other.lower()
        return False 