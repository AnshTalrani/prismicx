"""Worker for generative service.

Processes contexts requiring generative AI services by pulling directly from the repository.
"""
from typing import Dict, Any, Optional

from src.infrastructure.clients.generative_client import GenerativeClient
from src.infrastructure.services.worker_base import ClientWorker

class GenerativeWorker(ClientWorker):
    """Worker for generative service."""
    
    def __init__(
        self, 
        repository, 
        client: Optional[GenerativeClient] = None,
        **kwargs
    ):
        """
        Initialize generative worker.
        
        Args:
            repository: MongoDB repository for context access
            client: Optional generative client instance
            **kwargs: Additional arguments to pass to base class
        """
        super().__init__("GENERATIVE", repository, **kwargs)
        self.client = client or GenerativeClient()
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a context using the generative client.
        
        Args:
            context: Context to process
            
        Returns:
            Processing result
        """
        template_id = context["template"]["id"]
        service_template = context["template"].get("service_template", {})
        
        # Log processing start
        self.logger.info(f"Processing template {template_id} with generative client")
        
        # Execute template using generative client
        result = await self.client.execute_template(
            template_id=template_id,
            service_template=service_template,
            context=context
        )
        
        return result 