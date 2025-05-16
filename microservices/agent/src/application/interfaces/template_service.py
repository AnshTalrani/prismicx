"""Interface for template service operations."""
from typing import Dict, Any, Optional, List, Protocol, Tuple

from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.value_objects.service_type import ServiceType

class ITemplateService(Protocol):
    """
    Interface for template service operations.
    
    This interface defines the contract for template service implementations.
    It handles template management operations like adding, retrieving, listing, and
    validating templates.
    """
    
    async def add_template(self, template_data: Dict[str, Any]) -> bool:
        """
        Add a new template.
        
        Args:
            template_data: Template data as dictionary
            
        Returns:
            Success status
        """
        ...
    
    async def get_template(self, template_id: str) -> Optional[ExecutionTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Unique identifier of the template
            
        Returns:
            Template if found, None otherwise
        """
        ...
    
    async def list_templates(self, service_type: Optional[ServiceType] = None) -> List[ExecutionTemplate]:
        """
        List templates with optional service type filtering.
        
        Args:
            service_type: Optional service type filter
            
        Returns:
            List of matching templates
        """
        ...
    
    async def validate_template(self, template_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a template's structure and data.
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        ...
    
    async def get_service_specific_template(self, template_id: str) -> Optional[Any]:
        """
        Get the service-specific part of a template.
        
        Args:
            template_id: Template ID to look up
            
        Returns:
            Service-specific template if found
        """
        ...
    
    async def get_template_by_purpose_id(self, purpose_id: str) -> Optional[ExecutionTemplate]:
        """
        Get template based on purpose ID.
        
        Args:
            purpose_id: Purpose ID
            
        Returns:
            Template if found, None otherwise
        """
        ... 