"""
API router for configuration endpoints.

This module provides API endpoints for managing tenant configurations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request, Body
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.config_models import (
    TenantConfig, 
    ConfigSchema, 
    ConfigRequest, 
    ConfigResponse,
    ConfigSchemaRequest,
    UserPreference, 
    FeatureFrequencyGroup
)

config_router = APIRouter(tags=["Configuration"])

# Tenant Configuration Endpoints

@config_router.get("/tenants/{tenant_id}/configs/{config_key}", response_model=ConfigResponse)
async def get_tenant_config(
    request: Request,
    tenant_id: str = Path(..., description="Tenant ID"),
    config_key: str = Path(..., description="Configuration key")
):
    """
    Get configuration for a specific tenant.
    
    Args:
        tenant_id: Tenant ID
        config_key: Configuration key
        
    Returns:
        Configuration value for the specified tenant and key
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_config(tenant_id, config_key)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Configuration not found for tenant {tenant_id} and key {config_key}")
        
    return result

@config_router.get("/configs/{config_key}/all-tenants")
async def get_config_for_all_tenants(
    request: Request,
    config_key: str = Path(..., description="Configuration key")
):
    """
    Get configuration for all tenants at once.
    
    This optimized endpoint returns a mapping of tenant_id -> config_value
    for the requested configuration key across all tenants.
    
    Args:
        config_key: Configuration key
        
    Returns:
        Dictionary mapping tenant IDs to their configuration values
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_config_for_all_tenants(config_key)
    return result

@config_router.put("/tenants/{tenant_id}/configs/{config_key}", response_model=ConfigResponse)
async def set_tenant_config(
    request: Request,
    config_request: ConfigRequest,
    tenant_id: str = Path(..., description="Tenant ID"),
    config_key: str = Path(..., description="Configuration key"),
    user_id: Optional[str] = Query(None, description="User ID making the change")
):
    """
    Set or update configuration for a specific tenant.
    
    Args:
        tenant_id: Tenant ID
        config_key: Configuration key
        config_request: Configuration value and metadata
        user_id: Optional user ID making the change
        
    Returns:
        Updated configuration
    """
    config_repo = request.app.state.config_repo
    
    result = await config_repo.set_config(
        tenant_id=tenant_id,
        config_key=config_key,
        config_value=config_request.config_value,
        metadata=config_request.metadata,
        created_by=user_id,
        updated_by=user_id
    )
            
    if not result:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update configuration for tenant {tenant_id} and key {config_key}"
        )
    
    return result

@config_router.delete("/tenants/{tenant_id}/configs/{config_key}")
async def delete_tenant_config(
    request: Request,
    tenant_id: str = Path(..., description="Tenant ID"),
    config_key: str = Path(..., description="Configuration key")
):
    """
    Delete configuration for a specific tenant.
    
    Args:
        tenant_id: Tenant ID
        config_key: Configuration key
        
    Returns:
        Deletion status
    """
    config_repo = request.app.state.config_repo
    
    success = await config_repo.delete_config(tenant_id, config_key)
        
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Configuration not found for tenant {tenant_id} and key {config_key}"
        )
            
        return {"status": "deleted", "tenant_id": tenant_id, "config_key": config_key}

@config_router.get("/tenants/{tenant_id}/configs", response_model=List[ConfigResponse])
async def get_tenant_configs(
    request: Request,
    tenant_id: str = Path(..., description="Tenant ID"),
    prefix: Optional[str] = Query(None, description="Configuration key prefix filter"),
    limit: int = Query(100, description="Maximum number of configurations to return")
):
    """
    Get all configurations for a specific tenant.
    
    Args:
        tenant_id: Tenant ID
        prefix: Optional prefix to filter configuration keys
        limit: Maximum number of configurations to return
        
    Returns:
        List of configurations for the tenant
    """
    config_repo = request.app.state.config_repo
    
    if prefix:
        result = await config_repo.get_configs_by_prefix(tenant_id, prefix, limit)
    else:
        result = await config_repo.get_all_tenant_configs(tenant_id, limit)
    
    return result

# Configuration Schema Endpoints

@config_router.get("/schemas/{key}", response_model=ConfigSchema)
async def get_config_schema(
    request: Request,
    key: str = Path(..., description="Schema key")
):
    """
    Get configuration schema for a specific key.
    
    Args:
        key: Schema key
        
    Returns:
        Configuration schema
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_config_schema(key)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Configuration schema not found for key {key}")
    
    return result

