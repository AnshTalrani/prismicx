"""
Configuration service router.

This module provides REST API endpoints for managing tenant configurations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..plugins.config_service import ConfigServicePlugin
from ..dependencies import get_plugin_manager
from ..common.auth import oauth2_scheme, get_current_user

router = APIRouter(prefix="/config", tags=["configuration"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ConfigResponse(BaseModel):
    """Configuration response model."""
    tenant_id: str
    config_key: str
    config_value: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConfigRequest(BaseModel):
    """Configuration request model."""
    config_value: Dict[str, Any]

class ConfigSchemaRequest(BaseModel):
    """Configuration schema request model."""
    key: str = Field(..., description="Configuration key")
    schema: Dict[str, Any] = Field(..., description="JSON schema for the configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    required: bool = Field(default=False, description="Whether this config is required")
    default_value: Optional[Dict[str, Any]] = Field(None, description="Default value")

@router.get(
    "/tenants/{tenant_id}/configs/{config_key}",
    response_model=Optional[ConfigResponse]
)
async def get_config(
    tenant_id: str,
    config_key: str,
    token: str = Depends(oauth2_scheme),
    plugin_manager = Depends(get_plugin_manager)
):
    """Get tenant-specific configuration."""
    config_service: ConfigServicePlugin = plugin_manager.get_plugin("config_service")
    if not config_service:
        raise HTTPException(status_code=503, detail="Configuration service unavailable")
        
    config = await config_service.get_tenant_config(tenant_id, config_key)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    return ConfigResponse(
        tenant_id=tenant_id,
        config_key=config_key,
        config_value=config,
        metadata={}
    )

@router.put("/tenants/{tenant_id}/configs/{config_key}")
async def set_config(
    tenant_id: str,
    config_key: str,
    config_request: ConfigRequest,
    token: str = Depends(oauth2_scheme),
    plugin_manager = Depends(get_plugin_manager)
):
    """Set tenant-specific configuration."""
    config_service: ConfigServicePlugin = plugin_manager.get_plugin("config_service")
    if not config_service:
        raise HTTPException(status_code=503, detail="Configuration service unavailable")
        
    # Extract user_id from token (stub implementation)
    user_id = token.split("-")[0] if token else "anonymous"
        
    success = await config_service.set_tenant_config(
        tenant_id,
        config_key,
        config_request.config_value,
        user_id
    )
        
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set configuration")
        
    return {"status": "success"}

@router.get("/tenants/{tenant_id}/configs", response_model=List[ConfigResponse])
async def list_configs(
    tenant_id: str,
    token: str = Depends(oauth2_scheme),
    plugin_manager = Depends(get_plugin_manager)
):
    """List all configurations for a tenant."""
    config_service: ConfigServicePlugin = plugin_manager.get_plugin("config_service")
    if not config_service:
        raise HTTPException(status_code=503, detail="Configuration service unavailable")
        
    configs = await config_service.get_tenant_configs(tenant_id)
    return [
        ConfigResponse(
            tenant_id=config["tenant_id"],
            config_key=config["config_key"],
            config_value=config["config_value"],
            metadata=config.get("metadata", {})
        )
        for config in configs
    ]

@router.post("/schemas")
async def register_schema(
    schema_request: ConfigSchemaRequest,
    token: str = Depends(oauth2_scheme),
    plugin_manager = Depends(get_plugin_manager)
):
    """Register a new configuration schema."""
    config_service: ConfigServicePlugin = plugin_manager.get_plugin("config_service")
    if not config_service:
        raise HTTPException(status_code=503, detail="Configuration service unavailable")
        
    # Extract user_id from token (stub implementation)
    user_id = token.split("-")[0] if token else "anonymous"
        
    success = await config_service.register_config_schema(
        schema_request.key,
        schema_request.schema,
        schema_request.metadata,
        schema_request.required,
        schema_request.default_value
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to register schema")
        
    return {"status": "success"}

@router.get("/configs/{config_key}/all-tenants", response_model=List[ConfigResponse])
async def get_config_for_all_tenants(
    config_key: str,
    token: str = Depends(oauth2_scheme),
    plugin_manager = Depends(get_plugin_manager)
):
    """
    Get a specific configuration for all tenants.
    
    This is an admin-level operation that retrieves a specific configuration
    across all tenants in the system.
    
    Args:
        config_key: The configuration key to retrieve
        
    Returns:
        List of configuration responses with tenant IDs and config values
    """
    # Verify admin permissions
    user = get_current_user(token)
    if not user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Administrator privileges required for cross-tenant operations"
        )
        
    config_service: ConfigServicePlugin = plugin_manager.get_plugin("config_service")
    if not config_service:
        raise HTTPException(status_code=503, detail="Configuration service unavailable")
        
    configs = await config_service.get_config_for_all_tenants(config_key)
    
    return [
        ConfigResponse(
            tenant_id=config["tenant_id"],
            config_key=config_key,
            config_value=config["config_value"],
            metadata=config.get("metadata", {})
        )
        for config in configs
    ] 