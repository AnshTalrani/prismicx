"""Template repository interface for the domain layer."""
from typing import List, Optional, Protocol

from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.value_objects.service_type import ServiceType

class ITemplateRepository(Protocol):
    """Interface for template repository operations."""
    
    async def get_by_id(self, template_id: str) -> Optional[ExecutionTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template if found, None otherwise
        """
        ...
    
    async def list_by_service_type(self, service_type: Optional[ServiceType] = None) -> List[ExecutionTemplate]:
        """
        List templates, optionally filtered by service type.
        
        Args:
            service_type: Optional service type filter
            
        Returns:
            List of matching templates
        """
        ...
    
    async def save(self, template: ExecutionTemplate) -> bool:
        """
        Save a template.
        
        Args:
            template: Template to save
            
        Returns:
            Success status
        """
        ... 