import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading

from ..models.tenant import Tenant

logger = logging.getLogger(__name__)


class TenantRepository:
    """
    Repository for storing and retrieving tenant information.
    
    This implementation uses a file-based storage system for simplicity,
    but could be extended to use a database for production use.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the tenant repository.
        
        Args:
            storage_path: Path to store tenant data. Defaults to 'config/tenants'.
        """
        self.storage_path = storage_path or os.environ.get('TENANT_STORAGE_PATH', 'config/tenants')
        self.tenants_file = os.path.join(self.storage_path, 'tenants.json')
        self.tenants_cache = {}  # In-memory cache of tenants
        self._lock = threading.RLock()  # Thread-safe operations
        
        # Ensure the storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing tenants
        self._load_tenants()
    
    def _load_tenants(self) -> None:
        """Load tenants from the storage file into the cache."""
        if not os.path.exists(self.tenants_file):
            logger.info(f"Tenants file not found at {self.tenants_file}. Creating empty tenants list.")
            self._save_tenants({})
            return
        
        try:
            with open(self.tenants_file, 'r') as f:
                tenant_data = json.load(f)
                
            with self._lock:
                self.tenants_cache = {}
                for tenant_id, data in tenant_data.items():
                    # Convert datetime strings to datetime objects
                    if 'created_at' in data and isinstance(data['created_at'], str):
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if 'updated_at' in data and isinstance(data['updated_at'], str):
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                        
                    self.tenants_cache[tenant_id] = Tenant.from_dict(data)
                
            logger.info(f"Loaded {len(self.tenants_cache)} tenants from {self.tenants_file}")
        except Exception as e:
            logger.error(f"Error loading tenants: {e}")
            # Initialize with empty cache if file is corrupt
            with self._lock:
                self.tenants_cache = {}
    
    def _save_tenants(self, tenants_dict: Dict[str, Dict]) -> None:
        """
        Save tenants to the storage file.
        
        Args:
            tenants_dict: Dictionary of tenant data to save.
        """
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_dict = {}
            for tenant_id, data in tenants_dict.items():
                serializable_data = dict(data)
                if 'created_at' in serializable_data and isinstance(serializable_data['created_at'], datetime):
                    serializable_data['created_at'] = serializable_data['created_at'].isoformat()
                if 'updated_at' in serializable_data and isinstance(serializable_data['updated_at'], datetime):
                    serializable_data['updated_at'] = serializable_data['updated_at'].isoformat()
                serializable_dict[tenant_id] = serializable_data
            
            with open(self.tenants_file, 'w') as f:
                json.dump(serializable_dict, f, indent=2)
                
            logger.info(f"Saved {len(serializable_dict)} tenants to {self.tenants_file}")
        except Exception as e:
            logger.error(f"Error saving tenants: {e}")
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The ID of the tenant to retrieve.
            
        Returns:
            The tenant if found, None otherwise.
        """
        with self._lock:
            return self.tenants_cache.get(tenant_id)
    
    def get_all_tenants(self) -> List[Tenant]:
        """
        Get all tenants.
        
        Returns:
            A list of all tenants.
        """
        with self._lock:
            return list(self.tenants_cache.values())
    
    def get_active_tenants(self) -> List[Tenant]:
        """
        Get all active tenants.
        
        Returns:
            A list of active tenants.
        """
        with self._lock:
            return [t for t in self.tenants_cache.values() if t.active]
    
    def create_tenant(self, tenant: Tenant) -> bool:
        """
        Create a new tenant.
        
        Args:
            tenant: The tenant to create.
            
        Returns:
            True if the tenant was created, False if a tenant with the same ID already exists.
        """
        with self._lock:
            if tenant.tenant_id in self.tenants_cache:
                return False
            
            self.tenants_cache[tenant.tenant_id] = tenant
            
            # Save to storage
            tenants_dict = {t_id: t.to_dict() for t_id, t in self.tenants_cache.items()}
            self._save_tenants(tenants_dict)
            
            # Create tenant-specific directories
            tenant_dir = os.path.join(self.storage_path, tenant.tenant_id)
            os.makedirs(tenant_dir, exist_ok=True)
            os.makedirs(os.path.join(tenant_dir, 'templates'), exist_ok=True)
            
            return True
    
    def update_tenant(self, tenant: Tenant) -> bool:
        """
        Update an existing tenant.
        
        Args:
            tenant: The tenant to update.
            
        Returns:
            True if the tenant was updated, False if the tenant doesn't exist.
        """
        with self._lock:
            if tenant.tenant_id not in self.tenants_cache:
                return False
            
            tenant.updated_at = datetime.now()
            self.tenants_cache[tenant.tenant_id] = tenant
            
            # Save to storage
            tenants_dict = {t_id: t.to_dict() for t_id, t in self.tenants_cache.items()}
            self._save_tenants(tenants_dict)
            
            return True
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        Args:
            tenant_id: The ID of the tenant to delete.
            
        Returns:
            True if the tenant was deleted, False if the tenant doesn't exist.
        """
        with self._lock:
            if tenant_id not in self.tenants_cache:
                return False
            
            del self.tenants_cache[tenant_id]
            
            # Save to storage
            tenants_dict = {t_id: t.to_dict() for t_id, t in self.tenants_cache.items()}
            self._save_tenants(tenants_dict)
            
            return True
    
    def deactivate_tenant(self, tenant_id: str) -> bool:
        """
        Deactivate a tenant.
        
        Args:
            tenant_id: The ID of the tenant to deactivate.
            
        Returns:
            True if the tenant was deactivated, False if the tenant doesn't exist.
        """
        with self._lock:
            tenant = self.tenants_cache.get(tenant_id)
            if not tenant:
                return False
            
            tenant.active = False
            tenant.updated_at = datetime.now()
            
            # Save to storage
            tenants_dict = {t_id: t.to_dict() for t_id, t in self.tenants_cache.items()}
            self._save_tenants(tenants_dict)
            
            return True
    
    def activate_tenant(self, tenant_id: str) -> bool:
        """
        Activate a tenant.
        
        Args:
            tenant_id: The ID of the tenant to activate.
            
        Returns:
            True if the tenant was activated, False if the tenant doesn't exist.
        """
        with self._lock:
            tenant = self.tenants_cache.get(tenant_id)
            if not tenant:
                return False
            
            tenant.active = True
            tenant.updated_at = datetime.now()
            
            # Save to storage
            tenants_dict = {t_id: t.to_dict() for t_id, t in self.tenants_cache.items()}
            self._save_tenants(tenants_dict)
            
            return True
    
    def tenant_exists(self, tenant_id: str) -> bool:
        """
        Check if a tenant exists.
        
        Args:
            tenant_id: The ID of the tenant to check.
            
        Returns:
            True if the tenant exists, False otherwise.
        """
        with self._lock:
            return tenant_id in self.tenants_cache
    
    def is_tenant_active(self, tenant_id: str) -> bool:
        """
        Check if a tenant is active.
        
        Args:
            tenant_id: The ID of the tenant to check.
            
        Returns:
            True if the tenant is active, False otherwise.
        """
        with self._lock:
            tenant = self.tenants_cache.get(tenant_id)
            return tenant is not None and tenant.active 