import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


class Tenant:
    """
    Model representing a tenant in the system.
    
    A tenant is a logical separation of users and their data.
    Each tenant has its own configuration and can override default settings.
    """
    
    def __init__(
        self,
        tenant_id: str = None,
        name: str = None,
        active: bool = True,
        config: Dict[str, Any] = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        """
        Initialize a tenant with the given attributes.
        
        Args:
            tenant_id: Unique identifier for the tenant. If not provided, a UUID will be generated.
            name: Display name for the tenant.
            active: Whether the tenant is active and can access the system.
            config: Tenant-specific configuration overrides.
            created_at: When the tenant was created.
            updated_at: When the tenant was last updated.
        """
        self.tenant_id = tenant_id or str(uuid.uuid4())
        self.name = name or f"Tenant-{self.tenant_id[:8]}"
        self.active = active
        self.config = config or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tenant to a dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "active": self.active,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tenant':
        """Create a tenant from a dictionary."""
        return cls(
            tenant_id=data.get("tenant_id"),
            name=data.get("name"),
            active=data.get("active", True),
            config=data.get("config", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value for this tenant.
        
        Args:
            key: The configuration key to retrieve.
            default: The default value to return if the key is not found.
            
        Returns:
            The configuration value or the default.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set_config_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value for this tenant.
        
        Args:
            key: The configuration key to set.
            value: The value to set.
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the right nested dictionary
        for i, k in enumerate(keys[:-1]):
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # Set the value at the final key
        config[keys[-1]] = value
        self.updated_at = datetime.now() 