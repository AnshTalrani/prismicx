"""Worker for communication service.

Processes contexts requiring communication services by pulling directly from the repository.
"""
from typing import Dict, Any, Optional

from src.infrastructure.clients.communication_client import CommunicationClient
from src.infrastructure.services.worker_base import ClientWorker

class CommunicationWorker(ClientWorker):
    """Worker for communication service."""
    
    def __init__(
        self, 
        repository, 
        client: Optional[CommunicationClient] = None,
        **kwargs
    ):
        """
        Initialize communication worker.
        
        Args:
            repository: MongoDB repository for context access
            client: Optional communication client instance
            **kwargs: Additional arguments to pass to base class
        """
        super().__init__("COMMUNICATION", repository, **kwargs)
        self.client = client or CommunicationClient()
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a context using the communication client.
        
        Args:
            context: Context to process
            
        Returns:
            Processing result
        """
        template_id = context["template"]["id"]
        service_template = context["template"].get("service_template", {})
        
        # Log processing start
        self.logger.info(f"Processing template {template_id} with communication client")
        
        # Execute template using communication client
        result = await self.client.execute_template(
            template_id=template_id,
            service_template=service_template,
            context=context
        )
        
        return result 