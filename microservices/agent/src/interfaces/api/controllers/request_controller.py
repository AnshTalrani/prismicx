"""Controller for handling API requests."""
from typing import Dict, Any, List, Optional
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status

from src.interfaces.api.schemas.request_schemas import RequestSchema, BatchRequestSchema
from src.interfaces.api.schemas.response_schemas import ResponseSchema, BatchResponseSchema, ResponseStatus, ErrorSchema
from src.application.interfaces.request_service import IRequestService
from src.domain.exceptions.service_exceptions import ServiceError, ValidationError, ResourceNotFoundError
from src.infrastructure.config.feature_flags import IFeatureFlagManager
# Import the ID utilities
from src.utils.id_utils import generate_request_id, generate_batch_id

logger = logging.getLogger(__name__)

class RequestController:
    """Controller for handling request endpoints."""

    def __init__(self, 
                 request_service: IRequestService,
                 feature_flags: IFeatureFlagManager):
        """
        Initialize the request controller.
        
        Args:
            request_service: Service for handling requests
            feature_flags: Feature flag manager for toggling functionality
        """
        self.request_service = request_service
        self.feature_flags = feature_flags
        self.router = APIRouter(prefix="/requests", tags=["requests"])
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register all routes for the request controller."""
        self.router.post("/process", response_model=ResponseSchema)(self.process_request)
        self.router.post("/batch", response_model=BatchResponseSchema)(self.process_batch)
        
        # Register async endpoints if feature flag is enabled
        if self.feature_flags.is_enabled("async_processing"):
            self.router.post("/async/process", response_model=ResponseSchema)(self.process_request_async)
            self.router.post("/async/batch", response_model=BatchResponseSchema)(self.process_batch_async)
    
    async def process_request(self, request: RequestSchema) -> ResponseSchema:
        """
        Process a single request.
        
        Args:
            request: Request data
        
        Returns:
            Response with processing results
        
        Raises:
            HTTPException: If processing fails
        """
        try:
            # Generate a standardized request ID using our ID utilities
            request_id = generate_request_id(source="api")
            
            logger.info(f"Processing request {request_id}")
            result = await self.request_service.process_request(
                text=request.text,
                purpose_id=request.purpose_id,
                user_id=request.user_id,
                data=request.data,
                metadata=request.metadata,
                request_id=request_id
            )
            
            return ResponseSchema(
                status=ResponseStatus.SUCCESS,
                message="Request processed successfully",
                data=result,
                request_id=request_id
            )
            
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return ResponseSchema(
                status=ResponseStatus.FAILURE,
                message="Request validation failed",
                error=ErrorSchema(
                    error_type="VALIDATION_ERROR",
                    message=str(e),
                    details=getattr(e, "details", None)
                ),
                request_id=request_id if 'request_id' in locals() else None
            )
            
        except ResourceNotFoundError as e:
            logger.warning(f"Resource not found: {str(e)}")
            return ResponseSchema(
                status=ResponseStatus.FAILURE,
                message="Required resource not found",
                error=ErrorSchema(
                    error_type="RESOURCE_NOT_FOUND",
                    message=str(e),
                    details=getattr(e, "details", None)
                ),
                request_id=request_id if 'request_id' in locals() else None
            )
            
        except ServiceError as e:
            logger.error(f"Service error: {str(e)}")
            return ResponseSchema(
                status=ResponseStatus.FAILURE,
                message="Error processing request",
                error=ErrorSchema(
                    error_type="SERVICE_ERROR",
                    message=str(e),
                    details=getattr(e, "details", None)
                ),
                request_id=request_id if 'request_id' in locals() else None
            )
            
        except Exception as e:
            logger.exception(f"Unexpected error: {str(e)}")
            return ResponseSchema(
                status=ResponseStatus.FAILURE,
                message="An unexpected error occurred",
                error=ErrorSchema(
                    error_type="INTERNAL_ERROR",
                    message="An internal error occurred",
                    details={"original_error": str(e)}
                ),
                request_id=request_id if 'request_id' in locals() else None
            )
    
    async def process_request_async(self, 
                                   request: RequestSchema, 
                                   background_tasks: BackgroundTasks) -> ResponseSchema:
        """
        Process a request asynchronously.
        
        Args:
            request: Request data
            background_tasks: FastAPI background tasks handler
        
        Returns:
            Response acknowledging request acceptance
        """
        # Generate a standardized request ID for async processing
        request_id = generate_request_id(source="api_async")
        
        # Add to background tasks
        background_tasks.add_task(
            self._process_request_background,
            request,
            request_id
        )
        
        return ResponseSchema(
            status=ResponseStatus.PENDING,
            message="Request accepted for processing",
            data={"request_id": request_id},
            request_id=request_id
        )
    
    async def _process_request_background(self, request: RequestSchema, request_id: str) -> None:
        """
        Process a request in the background.
        
        Args:
            request: Request data
            request_id: Unique identifier for the request
        """
        try:
            await self.request_service.process_request(
                text=request.text,
                purpose_id=request.purpose_id,
                user_id=request.user_id,
                data=request.data,
                metadata=request.metadata,
                request_id=request_id
            )
            logger.info(f"Background processing of request {request_id} completed successfully")
            
        except Exception as e:
            logger.exception(f"Error in background processing of request {request_id}: {str(e)}")
    
    async def process_batch(self, batch: BatchRequestSchema) -> BatchResponseSchema:
        """
        Process a batch of requests.
        
        Args:
            batch: Batch request data
        
        Returns:
            Batch response with processing results
        """
        # Generate a standardized batch ID
        batch_id = generate_batch_id(source="api")
        logger.info(f"Processing batch {batch_id} with {len(batch.items)} items")
        
        results = []
        errors = []
        success_count = 0
        error_count = 0
        
        for item in batch.items:
            try:
                result = await self.request_service.process_batch_item(
                    batch_id=batch_id,
                    template_id=batch.template_id,
                    item_id=item.item_id,
                    data=item.data,
                    metadata=item.metadata,
                    batch_metadata=batch.batch_metadata,
                    source=batch.source
                )
                
                results.append({
                    "item_id": item.item_id,
                    "status": ResponseStatus.SUCCESS,
                    "data": result
                })
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing batch item {item.item_id}: {str(e)}")
                errors.append({
                    "item_id": item.item_id,
                    "error_type": type(e).__name__,
                    "message": str(e)
                })
                error_count += 1
        
        # Determine overall batch status
        total_items = len(batch.items)
        status = ResponseStatus.SUCCESS
        if error_count > 0:
            status = ResponseStatus.PARTIAL if success_count > 0 else ResponseStatus.FAILURE
        
        message = f"Batch processing complete. {success_count} succeeded, {error_count} failed."
        
        return BatchResponseSchema(
            status=status,
            message=message,
            results=results,
            errors=errors,
            batch_id=batch_id,
            summary={
                "total_items": total_items,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": success_count / total_items if total_items > 0 else 0
            }
        )
    
    async def process_batch_async(self,
                                batch: BatchRequestSchema,
                                background_tasks: BackgroundTasks) -> BatchResponseSchema:
        """
        Process a batch of requests asynchronously.
        
        Args:
            batch: Batch request data
            background_tasks: FastAPI background tasks handler
        
        Returns:
            Response acknowledging batch acceptance
        """
        # Generate a standardized batch ID for async processing
        batch_id = generate_batch_id(source="api_async")
        
        # Add to background tasks
        background_tasks.add_task(
            self._process_batch_background,
            batch,
            batch_id
        )
        
        return BatchResponseSchema(
            status=ResponseStatus.PENDING,
            message="Batch accepted for processing",
            results=[],
            errors=[],
            batch_id=batch_id,
            summary={
                "total_items": len(batch.items),
                "status": "pending"
            }
        )
    
    async def _process_batch_background(self, batch: BatchRequestSchema, batch_id: str) -> None:
        """
        Process a batch in the background.
        
        Args:
            batch: Batch request data
            batch_id: Unique identifier for the batch
        """
        try:
            await self.process_batch(batch)
            logger.info(f"Background processing of batch {batch_id} completed successfully")
            
        except Exception as e:
            logger.exception(f"Error in background processing of batch {batch_id}: {str(e)}") 