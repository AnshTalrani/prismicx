"""Implementation of request processing service."""
from typing import Dict, Any, Optional, Tuple, List
import logging
import json
import asyncio
from datetime import datetime
import dataclasses
import warnings

from src.application.interfaces.request_service import IRequestService
from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.entities.user import User
from src.domain.entities.request import Request, BatchRequest
from src.domain.value_objects.batch_type import BatchType, ProcessingMethod, DataSourceType
from src.domain.exceptions.service_exceptions import ServiceError, ValidationError, ResourceNotFoundError
from src.infrastructure.repositories.request_repository import IRequestRepository
from src.application.interfaces.template_service import ITemplateService
from src.application.services.context_manager import ContextManager
from src.application.interfaces.orchestration_service import IOrchestrationService
from src.application.interfaces.communication_service import ICommunicationService
from src.application.interfaces.nlp_service import INLPService
from src.utils.id_utils import generate_request_id


logger = logging.getLogger(__name__)


class RequestService(IRequestService):
    """Implementation of request processing service."""
    
    def __init__(
        self,
        request_repository: IRequestRepository,
        template_service: ITemplateService,
        context_manager: ContextManager,
        orchestration_service: IOrchestrationService,
        communication_service: ICommunicationService,
        nlp_service: INLPService,
        user_repository=None
    ):
        """
        Initialize the request service.
        
        Args:
            request_repository: Repository for request persistence
            template_service: Service for template management
            context_manager: Manager for context operations
            orchestration_service: Service for request orchestration
            communication_service: Service for user communication
            nlp_service: Service for natural language processing
            user_repository: Repository for accessing user data
        """
        self.request_repository = request_repository
        self.template_service = template_service
        self.context_manager = context_manager
        self.orchestration_service = orchestration_service
        self.communication_service = communication_service
        self.nlp_service = nlp_service
        self.user_repository = user_repository
        logger.info("Initialized request service")
    
    async def process_request(
        self,
        text: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        purpose_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        skip_template_selection: bool = False
    ) -> Dict[str, Any]:
        """
        Process a request based on text or purpose.
        
        Args:
            text: Request text
            user_id: User ID
            request_id: Request ID
            purpose_id: Purpose ID for template selection
            metadata: Additional metadata
            data: Request data
            parameters: Request parameters
            request: Pre-built request object
            skip_template_selection: Skip template selection if purpose_id provided
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Validate user if user_repository is available and user_id is provided
            if self.user_repository and user_id:
                user_exists = await self.user_repository.validate_user_exists(user_id)
                if not user_exists:
                    self.logger.warning(f"User {user_id} does not exist in system_users database")
                    return {"status": "error", "error": "User does not exist"}
            
            request_id = request.id if request else request_id
            start_time = datetime.utcnow()
            
            # Create a minimal user object if user_id is provided
            user = None
            if user_id:
                user = User(
                    id=user_id,
                    name=f"User {user_id}",
                    email=f"user-{user_id}@example.com"
                )
            
            # If no template is provided, get one using purpose_id
            if not request.template and purpose_id:
                request.template = await self.template_service.get_template_by_purpose_id(purpose_id)
                if not request.template:
                    raise ResourceNotFoundError(f"Template not found for purpose: {purpose_id}")
            
            # Detect purpose if not provided
            if not purpose_id and text:
                self.logger.info(f"Detecting purpose for text: '{text}'")
                purpose_id, confidence = await self.nlp_service.detect_purpose_with_confidence(text)
                if not purpose_id:
                    raise ValidationError("Could not determine request purpose")
                self.logger.info(f"Detected purpose {purpose_id} with confidence {confidence}")
                
                # Get template using detected purpose
                if not request.template:
                    request.template = await self.template_service.get_template_by_purpose_id(purpose_id)
                    if not request.template:
                        raise ResourceNotFoundError(f"Template not found for purpose: {purpose_id}")
                
                # Update request with detected purpose
                request.purpose_id = purpose_id
                
            # Store request
            await self.request_repository.save(request)
            
            # Validate template
            validation_result = self._validate_template(request.template)
            if not validation_result[0]:
                return self._create_error_response(request_id, validation_result[1], "validation_error")
            
            # Prepare request data for context
            request_data = {
                "id": request_id,
                "user_id": user_id,
                "text": text,
                "purpose_id": purpose_id,
                "created_at": start_time.isoformat(),
                "data": data or {},
                "metadata": metadata or {}
            }
            
            # Check for urgent flag in request metadata
            if (data and data.get("urgent", False)) or \
               (metadata and metadata.get("urgent", False)):
                request_data["urgent"] = True
                priority = 1  # Highest priority
                self.logger.info(f"Request {request_id} marked as URGENT with priority 1")
            else:
                priority = None  # Use default priority
            
            # Prepare template data for context
            template_data = {
                "id": request.template.id,
                "version": request.template.version,
                "parameters": request.template.parameters,
                "service_template": request.template.service_template
            }
            
            # Get service type
            service_type = request.template.service_type
            if isinstance(service_type, str):
                service_type_str = service_type
            else:
                service_type_str = service_type.value
            
            # Create service-ready context directly with priority
            context_id = await self.context_manager.create_service_context(
                request_data=request_data,
                template_data=template_data,
                service_type=service_type_str,
                source="request_service",
                priority=priority
            )
            
            if not context_id:
                raise ServiceError("Failed to create context for request")
            
            # Return acknowledgment
            result = {
                "success": True,
                "status": "pending",
                "message": f"Request queued for processing by {service_type_str} service",
                "context_id": context_id,
                "request_id": request_id
            }
            
            # Add metadata including priority info
            result["metadata"] = {
                "queued_at": datetime.utcnow().isoformat(),
                "service_type": service_type_str,
                "priority": priority or 5,  # Include priority in response
                "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
            
            # Notify user of queued request if user is provided
            if user:
                await self.communication_service.notify_queued(
                    user=user,
                    request_id=request_id,
                    result=result
                )
            
            self.logger.info(f"Request {request_id} queued for processing with priority {priority or 5}")
            return result
            
        except ValidationError as e:
            self.logger.warning(f"Validation error processing request {request_id}: {str(e)}")
            return self._create_error_response(request_id, str(e), "validation_error")
            
        except ResourceNotFoundError as e:
            self.logger.error(f"Resource not found processing request {request_id}: {str(e)}")
            return self._create_error_response(request_id, str(e), "not_found_error")
            
        except ServiceError as e:
            self.logger.error(f"Service error processing request {request_id}: {str(e)}")
            return self._create_error_response(request_id, str(e), "service_error")
            
        except Exception as e:
            self.logger.exception(f"Unexpected error processing request {request_id}: {str(e)}")
            return self._create_error_response(request_id, str(e), "system_error")
    
    def _create_error_response(
        self,
        request_id: str,
        error_message: str,
        error_type: str
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "success": False,
            "request_id": request_id,
            "error": {
                "type": error_type,
                "message": error_message
            },
            "metadata": {
                "processed_at": datetime.utcnow().isoformat()
            }
        }
    
    async def validate_request(self, request: Request, template: Optional[ExecutionTemplate] = None) -> Dict[str, Any]:
        """
        Validate a request before processing.
        
        Args:
            request: Request to validate
            template: Optional execution template to validate against
            
        Returns:
            Validation results
        """
        try:
            # Check if request has required fields
            if not request.id:
                return {"valid": False, "error": "Request ID is required"}
            
            # If template is provided, validate against it
            if template:
                # Implement template-specific validation logic here
                pass
            
            # If purpose_id is provided, check if a template exists for it
            if request.purpose_id:
                template = await self.template_service.get_template_by_purpose_id(request.purpose_id)
                if not template:
                    return {
                        "valid": False, 
                        "error": f"Template not found for purpose: {request.purpose_id}"
                    }
            
            # If no purpose_id is provided, check if text is available for purpose detection
            elif not request.text:
                return {
                    "valid": False,
                    "error": "Either purpose_id or text is required"
                }
            
            return {"valid": True}
            
        except Exception as e:
            self.logger.error(f"Error validating request: {str(e)}")
            return {"valid": False, "error": str(e)}
    
    async def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """
        Get the status of a request.
        
        Args:
            request_id: ID of the request to check
            
        Returns:
            Request status information
        """
        try:
            # Check if request exists in repository
            request = await self.request_repository.get(request_id)
            if not request:
                return {"found": False, "error": "Request not found"}
            
            # Search for context using the request ID
            context = await self.context_manager.repository.find_by_request_id(request_id)
            if context:
                return {
                    "found": True,
                    "status": context.get("status", "unknown"),
                    "created_at": context.get("created_at"),
                    "updated_at": context.get("updated_at"),
                    "metadata": context.get("metadata", {})
                }
            
            # If context not found, return request info from repository
            return {
                "found": True,
                "status": "submitted",
                "created_at": request.created_at.isoformat() if hasattr(request.created_at, 'isoformat') else str(request.created_at),
                "metadata": request.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error getting request status: {str(e)}")
            return {"found": False, "error": str(e)}
    
    async def process_batch(self, batch_request: BatchRequest) -> Dict[str, Any]:
        """
        Process a batch request based on its batch type.
        
        This method serves as the main entry point for all batch processing,
        delegating to the appropriate specialized method based on the batch type.
        The batch type follows the 2x2 matrix model (processing method × data source type).
        
        Args:
            batch_request: The batch request to process
            
        Returns:
            Batch processing results
        """
        self.logger.info(f"Processing batch {batch_request.id} with type {batch_request.batch_type}")
        
        # Extract processing method and data source type
        process_individually = batch_request.processing_method == ProcessingMethod.INDIVIDUAL
        
        # Route to the appropriate method based on data source type
        if batch_request.data_source_type == DataSourceType.USERS:
            return await self.process_user_batch(batch_request, process_individually=process_individually)
        else:  # CATEGORIES
            return await self.process_category_batch(batch_request, process_individually=process_individually)
    
    async def process_user_batch(
        self,
        batch_request: BatchRequest,
        process_individually: bool = True
    ) -> Dict[str, Any]:
        """
        Process a batch of user requests with user validation.
        
        This method handles user batch processing with enhanced user validation,
        filtering out invalid users before processing.
        
        Args:
            batch_request: Batch request object containing user data
            process_individually: Whether to process users individually
        
        Returns:
            Processing results with detailed validation statistics:
            - success: Overall success flag
            - batch_id: Batch identifier
            - status: Processing status (completed, partial, failed)
            - processed: Number of users processed
            - succeeded: Number of successfully processed users
            - failed: Number of failed user processes
            - total: Total number of valid users
            - valid_users: Number of valid users found
            - invalid_users: Number of invalid users found
            - results: Detailed results for each processed user
        """
        batch_id = batch_request.id
        template_id = batch_request.template_id
        users = batch_request.items
        batch_metadata = batch_request.batch_metadata
        
        self.logger.info(f"Processing user batch {batch_id} with {len(users)} users")
        
        # Lists to track valid and invalid users
        valid_users = []
        invalid_users = []
        
        # Validate users if user_repository is available
        if self.user_repository:
            # Extract user IDs
            user_ids = [user.get("id") for user in users if user.get("id")]
            
            # Validate users in batch
            for user_id in user_ids:
                user_exists = await self.user_repository.validate_user_exists(user_id)
                if user_exists:
                    valid_users.append(user_id)
                else:
                    invalid_users.append(user_id)
                    self.logger.warning(f"User {user_id} does not exist in system_users database")
            
            # Update users list to only include valid users
            users = [user for user in users if user.get("id") in valid_users]
            
            if not users:
                self.logger.warning(f"No valid users in batch {batch_id}")
                return {
                    "status": "completed",
                    "total": len(user_ids),
                    "succeeded": 0,
                    "failed": len(user_ids),
                    "valid_users": 0,
                    "invalid_users": len(invalid_users),
                    "message": "No valid users in batch"
                }
        
        # Get template
        template = await self.template_service.get_template_by_id(template_id)
        if not template:
            return {"success": False, "error": f"Template not found: {template_id}"}
        
        self.logger.info(f"Processing user batch {batch_id} with {len(users)} valid users, process_individually={process_individually}")
        
        # Add data source info to metadata
        batch_metadata["data_source_type"] = "users"
        batch_metadata["processing_method"] = "individual" if process_individually else "batch"
        
        # Create batch context with user validation tracking
        batch_context_id = await self._create_batch_context(
            batch_id=batch_id,
            purpose_id=template.purpose_id,
            item_count=len(users),
            metadata=batch_metadata,
            valid_items=valid_users,
            invalid_items=invalid_users
        )
        
        if process_individually:
            # Process users individually
            max_concurrent = 5  # Configure based on system capacity
            results = []
            processed = 0
            succeeded = 0
            failed = 0
            
            # Process users in chunks
            for i in range(0, len(users), max_concurrent):
                chunk = users[i:i + max_concurrent]
                chunk_tasks = []
                
                for user in chunk:
                    # Extract user_id from the user data
                    user_id = user.get("id") or user.get("user_id")
                    if not user_id:
                        self.logger.warning(f"Skipping user without ID in batch {batch_id}")
                        continue
                    
                    # Generate unique request ID for this user in the batch
                    request_id = generate_request_id(source=f"batch_{batch_id}_{user_id}")
                    
                    # Create request object
                    request = Request(
                        id=request_id,
                        user_id=user_id,
                        text="",  # No text needed for batch processing
                        purpose_id=template.purpose_id,
                        data=user,
                        metadata={
                            "batch_id": batch_id,
                            "batch_context_id": batch_context_id
                        }
                    )
                    
                    # Create task for processing
                    task = asyncio.create_task(self.process_request(request=request, skip_template_selection=True))
                    chunk_tasks.append((user_id, task))
                
                # Wait for all tasks in this chunk to complete
                for user_id, task in chunk_tasks:
                    try:
                        result = await task
                        results.append({
                            "user_id": user_id,
                            "success": result.get("success", False),
                            "result_id": result.get("result_id", ""),
                            "data": result.get("data", {})
                        })
                        processed += 1
                        if result.get("success", False):
                            succeeded += 1
                        else:
                            failed += 1
                    except Exception as e:
                        self.logger.error(f"Error processing user {user_id} in batch {batch_id}: {str(e)}")
                        results.append({
                            "user_id": user_id,
                            "success": False,
                            "error": {"message": str(e)}
                        })
                        processed += 1
                        failed += 1
                
                # Update progress
                await self._update_batch_progress(
                    batch_context_id=batch_context_id,
                    processed=processed,
                    succeeded=succeeded,
                    failed=failed,
                    total=len(users)
                )
            
            # Determine overall status
            status = "completed"
            if failed > 0:
                if succeeded > 0:
                    status = "partial"
                else:
                    status = "failed"
                    
            # Update batch status
            await self._update_batch_status(batch_context_id, status)
            
            # Return results with validation information
            return {
                "success": True,
                "batch_id": batch_id,
                "status": status,
                "processed": processed,
                "succeeded": succeeded,
                "failed": failed,
                "total": len(users),
                "valid_users": len(valid_users),
                "invalid_users": len(invalid_users),
                "results": results
            }
        else:
            # Process users as a batch (all together)
            try:
                # Create a single request for the entire batch
                request_id = generate_request_id(source=f"batch_group_{batch_id}")
                request = Request(
                    id=request_id,
                    text=f"Batch processing for {len(users)} users",
                    purpose_id=template.purpose_id,
                    data={"users": users},
                    metadata={
                        "batch_id": batch_id,
                        "batch_context_id": batch_context_id,
                        "is_group_processing": True,
                        "validation_stats": {
                            "valid_users": len(valid_users),
                            "invalid_users": len(invalid_users)
                        }
                    }
                )
                
                # Process the request
                result = await self.process_request(request=request, skip_template_selection=True)
                
                # Update batch status
                status = "completed" if result.get("success", False) else "failed"
                await self._update_batch_status(batch_context_id, status)
                
                # Return result with batch information and validation stats
                return {
                    "success": result.get("success", False),
                    "batch_id": batch_id,
                    "status": status,
                    "valid_users": len(valid_users),
                    "invalid_users": len(invalid_users),
                    "result_id": result.get("result_id", ""),
                    "data": result.get("data", {}),
                    "metadata": result.get("metadata", {})
                }
                
            except Exception as e:
                self.logger.error(f"Error processing user batch {batch_id}: {str(e)}")
                await self._update_batch_status(batch_context_id, "failed")
                
                return {
                    "success": False,
                    "batch_id": batch_id,
                    "status": "failed",
                    "valid_users": len(valid_users),
                    "invalid_users": len(invalid_users),
                    "error": {"message": str(e)}
                }
    
    async def process_category_batch(self, batch_request: BatchRequest,
                                   process_individually: Optional[bool] = None) -> Dict[str, Any]:
        """
        Process a batch of categories with enhanced validation.
        
        This method handles category batch processing with validation of both
        category IDs and any user references contained within the categories.
        User references are validated against the system_users database.
        
        Args:
            batch_request: The batch request containing category data
            process_individually: Whether to process categories individually or as a group.
                                 If None, uses the batch_type from the request.
            
        Returns:
            Batch processing results with validation statistics:
            - success: Overall success flag
            - batch_id: Batch identifier
            - status: Processing status (completed, partial, failed)
            - processed: Number of categories processed
            - succeeded: Number of successfully processed categories
            - failed: Number of failed category processes
            - total: Total number of valid categories
            - valid_categories: Number of valid categories found
            - invalid_categories: Number of invalid categories found
            - user_references: Validation statistics for referenced users
            - results: Detailed results for each processed category
        """
        batch_id = batch_request.id
        template_id = batch_request.template_id
        categories = batch_request.items
        metadata = batch_request.batch_metadata
        
        # Determine processing method - use parameter if provided, else use batch type
        if process_individually is None:
            process_individually = batch_request.processing_method == ProcessingMethod.INDIVIDUAL
        
        # Get template
        template = await self.template_service.get_template_by_id(template_id)
        if not template:
            return {"success": False, "error": f"Template not found: {template_id}"}
            
        # Check if we have any categories to process
        if not categories:
            return {"success": False, "error": "No categories provided for batch processing"}
        
        # Lists to track valid and invalid categories
        valid_categories = []
        invalid_categories = []
        
        # Track user references if present in categories
        referenced_users = {}
        valid_referenced_users = []
        invalid_referenced_users = []
        
        # Validate categories and extract user references if any
        for category in categories:
            category_id = category.get("id") or category.get("category_id")
            if not category_id:
                self.logger.warning(f"Skipping category without ID in batch {batch_id}")
                continue
                
            valid_categories.append(category_id)
            
            # Look for user references in the category
            user_refs = category.get("user_ids", []) or category.get("member_ids", []) or []
            
            # Validate user references if we have a user repository
            if user_refs and self.user_repository:
                for user_id in user_refs:
                    # Skip if we've already checked this user
                    if user_id in referenced_users:
                        continue
                        
                    # Validate user existence
                    user_exists = await self.user_repository.validate_user_exists(user_id)
                    referenced_users[user_id] = user_exists
                    
                    if user_exists:
                        valid_referenced_users.append(user_id)
                    else:
                        invalid_referenced_users.append(user_id)
                        self.logger.warning(f"Referenced user {user_id} in category {category_id} does not exist")
        
        self.logger.info(
            f"Processing category batch {batch_id} with {len(valid_categories)} categories, "
            f"process_individually={process_individually}, "
            f"referenced users: {len(valid_referenced_users)} valid, {len(invalid_referenced_users)} invalid"
        )
        
        # Extract category type if available
        category_type = metadata.get("category_type", "unknown")
        reference_type = metadata.get("reference_type", "distribute_to_members")
        
        # Update metadata with validation results
        metadata["data_source_type"] = "categories"
        metadata["processing_method"] = "individual" if process_individually else "batch"
        metadata["category_type"] = category_type
        metadata["reference_type"] = reference_type
        
        if referenced_users:
            metadata["user_references"] = {
                "total": len(referenced_users),
                "valid": len(valid_referenced_users),
                "invalid": len(invalid_referenced_users)
            }
        
        # Create batch context with validation tracking
        batch_context_id = await self._create_batch_context(
            batch_id=batch_id,
            purpose_id=template.purpose_id,
            item_count=len(valid_categories),
            metadata=metadata,
            valid_items=valid_categories,
            invalid_items=invalid_categories
        )
        
        if process_individually:
            # Process categories individually
            max_concurrent = 5  # Configure based on system capacity
            results = []
            processed = 0
            succeeded = 0
            failed = 0
            
            # Process categories in chunks
            for i in range(0, len(categories), max_concurrent):
                chunk = categories[i:i + max_concurrent]
                chunk_tasks = []
                
                for category in chunk:
                    # Extract category ID from the category data
                    category_id = category.get("id") or category.get("category_id")
                    if not category_id:
                        self.logger.warning(f"Skipping category without ID in batch {batch_id}")
                        continue
                    
                    # Generate unique request ID for this category in the batch
                    request_id = generate_request_id(source=f"batch_{batch_id}_{category_id}")
                    
                    # Create request object
                    request = Request(
                        id=request_id,
                        text=f"Processing category {category_id}",
                        purpose_id=template.purpose_id,
                        data=category,
                        metadata={
                            "batch_id": batch_id,
                            "batch_context_id": batch_context_id,
                            "category_type": category_type,
                            "user_references": {
                                "valid": [uid for uid in category.get("user_ids", []) or category.get("member_ids", []) 
                                         if uid in valid_referenced_users],
                                "invalid": [uid for uid in category.get("user_ids", []) or category.get("member_ids", []) 
                                           if uid in invalid_referenced_users]
                            } if referenced_users else {}
                        }
                    )
                    
                    # Create task for processing
                    task = asyncio.create_task(self.process_request(request=request, skip_template_selection=True))
                    chunk_tasks.append((category_id, task))
                
                # Wait for all tasks in this chunk to complete
                for category_id, task in chunk_tasks:
                    try:
                        result = await task
                        results.append({
                            "category_id": category_id,
                            "success": result.get("success", False),
                            "result_id": result.get("result_id", ""),
                            "data": result.get("data", {})
                        })
                        processed += 1
                        if result.get("success", False):
                            succeeded += 1
                        else:
                            failed += 1
                    except Exception as e:
                        self.logger.error(f"Error processing category {category_id} in batch {batch_id}: {str(e)}")
                        results.append({
                            "category_id": category_id,
                            "success": False,
                            "error": {"message": str(e)}
                        })
                        processed += 1
                        failed += 1
                
                # Update progress
                await self._update_batch_progress(
                    batch_context_id=batch_context_id,
                    processed=processed,
                    succeeded=succeeded,
                    failed=failed,
                    total=len(valid_categories)
                )
            
            # Determine overall status
            status = "completed"
            if failed > 0:
                if succeeded > 0:
                    status = "partial"
                else:
                    status = "failed"
                    
            # Update batch status
            await self._update_batch_status(batch_context_id, status)
            
            # Return results with validation information
            return {
                "success": True,
                "batch_id": batch_id,
                "status": status,
                "processed": processed,
                "succeeded": succeeded,
                "failed": failed,
                "total": len(valid_categories),
                "valid_categories": len(valid_categories),
                "invalid_categories": len(invalid_categories),
                "user_references": {
                    "valid": len(valid_referenced_users),
                    "invalid": len(invalid_referenced_users)
                } if referenced_users else {},
                "results": results
            }
        else:
            # Process as a single batch object
            try:
                # Create a single request for the entire batch
                request_id = generate_request_id(source=f"batch_obj_{batch_id}")
                request = Request(
                    id=request_id,
                    text=f"Batch processing for {category_type}",
                    purpose_id=template.purpose_id,
                    data={"categories": categories},
                    metadata={
                        "batch_id": batch_id,
                        "batch_context_id": batch_context_id,
                        "category_type": category_type,
                        "reference_type": reference_type,
                        "validation_stats": {
                            "valid_categories": len(valid_categories),
                            "invalid_categories": len(invalid_categories),
                            "valid_referenced_users": len(valid_referenced_users),
                            "invalid_referenced_users": len(invalid_referenced_users)
                        }
                    }
                )
                
                # Process the request
                result = await self.process_request(request=request, skip_template_selection=True)
                
                # Update batch status
                status = "completed" if result.get("success", False) else "failed"
                await self._update_batch_status(batch_context_id, status)
                
                # Return result with batch information and validation stats
                return {
                    "success": result.get("success", False),
                    "batch_id": batch_id,
                    "status": status,
                    "valid_categories": len(valid_categories),
                    "invalid_categories": len(invalid_categories),
                    "user_references": {
                        "valid": len(valid_referenced_users),
                        "invalid": len(invalid_referenced_users)
                    } if referenced_users else {},
                    "result_id": result.get("result_id", ""),
                    "data": result.get("data", {}),
                    "metadata": result.get("metadata", {})
                }
                
            except Exception as e:
                self.logger.error(f"Error processing category batch {batch_id}: {str(e)}")
                await self._update_batch_status(batch_context_id, "failed")
                
                return {
                    "success": False,
                    "batch_id": batch_id,
                    "status": "failed",
                    "valid_categories": len(valid_categories),
                    "invalid_categories": len(invalid_categories),
                    "user_references": {
                        "valid": len(valid_referenced_users),
                        "invalid": len(invalid_referenced_users)
                    } if referenced_users else {},
                    "error": {"message": str(e)}
                }
    
    # Helper methods for batch processing
    
    async def _create_batch_context(self, batch_id: str, item_count: int, purpose_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, valid_items: Optional[List[str]] = None, invalid_items: Optional[List[str]] = None) -> str:
        """
        Create a context for a batch job with enhanced tracking of validated items.
        
        Args:
            batch_id: Unique batch identifier
            item_count: Number of items in the batch
            purpose_id: Optional purpose identifier
            metadata: Additional batch metadata
            valid_items: List of valid item IDs (user_ids or category_ids)
            invalid_items: List of invalid item IDs
            
        Returns:
            Context ID
        """
        # Ensure metadata exists
        if not metadata:
            metadata = {}
            
        # Determine batch type
        data_source_type = metadata.get("data_source_type", "unknown")
        processing_method = metadata.get("processing_method", "individual")
        
        # Create batch type information
        batch_type = {
            "processing_method": processing_method,
            "data_source_type": data_source_type
        }
        
        # Create the batch context with enhanced tracking
        context_id = await self.context_manager.create_batch_context(
            batch_id=batch_id,
            batch_type=batch_type,
            purpose_id=purpose_id,
            item_count=item_count,
            metadata=metadata,
            valid_items=valid_items,
            invalid_items=invalid_items
        )
        
        return context_id
    
    async def _update_batch_progress(self, batch_context_id: str, processed: int, succeeded: int, failed: int, total: int) -> None:
        """
        Update batch context with progress information.
        
        Updates the progress tracking in the batch context document, including
        counts of processed, succeeded, and failed items, along with percentage completion.
        
        Args:
            batch_context_id: ID of the batch context to update
            processed: Number of items processed so far
            succeeded: Number of items processed successfully
            failed: Number of items that failed processing
            total: Total number of valid items to process
        """
        context = await self.context_manager.repository.get(batch_context_id)
        if context:
            # Calculate percentage
            percentage = int((processed / total) * 100) if total > 0 else 0
            
            # Update results
            if "results" not in context:
                context["results"] = {}
            
            context["results"]["progress"] = {
                "processed": processed,
                "succeeded": succeeded,
                "failed": failed,
                "total": total,
                "percentage": percentage
            }
            
            context["updated_at"] = datetime.utcnow().isoformat()
            
            await self.context_manager.repository.save(batch_context_id, context)
    
    async def _update_batch_status(self, batch_context_id: str, status: str) -> None:
        """
        Update batch context status.
        
        Updates the status field in the batch context document and sets completion
        timestamps when appropriate. This method is called when the batch processing
        state changes (e.g., initializing → in_progress → completed).
        
        Args:
            batch_context_id: ID of the batch context to update
            status: New status value (e.g., 'completed', 'failed', 'partial')
        """
        context = await self.context_manager.repository.get(batch_context_id)
        if context:
            context["status"] = status
            context["updated_at"] = datetime.utcnow().isoformat()
            
            if status in ["completed", "failed", "completed_with_errors"]:
                context["completed_at"] = datetime.utcnow().isoformat()
            
            await self.context_manager.repository.save(batch_context_id, context)
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep merge two dictionaries, with source values taking precedence.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                self._deep_merge(target[key], value)
            elif key in target and isinstance(target[key], list) and isinstance(value, list):
                # Append lists
                target[key].extend(value)
            else:
                # Set value
                target[key] = value 