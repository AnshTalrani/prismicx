"""
API router for data operations.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Path, Query, Body, status
from typing import Dict, List, Any, Optional

from ..services.data_service import (
    data_service,
    DataServiceError,
    DataValidationError,
    DataItemNotFoundError
)
from ..services.management_service import (
    InstanceNotFoundError,
    SystemNotFoundError
)
from ..models.management_system import DataItem, PaginatedResponse
from ..common.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["data"])

@router.get(
    "/tenant/{tenant_id}/systems/{instance_id}/data",
    response_model=PaginatedResponse,
    response_model_exclude_none=True
)
async def get_data_items(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    view_id: Optional[str] = Query(None, description="View ID to use"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    filters: Optional[Dict[str, Any]] = None
):
    """Get data items for a system instance."""
    try:
        return await data_service.get_data_items(
            tenant_id,
            instance_id,
            view_id=view_id,
            filters=filters,
            page=page,
            page_size=page_size
        )
    except InstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System instance {instance_id} not found for tenant {tenant_id}"
        )
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System definition not found for instance {instance_id}"
        )
    except DataServiceError as e:
        logger.error(f"Error retrieving data for system {instance_id} of tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data: {str(e)}"
        )

@router.get(
    "/tenant/{tenant_id}/systems/{instance_id}/data/{item_id}",
    response_model=DataItem,
    response_model_exclude_none=True
)
async def get_data_item(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    item_id: str = Path(..., description="Item ID")
):
    """Get a specific data item."""
    try:
        return await data_service.get_data_item(tenant_id, instance_id, item_id)
    except InstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System instance {instance_id} not found for tenant {tenant_id}"
        )
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System definition not found for instance {instance_id}"
        )
    except DataItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    except DataServiceError as e:
        logger.error(f"Error retrieving data item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data item: {str(e)}"
        )

@router.post(
    "/tenant/{tenant_id}/systems/{instance_id}/data",
    response_model=DataItem,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True
)
async def create_data_item(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    data: Dict[str, Any] = Body(..., description="Item data")
):
    """Create a new data item."""
    try:
        return await data_service.create_data_item(tenant_id, instance_id, data)
    except InstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System instance {instance_id} not found for tenant {tenant_id}"
        )
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System definition not found for instance {instance_id}"
        )
    except DataValidationError as e:
        logger.warning(f"Data validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data validation failed: {str(e)}"
        )
    except DataServiceError as e:
        logger.error(f"Error creating data item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data item: {str(e)}"
        )

@router.put(
    "/tenant/{tenant_id}/systems/{instance_id}/data/{item_id}",
    response_model=DataItem,
    response_model_exclude_none=True
)
async def update_data_item(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    item_id: str = Path(..., description="Item ID"),
    updates: Dict[str, Any] = Body(..., description="Updates to apply")
):
    """Update a data item."""
    try:
        return await data_service.update_data_item(tenant_id, instance_id, item_id, updates)
    except InstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System instance {instance_id} not found for tenant {tenant_id}"
        )
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System definition not found for instance {instance_id}"
        )
    except DataItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    except DataValidationError as e:
        logger.warning(f"Data validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data validation failed: {str(e)}"
        )
    except DataServiceError as e:
        logger.error(f"Error updating data item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update data item: {str(e)}"
        )

@router.delete(
    "/tenant/{tenant_id}/systems/{instance_id}/data/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_data_item(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    item_id: str = Path(..., description="Item ID")
):
    """Delete a data item."""
    try:
        await data_service.delete_data_item(tenant_id, instance_id, item_id)
    except InstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System instance {instance_id} not found for tenant {tenant_id}"
        )
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System definition not found for instance {instance_id}"
        )
    except DataItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    except DataServiceError as e:
        logger.error(f"Error deleting data item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data item: {str(e)}"
        )

@router.post(
    "/tenant/{tenant_id}/systems/{instance_id}/data/bulk",
    response_model=Dict[str, Any]
)
async def bulk_import_data(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    items: List[Dict[str, Any]] = Body(..., description="Data items to import")
):
    """Bulk import data items."""
    try:
        return await data_service.bulk_import_data(tenant_id, instance_id, items)
    except InstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System instance {instance_id} not found for tenant {tenant_id}"
        )
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System definition not found for instance {instance_id}"
        )
    except DataValidationError as e:
        logger.warning(f"Data validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data validation failed: {str(e)}"
        )
    except DataServiceError as e:
        logger.error(f"Error bulk importing data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk import data: {str(e)}"
        ) 