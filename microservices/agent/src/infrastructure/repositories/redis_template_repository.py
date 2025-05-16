"""Redis implementation of the template repository."""
from typing import Dict, List, Optional, Any
import logging
from redis import Redis
import json

from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.value_objects.service_type import ServiceType
from src.domain.repositories.template_repository import ITemplateRepository

logger = logging.getLogger(__name__)

class RedisTemplateRepository(ITemplateRepository):
    """
    Redis implementation of the template repository.
    
    This implementation stores templates in Redis, providing persistence
    and fast access to templates.
    """
    
    def __init__(self, redis_host: str = 'redis', redis_port: int = 6379, redis_db: int = 0):
        """
        Initialize the Redis repository.
        
        Args:
            redis_host: Redis host address
            redis_port: Redis port number
            redis_db: Redis database number
        """
        self.redis = Redis(host=redis_host, port=redis_port, db=redis_db)
        logger.info(f"Redis template repository initialized at {redis_host}:{redis_port}")
    
    async def save(self, template: ExecutionTemplate) -> bool:
        """
        Save a template to Redis.
        
        Args:
            template: Template to save
            
        Returns:
            Success status
        """
        try:
            # Convert template to dictionary and serialize to JSON
            template_data = template.to_dict()
            template_json = json.dumps(template_data)
            
            # Save to Redis with template ID as key
            self.redis.set(f"template:{template.id}", template_json)
            
            # Add to service type index for faster filtering
            self.redis.sadd(f"service_type:{template.service_type.value}", template.id)
            
            logger.info(f"Saved template {template.id} to Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save template to Redis: {str(e)}")
            return False
    
    async def get_by_id(self, template_id: str) -> Optional[ExecutionTemplate]:
        """
        Get a template by ID from Redis.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template if found, None otherwise
        """
        try:
            # Get template data from Redis
            template_json = self.redis.get(f"template:{template_id}")
            if not template_json:
                return None
                
            # Parse JSON and create template instance
            template_data = json.loads(template_json)
            return ExecutionTemplate.from_dict(template_data)
            
        except Exception as e:
            logger.error(f"Failed to get template from Redis: {str(e)}")
            return None
    
    async def delete(self, template_id: str) -> bool:
        """
        Delete a template by ID from Redis.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Success status
        """
        try:
            # Get template to determine service type
            template = await self.get_by_id(template_id)
            if not template:
                return False
                
            # Delete from Redis
            self.redis.delete(f"template:{template_id}")
            
            # Remove from service type index
            self.redis.srem(f"service_type:{template.service_type.value}", template_id)
            
            logger.info(f"Deleted template {template_id} from Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete template from Redis: {str(e)}")
            return False
    
    async def update(self, template: ExecutionTemplate) -> bool:
        """
        Update an existing template in Redis.
        
        Args:
            template: Updated template
            
        Returns:
            Success status
        """
        try:
            # Get existing template to check service type
            existing = await self.get_by_id(template.id)
            if not existing:
                return False
                
            # If service type changed, update indices
            if existing.service_type != template.service_type:
                self.redis.srem(f"service_type:{existing.service_type.value}", template.id)
                self.redis.sadd(f"service_type:{template.service_type.value}", template.id)
            
            # Save updated template
            return await self.save(template)
            
        except Exception as e:
            logger.error(f"Failed to update template in Redis: {str(e)}")
            return False
    
    async def list_by_service_type(self, service_type: Optional[ServiceType] = None) -> List[ExecutionTemplate]:
        """
        List templates with optional filtering by service type.
        
        Args:
            service_type: Optional filter by service type
            
        Returns:
            List of matching templates
        """
        try:
            if service_type:
                # Get template IDs for specific service type
                template_ids = self.redis.smembers(f"service_type:{service_type.value}")
            else:
                # Get all template keys
                template_keys = self.redis.keys("template:*")
                template_ids = [key.decode().split(":")[1] for key in template_keys]
            
            # Get all templates
            templates = []
            for template_id in template_ids:
                template = await self.get_by_id(template_id.decode() if isinstance(template_id, bytes) else template_id)
                if template:
                    templates.append(template)
            
            return templates
            
        except Exception as e:
            logger.error(f"Failed to list templates from Redis: {str(e)}")
            return []
    
    async def search(self, query: str, filter_criteria: Dict[str, Any] = None) -> List[ExecutionTemplate]:
        """
        Search templates by query and filter criteria.
        
        Args:
            query: Search query
            filter_criteria: Additional filter criteria
            
        Returns:
            List of matching templates
        """
        try:
            # Get all templates
            templates = await self.list_by_service_type()
            
            # Filter by query
            matching_templates = []
            for template in templates:
                # Check if query matches description or tags
                if (query.lower() in template.description.lower() or
                    any(query.lower() in tag.lower() for tag in template.tags)):
                    
                    # Apply additional filter criteria if provided
                    if filter_criteria:
                        matches_criteria = True
                        for key, value in filter_criteria.items():
                            if hasattr(template, key) and getattr(template, key) != value:
                                matches_criteria = False
                                break
                        
                        if not matches_criteria:
                            continue
                    
                    matching_templates.append(template)
            
            return matching_templates
            
        except Exception as e:
            logger.error(f"Failed to search templates in Redis: {str(e)}")
            return [] 