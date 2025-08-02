"""Template service implementation."""
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
import json
import os
import uuid

from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.value_objects.service_type import ServiceType
from src.application.interfaces.template_service import ITemplateService
from src.domain.repositories.template_repository import ITemplateRepository
from src.application.interfaces.repository.purpose_repository import IPurposeRepository
from src.utils.id_utils import generate_request_id

logger = logging.getLogger(__name__)

class TemplateService(ITemplateService):
    """
    Implementation of the template service.
    
    Key Features:
    - Template storage and retrieval
    - Service-type specific validation
    - Template filtering by service type
    """
    
    def __init__(self, template_repository: ITemplateRepository, purpose_repository: Optional[IPurposeRepository] = None):
        """
        Initialize template service.
        
        Args:
            template_repository: Repository for template storage
            purpose_repository: Repository for purpose mappings (optional)
        """
        self.template_repository = template_repository
        self.purpose_repository = purpose_repository
        # Keep the file path as fallback if repository is not provided
        self.purpose_mapping_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "purpose_mapping.json"
        )
        logger.info("Template service initialized")
    
    async def add_template(self, template_data: Dict[str, Any]) -> bool:
        """
        Add a new template.
        
        Args:
            template_data: Template data as dictionary
            
        Returns:
            Success status
        """
        try:
            # Validate template data
            is_valid, error = await self.validate_template(template_data)
            if not is_valid:
                logger.error(f"Invalid template data: {error}")
                return False
            
            # Generate ID if not provided
            if "id" not in template_data:
                template_data["id"] = generate_request_id(source="template")
                
            if "created_at" not in template_data:
                template_data["created_at"] = datetime.utcnow().isoformat()
                
            template_data["updated_at"] = datetime.utcnow().isoformat()
            
            template = ExecutionTemplate.from_dict(template_data)
            
            # Save to repository
            success = await self.template_repository.save(template)
            if success:
                logger.info(f"Added template {template.id} for {template.service_type.value} service")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to add template: {str(e)}")
            return False
    
    async def get_template(self, template_id: str) -> Optional[ExecutionTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Unique identifier of the template
            
        Returns:
            Template if found, None otherwise
        """
        return await self.template_repository.get_by_id(template_id)
    
    async def list_templates(self, service_type: Optional[ServiceType] = None) -> List[ExecutionTemplate]:
        """
        List templates with optional service type filtering.
        
        Args:
            service_type: Optional service type filter
            
        Returns:
            List of matching templates
        """
        return await self.template_repository.list_by_service_type(service_type)
    
    async def validate_template(self, template_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a template's structure and data.
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate basic structure
            if 'service_type' not in template_data:
                return False, "Missing service_type"
            
            # Create template instance (this will validate the structure)
            ExecutionTemplate.from_dict(template_data)
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    async def get_service_specific_template(self, template_id: str) -> Optional[Any]:
        """
        Get the service-specific part of a template.
        
        Args:
            template_id: Template ID to look up
            
        Returns:
            Service-specific template if found
        """
        template = await self.get_template(template_id)
        if not template:
            return None
            
        if template.service_type == ServiceType.ANALYSIS:
            return template.analysis_template
        elif template.service_type == ServiceType.GENERATIVE:
            return template.generative_template
        elif template.service_type == ServiceType.COMMUNICATION:
            return template.communication_template
            
        return None
    
    async def get_template_by_purpose_id(self, purpose_id: str) -> Optional[ExecutionTemplate]:
        """
        Get template based on purpose ID.
        
        Args:
            purpose_id: Purpose ID
            
        Returns:
            Template if found, None otherwise
        """
        try:
            # Try to use the repository if available
            if self.purpose_repository:
                # Get purpose from repository
                purpose = await self.purpose_repository.get_purpose(purpose_id)
                if not purpose:
                    logger.warning(f"No purpose found for ID: {purpose_id}")
                    return None
                
                # Get the template ID from purpose attributes or template_ids
                template_id = None
                if purpose.attributes and "template_id" in purpose.attributes:
                    template_id = purpose.attributes["template_id"]
                elif purpose.template_ids and len(purpose.template_ids) > 0:
                    template_id = purpose.template_ids[0]
                
                if not template_id:
                    logger.warning(f"No template ID found for purpose: {purpose_id}")
                    return None
                
                logger.info(f"Found template ID {template_id} for purpose ID {purpose_id} using repository")
                return await self.get_template(template_id)
            
            # Fallback to direct file access if repository not available
            purpose_map = await self._load_purpose_mapping()
            if purpose_id not in purpose_map:
                logger.warning(f"No mapping found for purpose ID: {purpose_id} in file")
                return None
                
            template_id = purpose_map[purpose_id].get("template_id")
            if not template_id:
                logger.warning(f"No template ID specified for purpose ID: {purpose_id} in file")
                return None
                
            logger.info(f"Found template ID {template_id} for purpose ID {purpose_id} using file")
            return await self.get_template(template_id)
            
        except Exception as e:
            logger.error(f"Failed to get template for purpose {purpose_id}: {str(e)}")
            return None
    
    async def _load_purpose_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        Load purpose to template mapping directly from file.
        This is a fallback method when purpose_repository is not available.
        
        Returns:
            Dictionary mapping purpose IDs to their configurations
        """
        try:
            if not os.path.exists(self.purpose_mapping_file):
                logger.warning(f"Purpose mapping file not found: {self.purpose_mapping_file}")
                return {}
                
            with open(self.purpose_mapping_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load purpose mapping: {str(e)}")
            return {} 