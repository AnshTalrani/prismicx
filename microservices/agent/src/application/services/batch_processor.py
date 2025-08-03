"""
Unified Batch Processor Service for handling batch operations.

This module combines the original BatchProcessor with the EnhancedBatchProcessor
to provide a single unified implementation with preference-based batch processing capabilities.
"""
import logging
import asyncio
import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, TYPE_CHECKING
import os
import json
import time
import uuid
import copy
import warnings

from src.domain.entities.request import Request, BatchRequest
from src.domain.entities.execution_template import ExecutionTemplate
from src.application.interfaces.request_service import IRequestService
from src.application.interfaces.repository.category_repository import ICategoryRepository
from src.infrastructure.services.job_statistics import JobStatistics
from src.utils.id_utils import generate_batch_id, generate_request_id
from src.domain.value_objects.batch_type import BatchType, ProcessingMethod, DataSourceType
from src.infrastructure.clients.config_database_client import ConfigDatabaseClient
from src.infrastructure.repositories.user_repository import UserRepository

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.application.services.context_manager import ContextManager

logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Service for orchestrating batch job processing.
    
    This service focuses on job orchestration, delegating the actual context management
    and processing to the RequestService. It maintains tracking information about
    active batches and job statistics, but does not directly manage contexts.
    
    Features:
    - Support for both individual requests grouped into batches and batches as objects
    - Prioritization of batch jobs based on configuration
    - Processing order management
    - Automatic retry for failed items
    - Result distribution to appropriate users
    - Stateful batch processing with progress tracking
    """
    
    # Default batch size for processing individual items
    DEFAULT_BATCH_SIZE = 100
    
    def __init__(
        self,
        request_service: IRequestService,
        category_repository: ICategoryRepository,
        context_manager: Optional["ContextManager"] = None,
        max_concurrent_items: int = 5,
        retry_limit: int = 3,
        config_db_client=None,
        user_repository=None
    ):
        """
        Initialize BatchProcessor with dependencies.
        
        Args:
            request_service: Service for handling requests
            category_repository: Repository for category data
            context_manager: Manager for context operations
            max_concurrent_items: Maximum number of items to process concurrently
            retry_limit: Maximum number of retries for failed items
            config_db_client: Optional client for config database
            user_repository: Optional repository for user data
        """
        self.request_service = request_service
        self.category_repository = category_repository
        self.context_manager = context_manager
        self.max_concurrent_items = max_concurrent_items
        self.retry_limit = retry_limit
        self.logger = logging.getLogger(__name__)
        self.active_batches = {}
        self.job_statistics = {}  # job_id -> JobStatistics
        
        # Config Database client for user preferences
        self.config_db_client = config_db_client
        self.user_repository = user_repository
        
        # Load batch configurations (will be populated by batch_scheduler)
        self.batch_configs = {}
        self.config_file = os.path.join("data", "batch", "batch_config.json")
        self._load_batch_configs()
        
    async def process_job(self, job_name: str, parameters: Dict[str, Any] = None) -> str:
        """
        Process a batch job by job name.
        
        Args:
            job_name: Name of the job to process
            parameters: Optional parameters to override job configuration
        
        Returns:
            Batch ID of the created batch
        """
        try:
            # Get job configuration
            job_config = self._get_job_config(job_name)
            if not job_config:
                raise ValueError(f"Job configuration for {job_name} not found")
                
            # Override parameters if provided
            if parameters:
                job_config = self._merge_parameters(job_config, parameters)
                
            # Create new batch using ID utilities
            batch_id = generate_batch_id(source="job_" + job_name)
            
            # Log batch creation
            self.logger.info(f"Creating new batch {batch_id} for job {job_name}")
            
            # Add to active batches
            self.active_batches[batch_id] = {
                "job_config": job_config,
                "status": "created",
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Process batch asynchronously
            asyncio.create_task(self._process_batch(batch_id))
            
            return batch_id
            
        except Exception as e:
            self.logger.error(f"Error creating batch for job {job_name}: {str(e)}")
            raise
    
    async def process_batch(self, batch_type: BatchType, items: List[Dict[str, Any]], 
                           template: Optional[ExecutionTemplate] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a batch of items.
        
        Args:
            batch_type: Type of batch (INDIVIDUAL_USERS, BATCH_USERS, 
                       INDIVIDUAL_CATEGORIES, BATCH_CATEGORIES, etc.)
            items: List of items to process
            template: Optional execution template
            metadata: Optional batch metadata
        
        Returns:
            Batch ID
        """
        batch_id = generate_batch_id(source="api")
        
        # Set initial batch status
        self.active_batches[batch_id] = {
            "status": "initializing",
            "start_time": datetime.datetime.now().isoformat(),
            "type": batch_type.value,
            "item_count": len(items),
            "metadata": metadata or {},
            "processing_method": batch_type.processing_method.value,
            "data_source_type": batch_type.data_source_type.value
        }
        
        # Get or create template ID
        template_id = None
        if template:
            template_id = template.id
        
        # Create BatchRequest object
        batch_request = BatchRequest(
            id=batch_id,
            source="batch_processor",
            template_id=template_id or "default_template",
            items=items,
            batch_type=batch_type,
            batch_metadata=metadata or {}
        )
        
        # Process the batch using the request service directly
        asyncio.create_task(self._process_using_request_service(batch_request, template))
        
        return batch_id
    
    async def _process_using_request_service(self, batch_request: BatchRequest, 
                                           template: Optional[ExecutionTemplate] = None) -> None:
        """
        Process a batch using the request service.
        
        Args:
            batch_request: The batch request to process
            template: Optional execution template
        """
        try:
            batch_id = batch_request.id
            
            # Get job statistics
            job_stats = self._get_job_statistics(batch_id)
            
            # Record execution start
            expected_count = len(batch_request.items)
            if batch_request.processing_method == ProcessingMethod.BATCH and \
               batch_request.data_source_type == DataSourceType.CATEGORIES:
                # For batch categories, count is just 1
                expected_count = 1
                
            # Record execution start in statistics
            job_stats.record_execution_start(
                batch_id, 
                batch_request.batch_type.value, 
                batch_request.template_id, 
                expected_count
            )
            
            # Update batch status
            self.active_batches[batch_id]["status"] = "processing"
            
            # Process the batch using the request service
            result = await self.request_service.process_batch(batch_request)
            
            # Update batch status
            status = result.get("status", "unknown")
            self.active_batches[batch_id]["status"] = status
            self.active_batches[batch_id]["result"] = result
            self.active_batches[batch_id]["completed_at"] = datetime.datetime.now().isoformat()
            
            # Record execution end in statistics
            processed = result.get("processed", 0)
            succeeded = result.get("succeeded", 0)
            failed = result.get("failed", 0)
            
            job_stats.record_execution_end(
                batch_id,
                total_processed=processed,
                succeeded=succeeded,
                failed=failed
            )
            
            self.logger.info(f"Completed batch {batch_id} with status {status}")
            
        except Exception as e:
            self.logger.error(f"Error processing batch {batch_id}: {str(e)}")
            self.active_batches[batch_id]["status"] = "failed"
            self.active_batches[batch_id]["error"] = str(e)
            self.active_batches[batch_id]["completed_at"] = datetime.datetime.now().isoformat()
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get status of a batch from internal tracking.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            Batch status information
        """
        # Check active batches
        if batch_id in self.active_batches:
            return self.active_batches[batch_id]
        
        return {"status": "not_found"}
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel a running batch.
        
        Args:
            batch_id: Batch ID
        
        Returns:
            Success status
        """
        if batch_id not in self.active_batches:
            self.logger.warning(f"Batch {batch_id} not found for cancellation")
            return False
            
        # Only cancel if still processing
        if self.active_batches[batch_id]["status"] in ["created", "initializing", "processing"]:
            self.active_batches[batch_id]["status"] = "cancelled"
            self.active_batches[batch_id]["cancelled_at"] = datetime.datetime.now().isoformat()
            self.logger.info(f"Cancelled batch {batch_id}")
            return True
        
        self.logger.warning(f"Batch {batch_id} cannot be cancelled in status {self.active_batches[batch_id]['status']}")
        return False
    
    async def _process_batch(self, batch_id: str) -> None:
        """
        Process a batch based on its configuration.
        
        Args:
            batch_id: Batch ID
        """
        try:
            # Get batch configuration
            batch_info = self.active_batches.get(batch_id)
            if not batch_info:
                self.logger.error(f"Batch {batch_id} not found in active batches")
                return
                
            job_config = batch_info.get("job_config", {})
            
            # Get batch type from job config
            batch_type_str = job_config.get("type", "INDIVIDUAL_USERS")
            try:
                # Parse batch type from string using the 2x2 matrix format
                parts = batch_type_str.upper().split("_", 1)
                if len(parts) == 2:
                    processing_method = ProcessingMethod.from_string(parts[0])
                    data_source_type = DataSourceType.from_string(parts[1])
                    batch_type = BatchType(processing_method, data_source_type)
                else:
                    # Default to INDIVIDUAL_USERS if format is invalid
                    self.logger.warning(f"Invalid batch type format: {batch_type_str}, defaulting to INDIVIDUAL_USERS")
                    batch_type = BatchType.INDIVIDUAL_USERS
            except ValueError:
                self.logger.error(f"Invalid batch type: {batch_type_str}, defaulting to INDIVIDUAL_USERS")
                batch_type = BatchType.INDIVIDUAL_USERS
                
            job_id = job_config.get("job_id", "unknown")
            purpose_id = job_config.get("purpose_id", "unknown")
            
            # Get job statistics
            job_stats = self._get_job_statistics(job_id)
            
            # Extract processing method and data source
            processing_method = batch_type.processing_method
            data_source_type = batch_type.data_source_type
            
            # Determine if processing individually
            process_individually = processing_method == ProcessingMethod.INDIVIDUAL
            
            # Record execution start
            expected_count = self._estimate_item_count(batch_type, job_config)
            
            # Record execution start in statistics
            job_stats.record_execution_start(
                batch_id=batch_id, 
                batch_type=batch_type.value,
                purpose_id=purpose_id, 
                expected_count=expected_count
            )
            
            # Log batch processing start
            self.logger.info(
                f"Starting processing of batch {batch_id} with type {batch_type}, "
                f"process_individually={process_individually}, data_source={data_source_type}"
            )
            
            # Update batch status
            self.active_batches[batch_id]["status"] = "processing"
            
            # Process batch based on modern 2x2 matrix model
            result = {}
            
            if data_source_type == DataSourceType.USERS:
                # Process user batch
                result = await self._process_modern_user_batch(
                    batch_id=batch_id,
                    job_config=job_config,
                    process_individually=process_individually
                )
            else:  # CATEGORIES
                # Process category batch
                result = await self._process_modern_category_batch(
                    batch_id=batch_id,
                    job_config=job_config,
                    process_individually=process_individually
                )
            
            # Update job statistics
            if process_individually:
                job_stats.update_execution_progress(
                    batch_id=batch_id,
                    processed=result.get("total", 0),
                    succeeded=result.get("succeeded", 0),
                    failed=result.get("failed", 0)
                )
            else:
                # For batch processing, it's either success (1) or failure (0)
                if result.get("status") == "completed":
                    job_stats.update_execution_progress(batch_id=batch_id, processed=1, succeeded=1)
                else:
                    job_stats.update_execution_progress(batch_id=batch_id, processed=1, failed=1)
                
            job_stats.record_execution_complete(batch_id=batch_id, status=result.get("status", "unknown"))
                
        except Exception as e:
            self.logger.error(f"Error processing batch {batch_id}: {str(e)}")
            # Try to update batch status if possible
            try:
                self.active_batches[batch_id]["status"] = "failed"
                job_stats = self._get_job_statistics(self.active_batches[batch_id].get("job_config", {}).get("job_id", "unknown"))
                job_stats.record_execution_complete(batch_id=batch_id, status="failed")
            except Exception:
                pass
    
    def _estimate_item_count(self, batch_type: BatchType, job_config: Dict[str, Any]) -> int:
        """
        Estimate the number of items in a batch based on its type and configuration.
        
        Args:
            batch_type: Type of batch
            job_config: Job configuration
            
        Returns:
            Estimated item count
        """
        # Base estimates on data source type and processing method
        if batch_type.data_source_type == DataSourceType.USERS:
            if batch_type.processing_method == ProcessingMethod.INDIVIDUAL:
                # For individual users, count depends on filters
                filters = job_config.get("filters", {})
                if filters.get("all_users", False):
                    return 3000  # Approximate total user count
                else:
                    # Estimate based on filters
                    return 1000  # Default estimate
            else:
                # For batch users, count is 1 (processed as a group)
                return 1
        else:  # CATEGORIES
            if batch_type.processing_method == ProcessingMethod.INDIVIDUAL:
                # For individual categories, estimate based on category size
                categories = job_config.get("categories", [])
                return len(categories) or 100  # Default if not specified
            else:
                # For batch categories, count is 1 (processed as a group)
                # Special case for combinations in metadata
                if job_config.get("metadata", {}).get("is_combined_batch", False):
                    # For combinations, count is number of category combinations
                    categories = job_config.get("categories", [])
                    if len(categories) >= 2:
                        # Rough estimate of combinations
                        return 10 * 10  # Assuming ~10 categories of each type
                return 1
    
    async def _process_modern_user_batch(self, batch_id: str, job_config: Dict[str, Any], 
                                       process_individually: bool) -> Dict[str, Any]:
        """
        Process a user batch with the modern 2x2 matrix model.
        
        Args:
            batch_id: Batch ID
            job_config: Job configuration
            process_individually: Whether to process users individually
            
        Returns:
            Processing results
        """
        template_id = job_config.get("template_id")
        if not template_id:
            self.logger.error(f"No template ID specified for batch {batch_id}")
            return {"status": "failed", "error": "No template ID specified"}
            
        # Get users based on filters
        users = await self._get_users_by_filters(job_config.get("filters", {}))
        
        if not users:
            self.logger.warning(f"No users found for batch {batch_id}")
            return {"status": "completed", "total": 0, "succeeded": 0, "failed": 0}
            
        # Create a batch request
        batch_request = BatchRequest.create_user_batch(
            source=f"batch_processor_{batch_id}",
            template_id=template_id,
            users=users,
            process_individually=process_individually,
            batch_metadata=job_config.get("metadata", {})
        )
        
        # Process the batch using request service
        return await self.request_service.process_user_batch(
            batch_request=batch_request,
            process_individually=process_individually
        )
    
    async def _process_modern_category_batch(self, batch_id: str, job_config: Dict[str, Any],
                                          process_individually: bool) -> Dict[str, Any]:
        """
        Process a category batch with the modern 2x2 matrix model.
        
        Args:
            batch_id: Batch ID
            job_config: Job configuration
            process_individually: Whether to process categories individually
            
        Returns:
            Processing results
        """
        template_id = job_config.get("template_id")
        if not template_id:
            self.logger.error(f"No template ID specified for batch {batch_id}")
            return {"status": "failed", "error": "No template ID specified"}
            
        # Get categories based on configuration
        categories = await self._get_categories_by_config(job_config)
        
        if not categories:
            self.logger.warning(f"No categories found for batch {batch_id}")
            return {"status": "completed", "total": 0, "succeeded": 0, "failed": 0}
            
        # Create metadata with additional processing information
        metadata = job_config.get("metadata", {}).copy()
        metadata["category_type"] = job_config.get("category_type", "unknown")
        
        # Handle "combined" batch type specially
        is_combined = job_config.get("type") == "combination"
        if is_combined:
            metadata["is_combined_batch"] = True
            metadata["combination_type"] = job_config.get("combination_type", "matrix")
            
        # Create a batch request
        batch_request = BatchRequest.create_category_batch(
            source=f"batch_processor_{batch_id}",
            template_id=template_id,
            categories=categories,
            process_individually=process_individually,
            batch_metadata=metadata
        )
        
        # Process the batch using request service
        return await self.request_service.process_category_batch(
            batch_request=batch_request,
            process_individually=process_individually
        )
        
    # Enhanced Batch Processor functionality
    
    async def process_user_preference_batch(self, feature_type: str, frequency: str, time_key: str) -> str:
        """
        Process a batch based on user preferences.
        
        Args:
            feature_type: Type of feature to process (e.g., "instagram_posts")
            frequency: Frequency of processing ("daily", "weekly", etc.)
            time_key: Time key for the processing schedule
            
        Returns:
            Batch ID
        """
        if not self.config_db_client:
            raise ValueError("Config database client is required for preference-based batches")
            
        try:
            # Create a batch ID for this preference-based batch
            batch_id = generate_batch_id(source=f"pref_{feature_type}_{frequency}")
            
            # Get users with matching preferences
            users = await self.config_db_client.get_frequency_group_users(
                feature_type, 
                frequency, 
                time_key
            )
            
            if not users:
                self.logger.warning(f"No users found with preferences for {feature_type} at {frequency}:{time_key}")
                return None
                
            self.logger.info(f"Creating preference batch {batch_id} for {len(users)} users")
            
            # Initialize batch in tracking
            self.active_batches[batch_id] = {
                "status": "initializing",
                "type": "preference_batch",
                "feature_type": feature_type,
                "frequency": frequency,
                "time_key": time_key,
                "user_count": len(users),
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Process asynchronously
            asyncio.create_task(self._process_preference_based_batch(batch_id, users, feature_type))
            
            return batch_id
            
        except Exception as e:
            self.logger.error(f"Error creating preference batch for {feature_type}: {str(e)}")
            raise
    
    async def _process_preference_based_batch(self, batch_id: str, users: List[Dict[str, Any]], feature_type: str):
        """
        Process a batch based on user preferences.
        
        Args:
            batch_id: Batch ID
            users: List of users with their preferences
            feature_type: Feature type to process
        """
        if not users:
            self.logger.warning(f"No users to process in preference batch {batch_id}")
            self.active_batches[batch_id]["status"] = "completed"
            self.active_batches[batch_id]["warning"] = "No users to process"
            return
            
        try:
            # Get template for this feature type
            template_id = self._get_template_for_feature(feature_type)
            
            # Update batch status
            self.active_batches[batch_id]["status"] = "processing"
            self.active_batches[batch_id]["template_id"] = template_id
            
            # Process concurrently with semaphore
            semaphore = asyncio.Semaphore(self.max_concurrent_items)
            total_users = len(users)
            processed = 0
            succeeded = 0
            failed = 0
            
            # Process each user concurrently
            async def process_user_task(user_data):
                nonlocal processed, succeeded, failed
                
                try:
                    user_id = user_data.get("user_id")
                    if not user_id:
                        self.logger.warning(f"Missing user_id in user data: {user_data}")
                        failed += 1
                        return
                        
                    # Process this user
                    result = await self._process_user_with_preferences(
                        user_id, 
                        template_id,
                        feature_type,
                        batch_id
                    )
                    
                    # Update counters
                    if result and result.get("success"):
                        succeeded += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing user in preference batch: {str(e)}")
                    failed += 1
                    
                finally:
                    processed += 1
                    
                    # Update batch progress
                    if batch_id in self.active_batches:
                        progress = (processed / total_users) * 100
                        self.active_batches[batch_id]["progress"] = {
                            "processed": processed,
                            "succeeded": succeeded,
                            "failed": failed,
                            "total": total_users,
                            "percentage": int(progress)
                        }
            
            # Create and run tasks
            tasks = []
            for user_data in users:
                task = asyncio.create_task(
                    self._with_semaphore(semaphore, process_user_task(user_data))
                )
                tasks.append(task)
                
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
            # Update final batch status
            if failed == 0:
                status = "completed"
            elif succeeded == 0:
                status = "failed"
            else:
                status = "completed_with_errors"
                
            self.active_batches[batch_id]["status"] = status
            self.active_batches[batch_id]["completed_at"] = datetime.datetime.now().isoformat()
            
            self.logger.info(
                f"Completed preference batch {batch_id}: {succeeded} succeeded, {failed} failed"
            )
            
        except Exception as e:
            self.logger.error(f"Error processing preference batch {batch_id}: {str(e)}")
            if batch_id in self.active_batches:
                self.active_batches[batch_id]["status"] = "failed"
                self.active_batches[batch_id]["error"] = str(e)
    
    async def _with_semaphore(self, semaphore, coro):
        """Helper for using semaphore with async tasks."""
        async with semaphore:
            return await coro
    
    async def _process_user_with_preferences(self, user_id: str, template_id: str, feature_type: str, batch_id: str):
        """
        Process a single user with their preferences.
        
        Args:
            user_id: User ID to process
            template_id: Template ID to use for processing
            feature_type: Feature type being processed
            batch_id: Parent batch ID
            
        Returns:
            Processing result
        """
        try:
            # Validate user exists if we have user_repository
            if self.user_repository:
                user_exists = await self.user_repository.validate_user_exists(user_id)
                if not user_exists:
                    self.logger.warning(f"User {user_id} does not exist in system_users database")
                    return {"success": False, "error": "User does not exist"}
            
            # Get user preferences for this feature
            user_preferences = await self.config_db_client.get_user_preferences(
                user_id, 
                feature_type
            )
            
            if not user_preferences:
                self.logger.warning(f"No preferences found for user {user_id} and feature {feature_type}")
                return {"success": False, "error": "No user preferences found"}
            
            # Get tenant ID for the user - either from preferences or use directly from user_repository
            tenant_id = user_preferences.get("tenant_id")
            
            # If tenant ID not in preferences, try to get it from the user repository
            if not tenant_id and self.user_repository:
                tenant_id = await self.user_repository.get_user_tenant(user_id)
            # Fall back to config database client if necessary
            elif not tenant_id and hasattr(self.config_db_client, "get_user_tenant"):
                tenant_id = await self.config_db_client.get_user_tenant(user_id)
            
            # Create a request ID for this user
            request_id = generate_request_id(source=f"pref_{feature_type}")
            
            # Prepare request data
            request_data = {
                "id": request_id,
                "batch_id": batch_id,
                "user_id": user_id,
                "tenant_id": tenant_id,  # Include tenant ID in request data
                "feature_type": feature_type,
                "preferences": user_preferences,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Get tenant-specific configuration if available
            if tenant_id:
                # Get tenant-specific template overrides
                tenant_template_config = None
                try:
                    config_key = f"features/{feature_type}/template_config"
                    all_tenant_configs = await self.config_db_client.get_config_for_all_tenants(config_key)
                    tenant_template_config = all_tenant_configs.get(tenant_id)
                except Exception as e:
                    self.logger.warning(f"Error getting tenant template config: {str(e)}")
                
                # Add tenant template configuration to request if available
                if tenant_template_config:
                    request_data["tenant_template_config"] = tenant_template_config
            
            # Track this request in batch
            if "requests" not in self.active_batches[batch_id]:
                self.active_batches[batch_id]["requests"] = {}
                
            self.active_batches[batch_id]["requests"][request_id] = {
                "user_id": user_id,
                "tenant_id": tenant_id,  # Track tenant ID in batch
                "status": "processing"
            }
            
            # Process request through context manager
            if self.context_manager:
                # Use context manager API to create service context
                context_id = await self.context_manager.create_service_context(
                    request_data=request_data,
                    template_id=template_id,
                    service_type="preference_processor", 
                    source="batch_processor",
                    parent_id=batch_id
                )
                
                if not context_id:
                    self.logger.error(f"Failed to create context for user {user_id}")
                    self.active_batches[batch_id]["requests"][request_id]["status"] = "failed"
                    self.active_batches[batch_id]["requests"][request_id]["error"] = "Context creation failed"
                    return {"success": False, "error": "Failed to create context"}
                    
                # Update tracking
                self.active_batches[batch_id]["requests"][request_id]["context_id"] = context_id
                self.active_batches[batch_id]["requests"][request_id]["status"] = "submitted"
                
                return {"success": True, "context_id": context_id}
                
            else:
                # Fallback to request service
                self.logger.warning("Context manager not available, using request service directly")
                
                # Create a request object
                request = Request(id=request_id)
                request.purpose_id = template_id
                request.parameters = request_data
                
                # Process through request service
                result = await self.request_service.process_request(request)
                
                # Update tracking
                if result:
                    self.active_batches[batch_id]["requests"][request_id]["status"] = "completed"
                    return {"success": True, "request_id": request_id}
                else:
                    self.active_batches[batch_id]["requests"][request_id]["status"] = "failed"
                    return {"success": False, "error": "Request processing failed"}
                    
        except Exception as e:
            self.logger.error(f"Error processing user {user_id} with preferences: {str(e)}")
            
            # Update tracking if possible
            if batch_id in self.active_batches and "requests" in self.active_batches[batch_id]:
                request_id = f"pref_{feature_type}_{user_id}"
                if request_id in self.active_batches[batch_id]["requests"]:
                    self.active_batches[batch_id]["requests"][request_id]["status"] = "failed"
                    self.active_batches[batch_id]["requests"][request_id]["error"] = str(e)
                    
            return {"success": False, "error": str(e)}
    
    def _get_template_for_feature(self, feature_type: str) -> str:
        """
        Get the template ID for a specific feature type.
        
        Args:
            feature_type: Feature type
            
        Returns:
            Template ID for the feature
        """
        # This would normally be defined in a configuration
        # Here we just use a simple mapping
        templates = {
            "instagram_posts": "instagram_post_generator",
            "etsy_analysis": "etsy_product_analyzer",
            "niche_research": "niche_trend_analyzer"
        }
        return templates.get(feature_type, "generic_template")

    async def get_batch_results_by_tenant(self, batch_id: str) -> Dict[str, Any]:
        """
        Get batch results summarized by tenant.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            Dictionary with tenant-specific summaries
        """
        if batch_id not in self.active_batches:
            return {"status": "not_found", "error": f"Batch {batch_id} not found"}
            
        batch_info = self.active_batches[batch_id]
        
        # If this is not a preference-based batch, return regular status
        if batch_info.get("type") != "preference_batch":
            return {"status": batch_info["status"], "message": "Not a preference-based batch"}
            
        requests = batch_info.get("requests", {})
        if not requests:
            return {
                "status": batch_info["status"],
                "message": "No requests found in batch"
            }
            
        # Organize results by tenant
        tenant_summaries = {}
        
        for request_id, request_info in requests.items():
            tenant_id = request_info.get("tenant_id", "unknown")
            
            if tenant_id not in tenant_summaries:
                tenant_summaries[tenant_id] = {
                    "processed": 0,
                    "succeeded": 0,
                    "failed": 0,
                    "user_count": 0
                }
                
            # Update counts
            tenant_summaries[tenant_id]["user_count"] += 1
            
            status = request_info.get("status")
            if status in ["completed", "submitted"]:
                tenant_summaries[tenant_id]["succeeded"] += 1
                tenant_summaries[tenant_id]["processed"] += 1
            elif status == "failed":
                tenant_summaries[tenant_id]["failed"] += 1
                tenant_summaries[tenant_id]["processed"] += 1
            else:
                # Still in progress or unknown
                tenant_summaries[tenant_id]["processed"] += 1
                
        # Add processing percentages for each tenant
        for tenant_id, summary in tenant_summaries.items():
            user_count = summary["user_count"]
            if user_count > 0:
                summary["success_rate"] = round((summary["succeeded"] / user_count) * 100, 2)
                summary["failure_rate"] = round((summary["failed"] / user_count) * 100, 2)
                summary["completion_rate"] = round((summary["processed"] / user_count) * 100, 2)
            else:
                summary["success_rate"] = 0
                summary["failure_rate"] = 0
                summary["completion_rate"] = 0
                
        return {
            "status": batch_info["status"],
            "batch_id": batch_id,
            "feature_type": batch_info.get("feature_type"),
            "frequency": batch_info.get("frequency"),
            "time_key": batch_info.get("time_key"),
            "total_tenants": len(tenant_summaries),
            "tenant_summaries": tenant_summaries,
            "created_at": batch_info.get("created_at"),
            "completed_at": batch_info.get("completed_at")
        }
    
    def _load_batch_configs(self):
        """Load batch configurations from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.batch_configs = config_data.get('batch_processing_jobs', {})
                    self.logger.info(f"Loaded {len(self.batch_configs)} batch configurations")
            else:
                self.logger.warning(f"Batch config file not found: {self.config_file}")
                self.batch_configs = {}
        except Exception as e:
            self.logger.error(f"Error loading batch configs: {str(e)}")
            self.batch_configs = {}