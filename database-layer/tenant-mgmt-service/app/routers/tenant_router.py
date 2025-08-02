"""
Tenant API router for the Tenant Management Service.

This module provides the API endpoints for managing tenant information,
including CRUD operations and tenant provisioning.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, status
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import Tenant, TenantCreate, TenantUpdate, TenantStatus
from ..services.tenant_service import TenantService

router = APIRouter()

async def get_tenant_service(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Dependency to get the tenant service."""
    return TenantService(db)

@router.post("/", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant: TenantCreate,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """
    Create a new tenant.
    
    Args:
        tenant: The tenant data to create.
        tenant_service: The tenant service.
        
    Returns:
        The created tenant.
    
    Raises:
        HTTPException: If a tenant with the same ID already exists.
    """
    # Check if tenant already exists
    existing_tenant = await tenant_service.get_tenant(tenant.tenant_id)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with ID {tenant.tenant_id} already exists"
        )
    
    # Create tenant
    created_tenant = await tenant_service.create_tenant(tenant)
    return created_tenant

@router.get("/", response_model=List[Tenant])
async def list_tenants(
    status: Optional[TenantStatus] = None,
    region: Optional[str] = None,
    tier: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """
    List tenants with optional filtering.
    
    Args:
        status: Optional filter by tenant status.
        region: Optional filter by tenant region.
        tier: Optional filter by tenant tier.
        skip: Number of tenants to skip.
        limit: Maximum number of tenants to return.
        tenant_service: The tenant service.
        
    Returns:
        List of tenants.
    """
    filters = {}
    if status:
        filters["status"] = status
    if region:
        filters["region"] = region
    if tier:
        filters["tier"] = tier
    
    tenants = await tenant_service.list_tenants(
        filters=filters,
        skip=skip,
        limit=limit
    )
    return tenants

@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """
    Get a tenant by ID.
    
    Args:
        tenant_id: The tenant ID.
        tenant_service: The tenant service.
        
    Returns:
        The tenant.
        
    Raises:
        HTTPException: If the tenant is not found.
    """
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found"
        )
    return tenant

@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """
    Update a tenant.
    
    Args:
        tenant_id: The tenant ID.
        tenant_update: The tenant data to update.
        tenant_service: The tenant service.
        
    Returns:
        The updated tenant.
        
    Raises:
        HTTPException: If the tenant is not found.
    """
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found"
        )
    
    updated_tenant = await tenant_service.update_tenant(tenant_id, tenant_update)
    return updated_tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """
    Delete a tenant.
    
    Args:
        tenant_id: The tenant ID.
        tenant_service: The tenant service.
        
    Raises:
        HTTPException: If the tenant is not found.
    """
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found"
        )
    
    await tenant_service.delete_tenant(tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{tenant_id}/provision", response_model=Tenant)
async def provision_tenant(
    tenant_id: str,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """
    Provision a tenant's database resources.
    
    Args:
        tenant_id: The tenant ID.
        tenant_service: The tenant service.
        
    Returns:
        The provisioned tenant.
        
    Raises:
        HTTPException: If the tenant is not found or already provisioned.
    """
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found"
        )
    
    if tenant["status"] != TenantStatus.PROVISIONING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with ID {tenant_id} is not in provisioning status"
        )
    
    provisioned_tenant = await tenant_service.provision_tenant(tenant_id)
    return provisioned_tenant 