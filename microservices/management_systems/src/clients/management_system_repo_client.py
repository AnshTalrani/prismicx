"""
Management System Repository client for interacting with the management-system-repo service in the database layer.

This client provides methods for accessing the management system repository API exposed
by the management-system-repo service in the database layer.
"""

import logging
import os
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class ManagementSystemRepoClient:
    """Client for interacting with the management-system-repo service in the database layer."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the management system repository client.
        
        Args:
            base_url: Base URL for the management-system-repo service
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.http_client = None
    
    async def initialize(self):
        """Initialize the HTTP client for making API requests."""
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            headers=self.headers
        )
        logger.info(f"ManagementSystemRepoClient initialized with base URL: {self.base_url}")
    
    async def close(self):
        """Close the HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("ManagementSystemRepoClient HTTP client closed")
    
    async def count_system_templates(self) -> int:
        """
        Count the number of system templates in the repository.
        
        Returns:
            Number of templates
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/systems/templates/count"
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json().get("count", 0)
        except Exception as e:
            logger.error(f"Error counting system templates: {str(e)}")
            return 0
    
    async def create_system_template(self, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new system template in the repository.
        
        Args:
            template_data: Template definition data
            
        Returns:
            Created template data or None if failed
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/systems/templates"
            response = await self.http_client.post(url, json=template_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating system template: {str(e)}")
            return None
    
    async def get_management_systems(self) -> List[Dict[str, Any]]:
        """
        Get all available management systems.
        
        Returns:
            List of management system definitions
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/systems"
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving management systems: {str(e)}")
            return []
    
    async def get_management_system(self, system_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific management system.
        
        Args:
            system_id: System identifier
            
        Returns:
            System data or None if not found
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/systems/{system_id}"
            response = await self.http_client.get(url)
            
            if response.status_code == 404:
                logger.debug(f"Management system not found: {system_id}")
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving management system {system_id}: {str(e)}")
            return None
    
    async def create_management_system(self, system_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new management system.
        
        Args:
            system_data: System definition data
            
        Returns:
            Created system data or None if failed
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/systems"
            response = await self.http_client.post(url, json=system_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating management system: {str(e)}")
            return None
    
    async def update_management_system(self, system_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a management system.
        
        Args:
            system_id: System identifier
            updates: Updates to apply
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/systems/{system_id}"
            response = await self.http_client.patch(url, json=updates)
            
            if response.status_code == 404:
                logger.debug(f"Management system not found: {system_id}")
                return False
                
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error updating management system {system_id}: {str(e)}")
            return False
    
    async def delete_management_system(self, system_id: str) -> bool:
        """
        Delete a management system.
        
        Args:
            system_id: System identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/systems/{system_id}"
            response = await self.http_client.delete(url)
            
            if response.status_code == 404:
                logger.debug(f"Management system not found: {system_id}")
                return False
                
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error deleting management system {system_id}: {str(e)}")
            return False
    
    async def get_tenant_systems(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get all system instances for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            List of system instances
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems"
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving tenant systems for {tenant_id}: {str(e)}")
            return []
    
    async def get_system_instance(self, tenant_id: str, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            
        Returns:
            System instance data or None if not found
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{instance_id}"
            response = await self.http_client.get(url)
            
            if response.status_code == 404:
                logger.debug(f"System instance not found: {instance_id} for tenant {tenant_id}")
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving system instance {instance_id} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def create_system_instance(
        self,
        tenant_id: str,
        system_id: str, 
        name: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new system instance for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            system_id: System identifier
            name: Instance name
            settings: Instance settings
            
        Returns:
            Created instance data or None if failed
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems"
            payload = {
                "system_id": system_id,
                "name": name,
                "settings": settings or {}
            }
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating system instance for tenant {tenant_id}: {str(e)}")
            return None
    
    async def update_system_instance(
        self,
        tenant_id: str,
        instance_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            updates: Updates to apply
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{instance_id}"
            response = await self.http_client.patch(url, json=updates)
            
            if response.status_code == 404:
                logger.debug(f"System instance not found: {instance_id} for tenant {tenant_id}")
                return False
                
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error updating system instance {instance_id} for tenant {tenant_id}: {str(e)}")
            return False
    
    async def delete_system_instance(self, tenant_id: str, instance_id: str) -> bool:
        """
        Delete a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{instance_id}"
            response = await self.http_client.delete(url)
            
            if response.status_code == 404:
                logger.debug(f"System instance not found: {instance_id} for tenant {tenant_id}")
                return False
                
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error deleting system instance {instance_id} for tenant {tenant_id}: {str(e)}")
            return False
    
    async def get_system_data(
        self, 
        tenant_id: str,
        instance_id: str,
        view_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get data for a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            view_id: View identifier
            filters: Data filters
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated data or None if failed
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{instance_id}/data"
            params = {"page": page, "page_size": page_size}
            
            if view_id:
                params["view_id"] = view_id
                
            if filters:
                # For filters, we need to use POST with a body instead of GET with query params
                url += "/filter"
                response = await self.http_client.post(
                    url, 
                    params=params,
                    json={"filters": filters}
                )
            else:
                response = await self.http_client.get(url, params=params)
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving system data for instance {instance_id}, tenant {tenant_id}: {str(e)}")
            return None
    
    async def create_data_item(
        self,
        tenant_id: str,
        instance_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new data item in a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            data: Item data
            
        Returns:
            Created item data or None if failed
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{instance_id}/data"
            payload = {"data": data}
            
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating data item for instance {instance_id}, tenant {tenant_id}: {str(e)}")
            return None 