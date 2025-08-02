"""
Template repository for template storage and retrieval.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
import glob
from datetime import datetime

from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.repositories.template_repository import ITemplateRepository
from src.domain.value_objects.service_type import ServiceType

logger = logging.getLogger(__name__)

class FileTemplateRepository(ITemplateRepository):
    """File-based implementation of template repository."""
    
    def __init__(self, template_dir: str = None):
        """
        Initialize FileTemplateRepository.
        
        Args:
            template_dir: Directory for storing templates
        """
        self.template_dir = template_dir or os.path.join("data", "templates")
        self.templates = {}  # In-memory cache: template_id -> ExecutionTemplate
        
        # Create template directory if it doesn't exist
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Load existing templates
        self._load_templates()
        
        logger.info(f"Initialized FileTemplateRepository with {len(self.templates)} templates")
    
    def _load_templates(self) -> None:
        """Load templates from disk."""
        if not os.path.exists(self.template_dir):
            logger.warning(f"Template directory not found: {self.template_dir}")
            return
            
        try:
            # Iterate through template files in directory
            for filename in os.listdir(self.template_dir):
                if not filename.endswith(".json"):
                    continue
                    
                file_path = os.path.join(self.template_dir, filename)
                
                with open(file_path, 'r') as f:
                    template_data = json.load(f)
                    
                template = ExecutionTemplate.from_dict(template_data)
                self.templates[template.id] = template
                
            logger.info(f"Loaded {len(self.templates)} templates from {self.template_dir}")
            
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
    
    async def get_by_id(self, template_id: str) -> Optional[ExecutionTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template if found, None otherwise
        """
        # Check in-memory cache first
        if template_id in self.templates:
            return self.templates[template_id]
            
        # Try to load from disk
        try:
            file_path = os.path.join(self.template_dir, f"{template_id}.json")
            
            if not os.path.exists(file_path):
                logger.warning(f"Template file not found: {file_path}")
                return None
                
            with open(file_path, 'r') as f:
                template_data = json.load(f)
                
            template = ExecutionTemplate.from_dict(template_data)
            
            # Cache in memory
            self.templates[template.id] = template
            
            logger.info(f"Loaded template {template_id} from disk")
            return template
            
        except Exception as e:
            logger.error(f"Error loading template {template_id}: {str(e)}")
            return None
    
    async def list_by_service_type(self, service_type: Optional[ServiceType] = None) -> List[ExecutionTemplate]:
        """
        List templates, optionally filtered by service type.
        
        Args:
            service_type: Optional service type filter
            
        Returns:
            List of matching templates
        """
        # Get all templates
        templates = list(self.templates.values())
        
        # Filter by service type if provided
        if service_type:
            templates = [t for t in templates if t.service_type == service_type]
            
        logger.info(f"Listed {len(templates)} templates" + (f" with service type {service_type.value}" if service_type else ""))
        return templates
    
    async def save(self, template: ExecutionTemplate) -> bool:
        """
        Save a template.
        
        Args:
            template: Template to save
            
        Returns:
            Success status
        """
        try:
            # Update template
            template.updated_at = datetime.utcnow()
            
            # Save to memory
            self.templates[template.id] = template
            
            # Save to disk
            file_path = os.path.join(self.template_dir, f"{template.id}.json")
            
            with open(file_path, 'w') as f:
                json.dump(template.to_dict(), f, indent=2)
                
            logger.info(f"Saved template {template.id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving template {template.id}: {str(e)}")
            return False
    
    async def add(self, template: ExecutionTemplate) -> bool:
        """
        Add a new template.
        
        Args:
            template: Template to add
            
        Returns:
            Success status
        """
        # Check if template already exists
        if template.id in self.templates:
            logger.warning(f"Template {template.id} already exists")
            return False
            
        # This is the same as save
        return await self.save(template)

    async def list(self) -> List[ExecutionTemplate]:
        """
        List all templates.
        
        Returns:
            List of templates
        """
        # This is the same as list_by_service_type with no service_type filter
        return await self.list_by_service_type()
    
    async def delete(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            Success status
        """
        try:
            # Check if file exists
            file_path = os.path.join(self.template_dir, f"{template_id}.json")
            if not os.path.exists(file_path):
                logger.warning(f"Template file not found for deletion: {file_path}")
                return False
            
            # Remove from memory cache
            if template_id in self.templates:
                del self.templates[template_id]
                
            # Delete file
            os.remove(file_path)
            
            logger.info(f"Deleted template {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {str(e)}")
            return False 