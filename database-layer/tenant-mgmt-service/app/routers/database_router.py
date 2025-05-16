"""
Database router for the Tenant Management Service.

This module provides API endpoints for managing tenant databases, including
database provisioning, status monitoring, and tenant-to-database mapping.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import TenantDatabase, TenantDatabaseCreate, TenantDatabaseUpdate, DatabaseStatus, DatabaseType
from ..services.database_service import DatabaseService

router = APIRouter()

async def get_database_service(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Dependency to get the database service."""
    return DatabaseService(db)

@router.post("/", response_model=TenantDatabase, status_code=status.HTTP_201_CREATED)
async def create_database(
    database: TenantDatabaseCreate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Create a new tenant database.
    
    Args:
        database: The database configuration to create.
        db_service: The database service.
        
    Returns:
        The created database.
        
    Raises:
        HTTPException: If a database with the same name already exists.
    """
    # Check if database already exists
    existing_db = await db_service.get_database(database.database_name)
    if existing_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database with name {database.database_name} already exists"
        )
    
    # Create database
    created_db = await db_service.create_database(database)
    return created_db

@router.get("/", response_model=List[TenantDatabase])
async def list_databases(
    type: Optional[DatabaseType] = None,
    status: Optional[DatabaseStatus] = None,
    region: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    List tenant databases with optional filtering.
    
    Args:
        type: Optional filter by database type.
        status: Optional filter by database status.
        region: Optional filter by database region.
        skip: Number of databases to skip.
        limit: Maximum number of databases to return.
        db_service: The database service.
        
    Returns:
        List of databases.
    """
    filters = {}
    if type:
        filters["type"] = type
    if status:
        filters["status"] = status
    if region:
        filters["region"] = region
    
    databases = await db_service.list_databases(
        filters=filters,
        skip=skip,
        limit=limit
    )
    return databases

@router.get("/{database_name}", response_model=TenantDatabase)
async def get_database(
    database_name: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Get a database by name.
    
    Args:
        database_name: The database name.
        db_service: The database service.
        
    Returns:
        The database.
        
    Raises:
        HTTPException: If the database is not found.
    """
    database = await db_service.get_database(database_name)
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database with name {database_name} not found"
        )
    return database

@router.put("/{database_name}", response_model=TenantDatabase)
async def update_database(
    database_name: str,
    database_update: TenantDatabaseUpdate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Update a database.
    
    Args:
        database_name: The database name.
        database_update: The database data to update.
        db_service: The database service.
        
    Returns:
        The updated database.
        
    Raises:
        HTTPException: If the database is not found.
    """
    database = await db_service.get_database(database_name)
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database with name {database_name} not found"
        )
    
    updated_database = await db_service.update_database(database_name, database_update)
    return updated_database

@router.delete("/{database_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database(
    database_name: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Mark a database for decommissioning.
    
    Args:
        database_name: The database name.
        db_service: The database service.
        
    Raises:
        HTTPException: If the database is not found or has active tenants.
    """
    database = await db_service.get_database(database_name)
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database with name {database_name} not found"
        )
    
    if database["tenants"] and len(database["tenants"]) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database {database_name} still has active tenants"
        )
    
    await db_service.mark_database_for_decommissioning(database_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{database_name}/tenants/{tenant_id}", status_code=status.HTTP_200_OK)
async def add_tenant_to_database(
    database_name: str,
    tenant_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Add a tenant to a database.
    
    Args:
        database_name: The database name.
        tenant_id: The tenant ID to add.
        db_service: The database service.
        
    Raises:
        HTTPException: If the database is not found or the tenant is already assigned.
    """
    database = await db_service.get_database(database_name)
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database with name {database_name} not found"
        )
    
    if tenant_id in database["tenants"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant {tenant_id} is already assigned to database {database_name}"
        )
    
    await db_service.add_tenant_to_database(database_name, tenant_id)
    return {"message": f"Tenant {tenant_id} added to database {database_name}"}

@router.delete("/{database_name}/tenants/{tenant_id}", status_code=status.HTTP_200_OK)
async def remove_tenant_from_database(
    database_name: str,
    tenant_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Remove a tenant from a database.
    
    Args:
        database_name: The database name.
        tenant_id: The tenant ID to remove.
        db_service: The database service.
        
    Raises:
        HTTPException: If the database is not found or the tenant is not assigned.
    """
    database = await db_service.get_database(database_name)
    if not database:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database with name {database_name} not found"
        )
    
    if tenant_id not in database["tenants"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} is not assigned to database {database_name}"
        )
    
    await db_service.remove_tenant_from_database(database_name, tenant_id)
    return {"message": f"Tenant {tenant_id} removed from database {database_name}"} 