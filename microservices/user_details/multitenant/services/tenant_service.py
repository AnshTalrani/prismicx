import os
import json
import logging
import shutil
from typing import Dict, List, Optional, Any, Tuple

from ..models.tenant import Tenant
from .tenant_repository import TenantRepository

logger = logging.getLogger(__name__)


class TenantService:
    """
    Service for managing tenants in the system.
    
    This service provides a high-level interface for tenant operations,
    including creation, configuration, and database initialization.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the tenant service.
        
        Args:
            storage_path: Path to store tenant data. Defaults to 'config/tenants'.
        """
        self.storage_path = storage_path or os.environ.get('TENANT_STORAGE_PATH', 'config/tenants')
        self.repository = TenantRepository(storage_path)
        self.default_templates_path = os.environ.get('DEFAULT_TEMPLATES_PATH', 'config/templates')
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The ID of the tenant to retrieve.
            
        Returns:
            The tenant if found, None otherwise.
        """
        return self.repository.get_tenant(tenant_id)
    
    def get_all_tenants(self) -> List[Tenant]:
        """
        Get all tenants.
        
        Returns:
            A list of all tenants.
        """
        return self.repository.get_all_tenants()
    
    def get_active_tenants(self) -> List[Tenant]:
        """
        Get all active tenants.
        
        Returns:
            A list of active tenants.
        """
        return self.repository.get_active_tenants()
    
    def create_tenant(self, tenant_id: str, name: str, config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Create a new tenant with all required resources.
        
        Args:
            tenant_id: The ID for the new tenant.
            name: The display name for the tenant.
            config: Optional tenant-specific configuration.
            
        Returns:
            A tuple of (success, message) where success is a boolean and message is a descriptive message.
        """
        # Check if tenant already exists
        if self.repository.tenant_exists(tenant_id):
            return False, f"Tenant with ID '{tenant_id}' already exists"
        
        # Create new tenant
        tenant = Tenant(tenant_id=tenant_id, name=name, config=config or {})
        
        # Save tenant to repository
        success = self.repository.create_tenant(tenant)
        if not success:
            return False, f"Failed to create tenant with ID '{tenant_id}'"
        
        # Create tenant directory structure
        tenant_dir = os.path.join(self.storage_path, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Create templates directory and copy default templates
        templates_dir = os.path.join(tenant_dir, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        self._copy_default_templates(templates_dir)
        
        logger.info(f"Created new tenant: {tenant_id} ({name})")
        return True, f"Successfully created tenant '{tenant_id}'"
    
    def _copy_default_templates(self, tenant_templates_dir: str) -> None:
        """
        Copy default templates to a tenant's templates directory.
        
        Args:
            tenant_templates_dir: The path to the tenant's templates directory.
        """
        if not os.path.exists(self.default_templates_path):
            logger.warning(f"Default templates path not found: {self.default_templates_path}")
            return
        
        try:
            # Copy user_insight_structure.json
            insight_structure_file = os.path.join(self.default_templates_path, 'user_insight_structure.json')
            if os.path.exists(insight_structure_file):
                shutil.copy2(insight_structure_file, tenant_templates_dir)
                logger.info(f"Copied user_insight_structure.json to {tenant_templates_dir}")
            
            # Copy default_topics.json
            default_topics_file = os.path.join(self.default_templates_path, 'default_topics.json')
            if os.path.exists(default_topics_file):
                shutil.copy2(default_topics_file, tenant_templates_dir)
                logger.info(f"Copied default_topics.json to {tenant_templates_dir}")
            
            # Copy extension_types directory
            ext_types_dir = os.path.join(self.default_templates_path, 'extension_types')
            tenant_ext_types_dir = os.path.join(tenant_templates_dir, 'extension_types')
            
            if os.path.exists(ext_types_dir) and os.path.isdir(ext_types_dir):
                os.makedirs(tenant_ext_types_dir, exist_ok=True)
                
                for filename in os.listdir(ext_types_dir):
                    if filename.endswith('.json'):
                        src_file = os.path.join(ext_types_dir, filename)
                        dst_file = os.path.join(tenant_ext_types_dir, filename)
                        shutil.copy2(src_file, dst_file)
                        logger.info(f"Copied extension type {filename} to {tenant_ext_types_dir}")
        except Exception as e:
            logger.error(f"Error copying default templates: {e}")
    
    def update_tenant(self, tenant_id: str, name: str = None, config: Dict[str, Any] = None, active: bool = None) -> Tuple[bool, str]:
        """
        Update an existing tenant.
        
        Args:
            tenant_id: The ID of the tenant to update.
            name: Optional new name for the tenant.
            config: Optional new configuration for the tenant.
            active: Optional new active status for the tenant.
            
        Returns:
            A tuple of (success, message) where success is a boolean and message is a descriptive message.
        """
        # Get the tenant
        tenant = self.repository.get_tenant(tenant_id)
        if not tenant:
            return False, f"Tenant with ID '{tenant_id}' not found"
        
        # Update tenant attributes
        if name is not None:
            tenant.name = name
        
        if config is not None:
            tenant.config = config
        
        if active is not None:
            tenant.active = active
        
        # Save updated tenant
        success = self.repository.update_tenant(tenant)
        if not success:
            return False, f"Failed to update tenant with ID '{tenant_id}'"
        
        logger.info(f"Updated tenant: {tenant_id}")
        return True, f"Successfully updated tenant '{tenant_id}'"
    
    def delete_tenant(self, tenant_id: str) -> Tuple[bool, str]:
        """
        Delete a tenant.
        
        Args:
            tenant_id: The ID of the tenant to delete.
            
        Returns:
            A tuple of (success, message) where success is a boolean and message is a descriptive message.
        """
        # Check if tenant exists
        if not self.repository.tenant_exists(tenant_id):
            return False, f"Tenant with ID '{tenant_id}' not found"
        
        # Delete tenant from repository
        success = self.repository.delete_tenant(tenant_id)
        if not success:
            return False, f"Failed to delete tenant with ID '{tenant_id}'"
        
        # Delete tenant directory (optional - may want to keep for audit purposes)
        tenant_dir = os.path.join(self.storage_path, tenant_id)
        if os.path.exists(tenant_dir) and os.path.isdir(tenant_dir):
            try:
                shutil.rmtree(tenant_dir)
                logger.info(f"Deleted tenant directory: {tenant_dir}")
            except Exception as e:
                logger.error(f"Error deleting tenant directory: {e}")
        
        logger.info(f"Deleted tenant: {tenant_id}")
        return True, f"Successfully deleted tenant '{tenant_id}'"
    
    def get_tenant_config_path(self, tenant_id: str) -> str:
        """
        Get the path to a tenant's configuration directory.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The path to the tenant's configuration directory.
        """
        return os.path.join(self.storage_path, tenant_id)
    
    def get_tenant_templates_path(self, tenant_id: str) -> str:
        """
        Get the path to a tenant's templates directory.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The path to the tenant's templates directory.
        """
        return os.path.join(self.storage_path, tenant_id, 'templates')
    
    def validate_tenant(self, tenant_id: str) -> bool:
        """
        Validate that a tenant exists and is active.
        
        Args:
            tenant_id: The ID of the tenant to validate.
            
        Returns:
            True if the tenant exists and is active, False otherwise.
        """
        return self.repository.is_tenant_active(tenant_id)
    
    def deactivate_tenant(self, tenant_id: str) -> Tuple[bool, str]:
        """
        Deactivate a tenant.
        
        Args:
            tenant_id: The ID of the tenant to deactivate.
            
        Returns:
            A tuple of (success, message) where success is a boolean and message is a descriptive message.
        """
        # Check if tenant exists
        if not self.repository.tenant_exists(tenant_id):
            return False, f"Tenant with ID '{tenant_id}' not found"
        
        # Deactivate tenant
        success = self.repository.deactivate_tenant(tenant_id)
        if not success:
            return False, f"Failed to deactivate tenant with ID '{tenant_id}'"
        
        logger.info(f"Deactivated tenant: {tenant_id}")
        return True, f"Successfully deactivated tenant '{tenant_id}'"
    
    def activate_tenant(self, tenant_id: str) -> Tuple[bool, str]:
        """
        Activate a tenant.
        
        Args:
            tenant_id: The ID of the tenant to activate.
            
        Returns:
            A tuple of (success, message) where success is a boolean and message is a descriptive message.
        """
        # Check if tenant exists
        if not self.repository.tenant_exists(tenant_id):
            return False, f"Tenant with ID '{tenant_id}' not found"
        
        # Activate tenant
        success = self.repository.activate_tenant(tenant_id)
        if not success:
            return False, f"Failed to activate tenant with ID '{tenant_id}'"
        
        logger.info(f"Activated tenant: {tenant_id}")
        return True, f"Successfully activated tenant '{tenant_id}'" 