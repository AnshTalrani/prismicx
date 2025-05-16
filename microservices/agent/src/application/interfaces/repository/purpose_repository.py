"""Purpose repository interface for managing purpose definitions."""
from typing import List, Optional, Protocol

from src.domain.entities.purpose import Purpose

class IPurposeRepository(Protocol):
    """Interface for purpose repository."""
    
    async def get_purpose(self, purpose_id: str) -> Optional[Purpose]:
        """
        Get purpose by ID.
        
        Args:
            purpose_id: Purpose ID
            
        Returns:
            Purpose if found, None otherwise
        """
        ...
    
    async def list_purposes(self) -> List[Purpose]:
        """
        List all purposes.
        
        Returns:
            List of all purposes
        """
        ...
    
    async def add_purpose(self, purpose: Purpose) -> bool:
        """
        Add a new purpose.
        
        Args:
            purpose: Purpose to add
            
        Returns:
            Success status
        """
        ...
    
    async def update_purpose(self, purpose: Purpose) -> bool:
        """
        Update an existing purpose.
        
        Args:
            purpose: Purpose with updated data
            
        Returns:
            Success status
        """
        ...
    
    async def delete_purpose(self, purpose_id: str) -> bool:
        """
        Delete a purpose.
        
        Args:
            purpose_id: ID of purpose to delete
            
        Returns:
            Success status
        """
        ...
    
    async def get_purpose_by_name(self, name: str) -> Optional[Purpose]:
        """
        Get purpose by name.
        
        Args:
            name: Purpose name
            
        Returns:
            Purpose if found, None otherwise
        """
        ... 