@config_router.put("/schemas/{key}", response_model=ConfigSchema)
async def set_config_schema(
    request: Request,
    schema_request: ConfigSchemaRequest,
    key: str = Path(..., description="Schema key")
):
    """
    Set or update configuration schema.
    
    Args:
        key: Schema key
        schema_request: Schema definition
        
    Returns:
        Updated configuration schema
    """
    config_repo = request.app.state.config_repo
    
    result = await config_repo.set_config_schema(
        key=key,
        schema=schema_request.schema,
        metadata=schema_request.metadata,
        required=schema_request.required if schema_request.required is not None else False,
        default_value=schema_request.default_value
    )
    
    if not result:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration schema for key {key}")
    
    return result

@config_router.delete("/schemas/{key}")
async def delete_config_schema(
    request: Request,
    key: str = Path(..., description="Schema key")
):
    """
    Delete configuration schema.
    
    Args:
        key: Schema key
        
    Returns:
        Deletion status
    """
    config_repo = request.app.state.config_repo
    
    success = await config_repo.delete_config_schema(key)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Configuration schema not found for key {key}")
    
    return {"status": "deleted", "key": key}

@config_router.get("/schemas", response_model=List[ConfigSchema])
async def get_all_config_schemas(
    request: Request,
    limit: int = Query(100, description="Maximum number of schemas to return")
):
    """
    Get all configuration schemas.
    
    Args:
        limit: Maximum number of schemas to return
        
    Returns:
        List of configuration schemas
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_all_config_schemas(limit)
    return result

# User Preference Endpoints

@config_router.get("/users/{user_id}/preferences/{feature_type}", response_model=UserPreference)
async def get_user_preferences(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    feature_type: str = Path(..., description="Feature type")
):
    """
    Get user preferences for a specific feature type.
    
    Args:
        user_id: User ID
        feature_type: Feature type
        
    Returns:
        User preferences
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_user_preference(user_id, feature_type)
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail=f"User preference not found for user {user_id} and feature {feature_type}"
        )
    
    return result

@config_router.put("/users/{user_id}/preferences/{feature_type}", response_model=UserPreference)
async def set_user_preferences(
    request: Request,
    preferences: Dict[str, Any] = Body(..., description="User preferences"),
    user_id: str = Path(..., description="User ID"),
    feature_type: str = Path(..., description="Feature type")
):
    """
    Set or update user preferences for a specific feature type.
    
    Args:
        user_id: User ID
        feature_type: Feature type
        preferences: User preferences
        
    Returns:
        Updated user preferences
    """
    config_repo = request.app.state.config_repo
    
    result = await config_repo.set_user_preference(
        user_id=user_id,
        feature_type=feature_type,
        preferences=preferences
    )
    
    if not result:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update user preference for user {user_id} and feature {feature_type}"
        )
    
    return result

@config_router.delete("/users/{user_id}/preferences/{feature_type}")
async def delete_user_preferences(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    feature_type: str = Path(..., description="Feature type")
):
    """
    Delete user preferences for a specific feature type.
    
    Args:
        user_id: User ID
        feature_type: Feature type
        
    Returns:
        Deletion status
    """
    config_repo = request.app.state.config_repo
    
    success = await config_repo.delete_user_preference(user_id, feature_type)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"User preference not found for user {user_id} and feature {feature_type}"
        )
    
    return {"status": "deleted", "user_id": user_id, "feature_type": feature_type}

@config_router.get("/users/{user_id}/preferences", response_model=List[UserPreference])
async def get_all_user_preferences(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(100, description="Maximum number of preferences to return")
):
    """
    Get all preferences for a specific user.
    
    Args:
        user_id: User ID
        limit: Maximum number of preferences to return
        
    Returns:
        List of user preferences
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_all_user_preferences(user_id, limit)
    return result

# Feature frequency group endpoints

@config_router.get("/feature-types")
async def get_feature_types(request: Request):
    """
    Get all available feature types.
    
    Returns:
        List of feature types
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_feature_types()
    return {"feature_types": result}

