"""
Tenant Configuration Module

This module provides utilities for managing tenant-specific configuration settings.
It allows different tenants to have their own configuration values.
"""

import logging
import os
from typing import Optional, Dict, Any, List, Union, TypeVar, Generic, Type, cast
from pydantic import BaseModel, Field, create_model

from .tenant_context import TenantContext

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class TenantConfig(Generic[T]):
    """
    Manager for tenant-specific configuration.
    
    This class allows different tenants to have their own configuration values,
    while maintaining defaults for unspecified settings.
    """
    
    def __init__(
        self,
        config_class: Type[T],
        default_config: Optional[T] = None,
        tenant_configs: Optional[Dict[str, T]] = None
    ):
        """
        Initialize the tenant configuration manager.
        
        Args:
            config_class: The configuration class (must be a Pydantic model).
            default_config: The default configuration for all tenants.
            tenant_configs: A dictionary of tenant-specific configurations.
        """
        self.config_class = config_class
        self.default_config = default_config or config_class()
        self.tenant_configs = tenant_configs or {}
    
    def get_config(self, tenant_id: Optional[str] = None) -> T:
        """
        Get configuration for a specific tenant.
        
        If no tenant ID is provided, the current tenant from context is used.
        If no tenant-specific configuration exists, the default is returned.
        
        Args:
            tenant_id: The tenant ID to get configuration for.
            
        Returns:
            The tenant-specific or default configuration.
        """
        # If no tenant ID provided, try to get from context
        if tenant_id is None:
            tenant_id = TenantContext.get_current_tenant()
            
        # If tenant ID is provided or found in context, try to get tenant config
        if tenant_id and tenant_id in self.tenant_configs:
            return self.tenant_configs[tenant_id]
            
        # Return default config
        return self.default_config
    
    def set_config(self, config: T, tenant_id: Optional[str] = None) -> None:
        """
        Set configuration for a specific tenant.
        
        If no tenant ID is provided, the current tenant from context is used.
        If that is also not available, sets the default configuration.
        
        Args:
            config: The configuration to set.
            tenant_id: The tenant ID to set configuration for.
        """
        # If no tenant ID provided, try to get from context
        if tenant_id is None:
            tenant_id = TenantContext.get_current_tenant()
            
        # If tenant ID is provided or found in context, set tenant config
        if tenant_id:
            self.tenant_configs[tenant_id] = config
        else:
            # Set default config
            self.default_config = config
    
    def update_config(
        self, config_updates: Dict[str, Any], tenant_id: Optional[str] = None
    ) -> None:
        """
        Update configuration for a specific tenant.
        
        If no tenant ID is provided, the current tenant from context is used.
        If that is also not available, updates the default configuration.
        
        Args:
            config_updates: The configuration updates to apply.
            tenant_id: The tenant ID to update configuration for.
        """
        # Get current config
        current_config = self.get_config(tenant_id)
        
        # Create updated config
        updated_config = current_config.copy(update=config_updates)
        
        # Set updated config
        self.set_config(updated_config, tenant_id)
    
    def reset_config(self, tenant_id: str) -> None:
        """
        Reset configuration for a specific tenant to the default.
        
        Args:
            tenant_id: The tenant ID to reset configuration for.
        """
        if tenant_id in self.tenant_configs:
            del self.tenant_configs[tenant_id]


class CommunicationSettings(BaseModel):
    """Base communication settings for tenants."""
    
    # Email settings
    email_from: str = Field(
        "noreply@example.com", 
        description="Default sender email address"
    )
    email_reply_to: Optional[str] = Field(
        None, 
        description="Reply-to email address"
    )
    email_signature: str = Field(
        "Best regards,\nThe Team", 
        description="Email signature"
    )
    
    # SMS settings
    sms_sender_id: str = Field(
        "Company", 
        description="SMS sender ID"
    )
    sms_template_prefix: str = Field(
        "", 
        description="Prefix for SMS templates"
    )
    
    # Rate limiting
    rate_limit_emails: int = Field(
        100, 
        description="Maximum emails per hour"
    )
    rate_limit_sms: int = Field(
        50, 
        description="Maximum SMS per hour"
    )
    
    # Feature flags
    enable_email: bool = Field(
        True, 
        description="Enable email communications"
    )
    enable_sms: bool = Field(
        True, 
        description="Enable SMS communications"
    )
    enable_push: bool = Field(
        True, 
        description="Enable push notifications"
    )
    enable_chat: bool = Field(
        True, 
        description="Enable chat communications"
    )


# Global configuration manager
_comm_config: Optional[TenantConfig[CommunicationSettings]] = None


def get_communication_config() -> TenantConfig[CommunicationSettings]:
    """
    Get the global communication configuration manager.
    
    Returns:
        The communication configuration manager.
    """
    global _comm_config
    if _comm_config is None:
        # Create default configuration
        default_config = CommunicationSettings(
            email_from=os.environ.get("DEFAULT_EMAIL_FROM", "noreply@example.com"),
            sms_sender_id=os.environ.get("DEFAULT_SMS_SENDER_ID", "Company")
        )
        
        _comm_config = TenantConfig(
            config_class=CommunicationSettings,
            default_config=default_config
        )
        
    return _comm_config 