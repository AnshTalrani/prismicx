"""Template manager interface for the application layer."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any

from domain.entities.template import ExecutionTemplate
from domain.value_objects.service_type import ServiceType

class ITemplateManager(ABC):
    """Interface for template management operations."""
    
    @abstractmethod
    def add_template(self, template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Add a new template to the system.
        
        Args:
            template_data: Template data to add
            
        Returns:
            Tuple of (success, error_message)
        """
        pass
    
    @abstractmethod
    def get_template(self, template_id: str) -> Optional[ExecutionTemplate]:
        """
        Retrieve a template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_templates(self, service_type: Optional[ServiceType] = None) -> List[ExecutionTemplate]:
        """
        List templates with optional filtering.
        
        Args:
            service_type: Optional filter by service type
            
        Returns:
            List of matching templates
        """
        pass
    
    @abstractmethod
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Update an existing template.
        
        Args:
            template_id: Template identifier
            template_data: Updated template data
            
        Returns:
            Tuple of (success, error_message)
        """
        pass
    
    @abstractmethod
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    def validate_template(self, template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a template's structure and content.
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Tuple of (valid, error_message)
        """
        pass
    
    @abstractmethod
    def search_templates(self, query: str, filter_criteria: Dict[str, Any] = None) -> List[ExecutionTemplate]:
        """
        Search templates by query and filter criteria.
        
        Args:
            query: Search query
            filter_criteria: Additional filter criteria
            
        Returns:
            List of matching templates
        """
        pass 