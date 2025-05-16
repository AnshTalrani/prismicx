"""File-based implementation of the template repository."""
import json
import os
import logging
from typing import Dict, List, Optional, Any
import asyncio

from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.value_objects.service_type import ServiceType
from src.domain.repositories.template_repository import ITemplateRepository

logger = logging.getLogger(__name__)

class FileTemplateRepository(ITemplateRepository):
    """
    A repository implementation that stores templates in a JSON file.
    
    This repository:
    1. Stores templates in a simple JSON file
    2. Provides CRUD operations for template management
    3. Supports querying by service type
    
    Note: This is a simple implementation for testing and development, not 
    intended for production use with large datasets.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the file-based template repository.
        
        Args:
            file_path: Path to the JSON file to use for storage
        """
        self.file_path = file_path
        self._templates: Dict[str, ExecutionTemplate] = {}
        self._loaded = False
        self._lock = asyncio.Lock()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create the file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)
        
        logger.info(f"Initialized file template repository with file: {file_path}")
    
    async def _ensure_loaded(self) -> None:
        """Ensure templates are loaded from the file."""
        if not self._loaded:
            await self._load_templates()
    
    async def _load_templates(self) -> None:
        """Load templates from the file."""
        async with self._lock:
            try:
                if not os.path.exists(self.file_path):
                    self._templates = {}
                    return
                
                with open(self.file_path, 'r') as f:
                    templates_data = json.load(f)
                
                self._templates = {}
                for template_data in templates_data:
                    template = ExecutionTemplate.from_dict(template_data)
                    self._templates[template.id] = template
                
                self._loaded = True
                logger.info(f"Loaded {len(self._templates)} templates from file")
                
            except Exception as e:
                logger.error(f"Failed to load templates from file: {str(e)}")
                self._templates = {}
    
    async def _save_templates(self) -> None:
        """Save templates to the file."""
        async with self._lock:
            try:
                templates_data = [template.to_dict() for template in self._templates.values()]
                
                with open(self.file_path, 'w') as f:
                    json.dump(templates_data, f, indent=2)
                
                logger.info(f"Saved {len(self._templates)} templates to file")
                
            except Exception as e:
                logger.error(f"Failed to save templates to file: {str(e)}")
    
    async def get_by_id(self, template_id: str) -> Optional[ExecutionTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: The ID of the template to retrieve
            
        Returns:
            The template if found, None otherwise
        """
        await self._ensure_loaded()
        return self._templates.get(template_id)
    
    async def list_by_service_type(self, service_type: Optional[ServiceType] = None) -> List[ExecutionTemplate]:
        """
        List templates, optionally filtered by service type.
        
        Args:
            service_type: Optional service type to filter by
            
        Returns:
            List of matching templates
        """
        await self._ensure_loaded()
        
        if service_type is None:
            return list(self._templates.values())
        
        return [
            template for template in self._templates.values()
            if template.service_type == service_type
        ]
    
    async def save(self, template: ExecutionTemplate) -> bool:
        """
        Save a template to the repository.
        
        Args:
            template: The template to save
            
        Returns:
            Success status
        """
        await self._ensure_loaded()
        
        try:
            self._templates[template.id] = template
            await self._save_templates()
            return True
        except Exception as e:
            logger.error(f"Failed to save template: {str(e)}")
            return False
    
    async def delete(self, template_id: str) -> bool:
        """
        Delete a template from the repository.
        
        Args:
            template_id: The ID of the template to delete
            
        Returns:
            Success status
        """
        await self._ensure_loaded()
        
        if template_id not in self._templates:
            return False
        
        try:
            del self._templates[template_id]
            await self._save_templates()
            return True
        except Exception as e:
            logger.error(f"Failed to delete template: {str(e)}")
            return False 