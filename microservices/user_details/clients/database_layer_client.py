import os
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseLayerClient:
    """
    Base client for interacting with the Database Layer services.
    Provides common functionality for making HTTP requests to the services.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the database layer client.
        
        Args:
            base_url: Base URL for the service (defaults to env var if not provided)
            api_key: API key for authentication (defaults to env var if not provided)
        """
        self.base_url = base_url or os.getenv('DATABASE_LAYER_BASE_URL', 'http://user-data-service:8000')
        self.api_key = api_key or os.getenv('DATABASE_LAYER_API_KEY', 'default_api_key')
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,  # 30 second timeout
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
        )
        logger.info(f"Initialized DatabaseLayerClient with base URL: {self.base_url}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None):
        """
        Make a GET request to the database layer service.
        
        Args:
            path: API endpoint path
            params: Query parameters
            tenant_id: Tenant ID for multi-tenant requests
        
        Returns:
            Response data
        """
        headers = {"X-Tenant-ID": tenant_id} if tenant_id else {}
        try:
            response = await self.client.get(path, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during GET request to {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during GET request to {path}: {e}")
            raise
    
    async def post(self, path: str, data: Dict[str, Any], tenant_id: Optional[str] = None):
        """
        Make a POST request to the database layer service.
        
        Args:
            path: API endpoint path
            data: Request data
            tenant_id: Tenant ID for multi-tenant requests
        
        Returns:
            Response data
        """
        headers = {"X-Tenant-ID": tenant_id} if tenant_id else {}
        try:
            response = await self.client.post(path, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during POST request to {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during POST request to {path}: {e}")
            raise
    
    async def put(self, path: str, data: Dict[str, Any], tenant_id: Optional[str] = None):
        """
        Make a PUT request to the database layer service.
        
        Args:
            path: API endpoint path
            data: Request data
            tenant_id: Tenant ID for multi-tenant requests
        
        Returns:
            Response data
        """
        headers = {"X-Tenant-ID": tenant_id} if tenant_id else {}
        try:
            response = await self.client.put(path, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during PUT request to {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during PUT request to {path}: {e}")
            raise
    
    async def delete(self, path: str, tenant_id: Optional[str] = None):
        """
        Make a DELETE request to the database layer service.
        
        Args:
            path: API endpoint path
            tenant_id: Tenant ID for multi-tenant requests
        
        Returns:
            Response data or None
        """
        headers = {"X-Tenant-ID": tenant_id} if tenant_id else {}
        try:
            response = await self.client.delete(path, headers=headers)
            response.raise_for_status()
            if response.content:
                return response.json()
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during DELETE request to {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during DELETE request to {path}: {e}")
            raise 