@config_router.get("/features/{feature_type}/frequency-groups")
async def get_frequency_groups(
    request: Request,
    feature_type: str = Path(..., description="Feature type")
):
    """
    Get frequency groups for a specific feature type.
    
    Args:
        feature_type: Feature type
        
    Returns:
        Dictionary of frequency -> time_keys
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_frequency_groups(feature_type)
    return result

@config_router.get("/features/{feature_type}/frequency-groups/{frequency}/{time_key}/tenants")
async def get_frequency_group_tenants(
    request: Request,
    feature_type: str = Path(..., description="Feature type"),
    frequency: str = Path(..., description="Frequency (daily, weekly, monthly)"),
    time_key: str = Path(..., description="Time key")
):
    """
    Get tenants in a specific frequency group.
    
    Args:
        feature_type: Feature type
        frequency: Frequency (daily, weekly, monthly)
        time_key: Time key
        
    Returns:
        List of tenant IDs
    """
    config_repo = request.app.state.config_repo
    result = await config_repo.get_frequency_group_tenants(feature_type, frequency, time_key)
    return {"tenant_ids": result}

@config_router.put("/features/{feature_type}/frequency-groups/{frequency}/{time_key}")
async def set_frequency_group(
    request: Request,
    tenant_ids: List[str] = Body(..., description="List of tenant IDs"),
    feature_type: str = Path(..., description="Feature type"),
    frequency: str = Path(..., description="Frequency (daily, weekly, monthly)"),
    time_key: str = Path(..., description="Time key")
):
    """
    Set or update a frequency group.
    
    Args:
        feature_type: Feature type
        frequency: Frequency (daily, weekly, monthly)
        time_key: Time key
        tenant_ids: List of tenant IDs
        
    Returns:
        Success status
    """
    config_repo = request.app.state.config_repo
    success = await config_repo.set_frequency_group(feature_type, frequency, time_key, tenant_ids)
    
    if not success:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update frequency group {feature_type}/{frequency}/{time_key}"
        )
    
    return {"status": "updated", "feature_type": feature_type, "frequency": frequency, "time_key": time_key}

@config_router.post("/features/{feature_type}/frequency-groups/{frequency}/{time_key}/tenants/{tenant_id}")
async def add_tenant_to_frequency_group(
    request: Request,
    feature_type: str = Path(..., description="Feature type"),
    frequency: str = Path(..., description="Frequency (daily, weekly, monthly)"),
    time_key: str = Path(..., description="Time key"),
    tenant_id: str = Path(..., description="Tenant ID")
):
    """
    Add a tenant to a frequency group.
    
    Args:
        feature_type: Feature type
        frequency: Frequency (daily, weekly, monthly)
        time_key: Time key
        tenant_id: Tenant ID
        
    Returns:
        Success status
    """
    config_repo = request.app.state.config_repo
    success = await config_repo.add_tenant_to_frequency_group(feature_type, frequency, time_key, tenant_id)
    
    if not success:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to add tenant {tenant_id} to frequency group {feature_type}/{frequency}/{time_key}"
        )
    
    return {
        "status": "added", 
        "feature_type": feature_type, 
        "frequency": frequency, 
        "time_key": time_key, 
        "tenant_id": tenant_id
    }

@config_router.delete("/features/{feature_type}/frequency-groups/{frequency}/{time_key}/tenants/{tenant_id}")
async def remove_tenant_from_frequency_group(
    request: Request,
    feature_type: str = Path(..., description="Feature type"),
    frequency: str = Path(..., description="Frequency (daily, weekly, monthly)"),
    time_key: str = Path(..., description="Time key"),
    tenant_id: str = Path(..., description="Tenant ID")
):
    """
    Remove a tenant from a frequency group.
    
    Args:
        feature_type: Feature type
        frequency: Frequency (daily, weekly, monthly)
        time_key: Time key
        tenant_id: Tenant ID
        
    Returns:
        Success status
    """
    config_repo = request.app.state.config_repo
    success = await config_repo.remove_tenant_from_frequency_group(feature_type, frequency, time_key, tenant_id)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Tenant {tenant_id} not found in frequency group {feature_type}/{frequency}/{time_key}"
        )
    
    return {
        "status": "removed", 
        "feature_type": feature_type, 
        "frequency": frequency, 
        "time_key": time_key, 
        "tenant_id": tenant_id
    }

@config_router.delete("/features/{feature_type}/frequency-groups/{frequency}/{time_key}")
async def delete_frequency_group(
    request: Request,
    feature_type: str = Path(..., description="Feature type"),
    frequency: str = Path(..., description="Frequency (daily, weekly, monthly)"),
    time_key: str = Path(..., description="Time key")
):
    """
    Delete a frequency group.
    
    Args:
        feature_type: Feature type
        frequency: Frequency (daily, weekly, monthly)
        time_key: Time key
        
    Returns:
        Success status
    """
    config_repo = request.app.state.config_repo
    success = await config_repo.delete_frequency_group(feature_type, frequency, time_key)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Frequency group {feature_type}/{frequency}/{time_key} not found"
        )
    
    return {"status": "deleted", "feature_type": feature_type, "frequency": frequency, "time_key": time_key}

@config_router.get("/users/{user_id}/tenant")
async def get_user_tenant(
    request: Request,
    user_id: str = Path(..., description="User ID")
):
    """
    Get tenant for a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        Tenant ID
    """
    # Implement user tenant mapping...
    # This would typically involve a call to the user service
    # or a lookup in a tenant mapping table
    
    # For now, we'll return a placeholder
    raise HTTPException(status_code=501, detail="Not implemented yet") 