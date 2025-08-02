import os
import logging
from typing import Dict, Any, Optional

from services.config_service import ConfigService
from ..services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class TenantConfigService:
    """
    A tenant-aware configuration service that loads templates from tenant-specific directories.
    
    This service extends the base ConfigService to support multi-tenancy by:
    1. Loading configurations from tenant-specific directories
    2. Falling back to default templates if tenant-specific ones don't exist
    3. Maintaining separate configurations for each tenant in memory
    """
    
    def __init__(self, tenant_service: TenantService = None):
        """
        Initialize the tenant config service.
        
        Args:
            tenant_service: Service for accessing tenant information.
        """
        self.tenant_service = tenant_service or TenantService()
        self.config_services = {}  # Mapping of tenant_id -> ConfigService instance
        self.default_config_service = None  # For fallback when no tenant ID is provided
    
    def get_config_service(self, tenant_id: str = None) -> ConfigService:
        """
        Get or create a ConfigService for a tenant.
        
        Args:
            tenant_id: The ID of the tenant, or None for the default config
            
        Returns:
            A ConfigService instance for the tenant
        """
        # If no tenant ID is provided, return the default config service
        if not tenant_id:
            if not self.default_config_service:
                default_path = os.environ.get('DEFAULT_CONFIG_PATH', 'config/templates')
                self.default_config_service = ConfigService(config_path=default_path)
                logger.info(f"Created default ConfigService with path: {default_path}")
            return self.default_config_service
        
        # If we already have a ConfigService for this tenant, return it
        if tenant_id in self.config_services:
            return self.config_services[tenant_id]
        
        # Check if the tenant exists
        tenant = self.tenant_service.get_tenant(tenant_id)
        if not tenant:
            logger.warning(f"Tenant not found: {tenant_id}, using default config")
            return self.get_config_service(None)
        
        # Get the tenant-specific templates path
        templates_path = self.tenant_service.get_tenant_templates_path(tenant_id)
        
        # Create a new ConfigService for this tenant
        config_service = ConfigService(config_path=templates_path)
        self.config_services[tenant_id] = config_service
        
        logger.info(f"Created ConfigService for tenant {tenant_id} with path: {templates_path}")
        return config_service
    
    def reload_all_configs(self, auto_migrate: bool = True) -> Dict[str, Any]:
        """
        Reload configurations for all tenants.
        
        Args:
            auto_migrate: Whether to automatically migrate data when templates change
            
        Returns:
            A summary of reload operations by tenant
        """
        results = {}
        
        # Reload default config
        if self.default_config_service:
            results['default'] = self.default_config_service.reload_configs(auto_migrate=auto_migrate)
        
        # Reload tenant-specific configs
        for tenant_id, config_service in self.config_services.items():
            results[tenant_id] = config_service.reload_configs(auto_migrate=auto_migrate)
        
        return results
    
    def get_insight_structure(self, tenant_id: str = None) -> Dict[str, Any]:
        """
        Get the user insight structure for a tenant.
        
        Args:
            tenant_id: The ID of the tenant, or None for the default structure
            
        Returns:
            The insight structure configuration
        """
        config_service = self.get_config_service(tenant_id)
        return config_service.get_insight_structure()
    
    def get_extension_type_config(self, extension_type: str, tenant_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific extension type for a tenant.
        
        Args:
            extension_type: The type of extension
            tenant_id: The ID of the tenant, or None for the default configuration
            
        Returns:
            The extension type configuration, or None if not found
        """
        config_service = self.get_config_service(tenant_id)
        return config_service.get_extension_type_config(extension_type)
    
    def get_all_extension_types(self, tenant_id: str = None) -> list:
        """
        Get all configured extension types for a tenant.
        
        Args:
            tenant_id: The ID of the tenant, or None for the default types
            
        Returns:
            A list of extension type names
        """
        config_service = self.get_config_service(tenant_id)
        return config_service.get_all_extension_types()
    
    def get_default_topics(self, tenant_id: str = None) -> list:
        """
        Get the default topics for a tenant.
        
        Args:
            tenant_id: The ID of the tenant, or None for the default topics
            
        Returns:
            A list of default topic dictionaries
        """
        config_service = self.get_config_service(tenant_id)
        return config_service.get_default_topics()
    
    def validate_insight_structure(self, insight: Dict[str, Any], tenant_id: str = None) -> bool:
        """
        Validate a user insight against the defined structure for a tenant.
        
        Args:
            insight: The user insight to validate
            tenant_id: The ID of the tenant, or None for the default structure
            
        Returns:
            True if the insight is valid, False otherwise
        """
        config_service = self.get_config_service(tenant_id)
        return config_service.validate_insight_structure(insight)
    
    def validate_extension(self, extension_type: str, extension: Dict[str, Any], tenant_id: str = None) -> bool:
        """
        Validate an extension against its type-specific schema for a tenant.
        
        Args:
            extension_type: The type of extension
            extension: The extension to validate
            tenant_id: The ID of the tenant, or None for the default schema
            
        Returns:
            True if the extension is valid, False otherwise
        """
        config_service = self.get_config_service(tenant_id)
        return config_service.validate_extension(extension_type, extension)
    
    def migrate_existing_insights(self, insight_repo, tenant_id: str = None) -> Dict[str, Any]:
        """
        Migrate existing user insights for a tenant.
        
        Args:
            insight_repo: The repository for user insights
            tenant_id: The ID of the tenant, or None to migrate all tenants
            
        Returns:
            A summary of migration results
        """
        if tenant_id:
            # Migrate a specific tenant
            config_service = self.get_config_service(tenant_id)
            return config_service.migrate_existing_insights(insight_repo)
        else:
            # Migrate all tenants
            results = {}
            
            # Get all active tenants
            tenants = self.tenant_service.get_active_tenants()
            
            for tenant in tenants:
                config_service = self.get_config_service(tenant.tenant_id)
                results[tenant.tenant_id] = config_service.migrate_existing_insights(insight_repo)
            
            return {
                "status": "completed",
                "tenant_results": results
            }
    
    def migrate_extensions(self, extension_repo, tenant_id: str = None) -> Dict[str, Any]:
        """
        Migrate existing extensions for a tenant.
        
        Args:
            extension_repo: The repository for extensions
            tenant_id: The ID of the tenant, or None to migrate all tenants
            
        Returns:
            A summary of migration results
        """
        if tenant_id:
            # Migrate a specific tenant
            config_service = self.get_config_service(tenant_id)
            return config_service.migrate_extensions(extension_repo)
        else:
            # Migrate all tenants
            results = {}
            
            # Get all active tenants
            tenants = self.tenant_service.get_active_tenants()
            
            for tenant in tenants:
                config_service = self.get_config_service(tenant.tenant_id)
                results[tenant.tenant_id] = config_service.migrate_extensions(extension_repo)
            
            return {
                "status": "completed",
                "tenant_results": results
            } 