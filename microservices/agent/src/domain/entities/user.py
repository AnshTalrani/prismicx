"""
User entity representing a user in the system.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class User:
    """
    User entity representing a user in the system.
    
    This class contains essential user information and is used for
    managing user-specific contexts and batch references.
    
    Attributes:
        id: Unique identifier for the user
        name: User's display name
        email: User's email address
        metadata: Additional user metadata
    """
    
    id: str
    name: str
    email: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def display_name(self) -> str:
        """User's display name, fallback to email if name not available."""
        return self.name if self.name else self.email
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user to dictionary representation.
        
        Returns:
            Dictionary representation of user
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Create a user from dictionary data.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            User instance
            
        Raises:
            ValueError: If required fields are missing
        """
        if not data.get("id"):
            raise ValueError("User ID is required")
            
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            email=data.get("email", ""),
            metadata=data.get("metadata", {})
        )
    
    def has_permissions_for(self, purpose_id: str) -> bool:
        """
        Check if user has permissions for a specific purpose.
        
        Args:
            purpose_id: Purpose ID to check permissions for
            
        Returns:
            True if user has permissions, False otherwise
        """
        # This is a placeholder implementation
        # In a real system, this would check against a permissions system
        
        # Default to True for now
        return True 