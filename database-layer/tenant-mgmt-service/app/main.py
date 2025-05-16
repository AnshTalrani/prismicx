"""
Tenant Management Service - Main application entry point

This service manages tenant information and provides database routing
for multi-tenant architecture. It serves as the central registry for
tenant databases and handles tenant-specific database connections.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db, close_db
from .models import Tenant, TenantCreate, TenantUpdate, DatabaseConfig
from .routers import tenant_router, database_router
from .multitenant import TenantManager, get_tenant_manager
from .multitenant.tenant_context import TenantContext, TenantInfo
from .multitenant.tenant_middleware import TenantMiddleware
from .multitenant.database_adapter import get_database_adapter

# Create FastAPI app
app = FastAPI(
    title="Tenant Management Service",
    description="Service for managing multi-tenant databases and tenant information",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup."""
    app.state.db = await init_db()
    app.state.tenant_manager = TenantManager()
    
    # Initialize the database adapter
    app.state.db_adapter = get_database_adapter()
    
    # Add tenant middleware
    app.add_middleware(
        TenantMiddleware,
        tenant_manager=app.state.tenant_manager,
        tenant_header="X-Tenant-ID",
        exclude_paths=[
            "/health", 
            "/", 
            "/api/v1/tenant-connection", 
            "/docs", 
            "/openapi.json",
            "/redoc"
        ]
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    await close_db()

# Include routers
app.include_router(tenant_router.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(database_router.router, prefix="/api/v1/databases", tags=["databases"])

@app.get("/")
async def root():
    """Root endpoint for service health check."""
    return {"status": "healthy", "service": "tenant-management"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}

# Middleware to extract tenant ID
async def get_tenant_id(x_tenant_id: str = Header(None)):
    """Extract tenant ID from request header."""
    if x_tenant_id is None:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return x_tenant_id

@app.get("/api/v1/tenant-connection")
async def get_tenant_connection(
    tenant_id: str = Depends(get_tenant_id),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """
    Get database connection information for a specific tenant.
    
    This endpoint is used by microservices to get connection details for a specific tenant.
    """
    try:
        connection_info = await tenant_manager.get_connection_info(tenant_id)
        return connection_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving tenant connection information: {str(e)}"
        ) 