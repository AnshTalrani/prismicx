"""Worker for analysis service.

Processes contexts requiring data analysis services by pulling directly from the repository.
Includes integrated client functionality for communicating with the Analysis Base service.
"""
import logging
import json
import httpx
import os
import uuid
from typing import Dict, Any, Optional

from src.infrastructure.workers.worker_base import ClientWorker

class AnalysisWorker(ClientWorker):
    """Worker for analysis service with integrated client functionality."""
    
    def __init__(
        self, 
        repository,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize analysis worker.
        
        Args:
            repository: MongoDB repository for context access
            base_url: Base URL of the Analysis Base service
            api_key: API key for authentication
            **kwargs: Additional arguments to pass to base class
        """
        super().__init__("ANALYSIS", repository, **kwargs)
        
        # Client configuration
        self.base_url = base_url or os.getenv("ANALYSIS_BASE_URL", "http://analysis-base:8080")
        self.api_key = api_key or os.getenv("ANALYSIS_BASE_API_KEY", "")
        self.http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }
        )
        self.logger.info(f"Initialized AnalysisWorker with URL: {self.base_url}")
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a context using the integrated analysis client functionality.
        
        Args:
            context: Context to process
            
        Returns:
            Processing result
        """
        template_id = context["template"]["id"]
        service_template = context["template"].get("service_template", {})
        
        # Log processing start
        self.logger.info(f"Processing template {template_id} with analysis service")
        
        # Execute template
        result = await self.execute_template(
            template_id=template_id,
            service_template=service_template,
            context=context
        )
        
        return result
    
    async def execute_template(
        self, 
        template_id: str, 
        service_template: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a template on the Analysis Base service.
        
        Args:
            template_id: ID of the template to execute
            service_template: The service-specific template data 
            context: Execution context
            
        Returns:
            Analysis result
        """
        try:
            # Prepare request payload
            payload = {
                "template_id": template_id,
                "template_data": service_template,
                "context": context,
                "request_id": context.get("request_id", str(uuid.uuid4()))
            }
            
            # Check if service is available
            if await self._is_service_available():
                # Send request to Analysis Base service
                url = f"{self.base_url}/api/v1/analyze"
                response = await self.http_client.post(url, json=payload)
                
                if response.status_code == 200:
                    # Parse response
                    result = response.json()
                    self.logger.info(f"Successfully executed template {template_id}")
                    return result
                else:
                    # Handle error response
                    error_message = f"Error from Analysis Base: {response.status_code} - {response.text}"
                    self.logger.error(error_message)
                    return self._create_error_response(template_id, error_message)
            else:
                # Return error response if service not available
                error_message = "Analysis Base service not available"
                self.logger.error(error_message)
                return self._create_error_response(template_id, error_message)
                
        except Exception as e:
            self.logger.exception(f"Error executing template {template_id}: {str(e)}")
            return self._create_error_response(template_id, str(e))

    async def _is_service_available(self) -> bool:
        """
        Check if the Analysis Base service is available.
        
        Returns:
            True if the service is available, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            response = await self.http_client.get(url, timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
            
    def _create_error_response(self, template_id: str, error_message: str) -> Dict[str, Any]:
        """
        Create an error response.
        
        Args:
            template_id: Template ID
            error_message: Error message
            
        Returns:
            Error response
        """
        return {
            "template_id": template_id,
            "success": False,
            "status": "error",
            "error": error_message
        }
        
    async def stop(self):
        """Stop the worker processing loop and close HTTP client."""
        # First call the parent stop method
        await super().stop()
        
        # Then close the HTTP client
        if self.http_client:
            await self.http_client.aclose()
            self.logger.info("Closed HTTP client")
            
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop() 