"""
Context Manager for handling context workflows based on rules.

Manages the lifecycle of contexts, applies conditions based on status tags,
routes completed contexts to the output manager, and handles context cleanup.
"""
import json
import os
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from src.utils.id_utils import generate_request_id
from src.infrastructure.repositories.task_repository_adapter import TaskRepositoryAdapter
from src.config.task_repository_config import COMPLETED_CONTEXT_TTL, FAILED_CONTEXT_TTL
from src.domain.value_objects.batch_type import ProcessingMethod, DataSourceType
from src.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Context Manager is responsible for coordinating context workflows based on rules.
    
    Responsibilities:
    - Coordinating context workflows based on rules
    - Processing contexts based on their status tags
    - Routing completed contexts to output manager
    - Managing conditions and rules for context processing
    - Periodic cleanup of old contexts
    - Supporting batch processing with the 2x2 matrix model
    - Supporting preference-based batch processing
    
    This implementation uses TaskRepositoryAdapter to interact with the centralized
    task-repo-service in the database layer, ensuring consistent task management
    across microservices.
    """
    
    def __init__(self, 
                 repository: TaskRepositoryAdapter,
                 output_manager = None,
                 conditions_path: str = "data/context/context_conditions.json",
                 cleanup_interval_hours: int = 24,
                 user_repository = None):
        """
        Initialize Context Manager.
        
        Args:
            repository: Task repository adapter for connecting to task-repo-service in database layer
            output_manager: Output manager for handling completed contexts
            conditions_path: Path to context conditions JSON file
            cleanup_interval_hours: Interval for automatic context cleanup in hours
            user_repository: Repository for user data
        """
        self.repository = repository
        self.output_manager = output_manager
        self.conditions_path = conditions_path
        self.conditions = {}
        
        # Cleanup task attributes
        self.cleanup_interval_seconds = cleanup_interval_hours * 3600
        self.cleanup_running = False
        self.cleanup_task = None
        
        # Promotion task attributes
        self.promotion_running = False
        self.promotion_task = None
        
        # User repository for validating users
        self.user_repository = user_repository
        
        self._load_conditions()
        
        self.logger = logging.getLogger(__name__)
        
    def _load_conditions(self) -> None:
        """Load conditions from conditions file."""
        try:
            if os.path.exists(self.conditions_path):
                with open(self.conditions_path, 'r') as file:
                    self.conditions = json.load(file)
                    logger.info(f"Loaded context conditions from {self.conditions_path}")
            else:
                logger.warning(f"Conditions file not found at {self.conditions_path}, using defaults")
                # Create default conditions
                self.conditions = {
                    "status": {
                        "completed": {
                            "action": "route_to_output",
                            "delete_after": 86400  # 24 hours in seconds
                        },
                        "failed": {
                            "action": "log_error",
                            "delete_after": 604800  # 7 days in seconds
                        }
                    }
                }
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.conditions_path), exist_ok=True)
                # Save default conditions
                with open(self.conditions_path, 'w') as file:
                    json.dump(self.conditions, file, indent=2)
                    logger.info(f"Created default conditions file at {self.conditions_path}")
        except Exception as e:
            logger.error(f"Error loading conditions: {str(e)}")
            # Use empty conditions if loading fails
            self.conditions = {}
            
    async def reload_conditions(self) -> bool:
        """
        Reload conditions from the conditions file.
        
        Returns:
            Success status
        """
        try:
            self._load_conditions()
            return True
        except Exception as e:
            logger.error(f"Error reloading conditions: {str(e)}")
            return False
    
    async def create_context(
            self, 
            request_data: Dict[str, Any], 
            template_data: Dict[str, Any],
            source: str = "api",
            parent_id: Optional[str] = None
        ) -> Optional[str]:
        """
        Create a new context.
        
        Args:
            request_data: Request data including text and metadata
            template_data: Template data including ID and parameters
            source: Source identifier for the request
            parent_id: Optional parent context ID for batch processing
            
        Returns:
            Context ID if successful, None otherwise
        """
        try:
            # Generate context ID
            context_id = generate_request_id(source=source)
            
            # Create context document
            context = {
                "_id": context_id,
                "request": request_data,
                "template_data": template_data,
                "template_id": template_data.get("id"),
                "status": "created",
                "source": source,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add parent ID if provided (for batch processing)
            if parent_id:
                context["parent_id"] = parent_id
                
            # Save context to repository
            success = await self.repository.save(context_id, context)
            
            if success:
                logger.info(f"Created context {context_id} from {source}")
                return context_id
            else:
                logger.error(f"Failed to create context")
                return None
                
        except Exception as e:
            logger.error(f"Error creating context: {str(e)}")
            return None
    
    async def create_service_context(
            self, 
            request_data: Dict[str, Any], 
            template_id: str = None,
            service_type: str = None,
            source: str = "api",
            parent_id: Optional[str] = None,
            priority: Optional[int] = None
        ) -> Optional[str]:
        """
        Create a context ready for service processing.
        
        Creates a context with 'pending' status, properly tagged with service type,
        ready for direct pickup by service workers.
        
        Args:
            request_data: Request data including text and metadata
            template_id: ID of the template to use
            service_type: Type of service (e.g., "GENERATIVE", "ANALYSIS", "COMMUNICATION")
            source: Source identifier for the request
            parent_id: Optional parent context ID for batch processing
            priority: Priority level (1-10, lower number = higher priority, default 5)
            
        Returns:
            Context ID if successful, None otherwise
        """
        try:
            # Validate user if user repository is available
            user_id = request_data.get("user_id")
            if self.user_repository and user_id:
                user_exists = await self.user_repository.validate_user_exists(user_id)
                if not user_exists:
                    logger.warning(f"User {user_id} does not exist in system_users database")
                    return None
            
            # Generate context ID
            context_id = generate_request_id(source=source)
            
            # Assign priority (default is 5)
            assigned_priority = 5
            if priority is not None:
                if 1 <= priority <= 10:
                    assigned_priority = priority
                else:
                    logger.warning(f"Invalid priority {priority}, using default (5)")
            
            # Create template data structure
            template_data = {
                "id": template_id,
                "service_type": service_type
            }
            
            # Create context document
            context = {
                "_id": context_id,
                "request": request_data,
                "template": template_data,
                "template_id": template_id,
                "status": "pending",
                "service_type": service_type,
                "source": source,
                "priority": assigned_priority,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tags": [service_type.lower() if service_type else "unknown"]
            }
            
            # Add user_id to tags if available
            if user_id:
                context["tags"].append(f"user:{user_id}")
            
            # Add parent ID if provided (for batch processing)
            if parent_id:
                context["parent_id"] = parent_id
                
            # Save context to repository
            success = await self.repository.save(context_id, context)
            
            if success:
                logger.info(f"Created service context {context_id} for service type {service_type}")
                return context_id
            else:
                logger.error(f"Failed to create service context")
                return None
                
        except Exception as e:
            logger.error(f"Error creating service context: {str(e)}")
            return None
            
    async def create_batch_context(
            self, 
            batch_id: str, 
            batch_type: Dict[str, Any],
            purpose_id: Optional[str] = None,
            item_count: int = 0,
            metadata: Optional[Dict[str, Any]] = None,
            valid_items: Optional[List[str]] = None,
            invalid_items: Optional[List[str]] = None
        ) -> Optional[str]:
        """
        Create a context specifically for batch processing with enhanced tracking.
        
        This method creates a context with batch-specific metadata that clearly
        represents both dimensions of the batch processing matrix:
        - Processing method: INDIVIDUAL vs BATCH
        - Data source type: USERS vs CATEGORIES
        
        The improved format tracks valid and invalid items (users or categories)
        for better monitoring and debugging.
        
        Args:
            batch_id: Unique batch identifier
            batch_type: Dictionary containing processing_method and data_source_type
            purpose_id: Optional purpose identifier for analytics
            item_count: Number of items in the batch
            metadata: Additional batch metadata
            valid_items: List of valid item IDs (user_ids or category_ids)
            invalid_items: List of invalid item IDs
            
        Returns:
            Context ID if successful, None otherwise
        """
        try:
            # Validate and extract batch type components
            processing_method = batch_type.get("processing_method")
            data_source_type = batch_type.get("data_source_type")
            
            if not processing_method or not data_source_type:
                logger.error(f"Invalid batch type provided for batch {batch_id}")
                return None
                
            # Generate context ID using batch ID for traceability
            context_id = f"batch_{batch_id}_{int(time.time())}"
            
            # Base request data
            request_data = {
                "id": batch_id,
                "type": "batch",
                "item_count": item_count,
                "purpose_id": purpose_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Template data for the batch
            template_data = {
                "id": f"template_for_{batch_id}",
                "service_type": "batch",
                "version": "1.0",
                "parameters": {}
            }
            
            # Prepare validation statistics
            valid_count = len(valid_items) if valid_items else 0
            invalid_count = len(invalid_items) if invalid_items else 0
            total_validated = valid_count + invalid_count
            
            # Create context document with explicit matrix model metadata
            context = {
                "_id": context_id,
                "request": request_data,
                "template_data": template_data,
                "template_id": template_data.get("id"),
                "status": "initializing",
                "source": "batch_processor",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tags": ["batch"],
                "batch": {
                    "id": batch_id,
                    "processing_method": processing_method,
                    "data_source_type": data_source_type,
                    "item_count": item_count
                },
                "results": {
                    "metadata": metadata or {},
                    "items": {},
                    "progress": {
                        "processed": 0,
                        "succeeded": 0,
                        "failed": 0,
                        "total": item_count,
                        "percentage": 0
                    },
                    "validation": {
                        "total": total_validated,
                        "valid": valid_count,
                        "invalid": invalid_count
                    }
                }
            }
            
            # Add validation item lists if provided
            if valid_items or invalid_items:
                # Determine field name based on data source type
                if data_source_type.lower() == "users":
                    item_field = "users"
                else:
                    item_field = "categories"
                    
                # Add valid and invalid items to results
                context["results"]["items"] = {
                    f"valid_{item_field}": valid_items or [],
                    f"invalid_{item_field}": invalid_items or []
                }
                
            # Add batch-specific information to context tags
            context["tags"].append(f"processing_method:{processing_method}")
            context["tags"].append(f"data_source:{data_source_type}")
            
            # Add purpose ID to tags if provided
            if purpose_id:
                context["tags"].append(f"purpose:{purpose_id}")
                
            # Save context to repository
            success = await self.repository.save(context_id, context)
            
            if success:
                logger.info(
                    f"Created batch context {context_id} for batch {batch_id} "
                    f"({processing_method}/{data_source_type}) with {item_count} items "
                    f"(valid: {valid_count}, invalid: {invalid_count})"
                )
                return context_id
            else:
                logger.error(f"Failed to create batch context for {batch_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating batch context: {str(e)}")
            return None
    
    async def update_batch_progress(
            self, 
            batch_context_id: str, 
            processed: int = 0,
            succeeded: int = 0,
            failed: int = 0,
            total: Optional[int] = None
        ) -> bool:
        """
        Update batch progress in the context.
        
        This method updates the progress tracking information for a batch context.
        
        Args:
            batch_context_id: Batch context ID to update
            processed: Number of items processed so far
            succeeded: Number of items processed successfully
            failed: Number of items that failed processing
            total: Optional total number of items (uses existing total if not provided)
            
        Returns:
            Success flag
        """
        try:
            # Get the current context
            context = await self.repository.get(batch_context_id)
            if not context:
                logger.error(f"Batch context {batch_context_id} not found")
                return False
                
            # Ensure results structure exists
            if "results" not in context:
                context["results"] = {}
            if "progress" not in context["results"]:
                context["results"]["progress"] = {}
                
            # Update progress with provided values
            progress = context["results"]["progress"]
            progress["processed"] = processed
            progress["succeeded"] = succeeded
            progress["failed"] = failed
            
            # Use provided total or existing total
            if total is not None:
                progress["total"] = total
            elif "total" not in progress:
                progress["total"] = processed
                
            # Calculate percentage
            if progress["total"] > 0:
                progress["percentage"] = int((processed / progress["total"]) * 100)
            else:
                progress["percentage"] = 0
                
            # Update timestamp
            context["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated context
            success = await self.repository.save(batch_context_id, context)
            
            if success:
                logger.debug(
                    f"Updated batch context {batch_context_id} progress: "
                    f"{processed}/{progress['total']} ({progress['percentage']}%)"
                )
            else:
                logger.error(f"Failed to update batch context {batch_context_id}")
                
            return success
                
        except Exception as e:
            logger.error(f"Error updating batch progress: {str(e)}")
            return False
    
    async def update_batch_status(self, batch_context_id: str, status: str) -> bool:
        """
        Update batch status in the context.
        
        Args:
            batch_context_id: Batch context ID to update
            status: New status value
            
        Returns:
            Success flag
        """
        try:
            # Get the current context
            context = await self.repository.get(batch_context_id)
            if not context:
                logger.error(f"Batch context {batch_context_id} not found")
                return False
                
            # Update status
            context["status"] = status
            
            # Update timestamp
            context["updated_at"] = datetime.utcnow().isoformat()
            
            # If status is 'completed' or 'failed', add completion time
            if status in ["completed", "failed", "partial"]:
                context["completed_at"] = datetime.utcnow().isoformat()
                
            # Save updated context
            success = await self.repository.save(batch_context_id, context)
            
            if success:
                logger.info(f"Updated batch context {batch_context_id} status to {status}")
                
                # Process status conditions for the new status
                await self._process_status_conditions(batch_context_id, status, context)
            else:
                logger.error(f"Failed to update batch context {batch_context_id}")
                
            return success
                
        except Exception as e:
            logger.error(f"Error updating batch status: {str(e)}")
            return False
            
    async def add_batch_item_result(
            self, 
            batch_context_id: str, 
            item_id: str, 
            result: Dict[str, Any]
        ) -> bool:
        """
        Add result for a batch item to the batch context.
        
        Args:
            batch_context_id: Batch context ID to update
            item_id: ID of the item to update
            result: Result data for the item
            
        Returns:
            Success flag
        """
        try:
            # Get the current context
            context = await self.repository.get(batch_context_id)
            if not context:
                logger.error(f"Batch context {batch_context_id} not found")
                return False
                
            # Ensure results structure exists
            if "results" not in context:
                context["results"] = {}
            if "items" not in context["results"]:
                context["results"]["items"] = {}
                
            # Add item result
            context["results"]["items"][item_id] = result
            
            # Update timestamp
            context["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated context
            success = await self.repository.save(batch_context_id, context)
            
            if success:
                logger.debug(f"Added result for item {item_id} to batch context {batch_context_id}")
            else:
                logger.error(f"Failed to update batch context {batch_context_id}")
                
            return success
                
        except Exception as e:
            logger.error(f"Error adding batch item result: {str(e)}")
            return False
    
    async def get_batch_context_by_batch_id(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a batch context by its batch ID.
        
        Args:
            batch_id: Batch ID to find
            
        Returns:
            Batch context if found, None otherwise
        """
        try:
            # Find context with matching batch ID in request data
            batch_contexts = await self.repository.find({"request.id": batch_id, "tags": "batch"}, limit=1)
            
            if batch_contexts and len(batch_contexts) > 0:
                return batch_contexts[0]
            
            return None
                
        except Exception as e:
            logger.error(f"Error finding batch context for batch {batch_id}: {str(e)}")
            return None
    
    async def get_batch_context_summary(self, batch_id: str) -> Dict[str, Any]:
        """
        Get a summary of batch context status and progress.
        
        Args:
            batch_id: Batch ID to summarize
            
        Returns:
            Summary information including status and progress
        """
        try:
            # Find the batch context
            batch_context = await self.get_batch_context_by_batch_id(batch_id)
            
            if not batch_context:
                return {"status": "not_found", "error": f"Batch {batch_id} not found"}
                
            # Extract summary information
            summary = {
                "batch_id": batch_id,
                "status": batch_context.get("status", "unknown"),
                "created_at": batch_context.get("created_at"),
                "updated_at": batch_context.get("updated_at")
            }
            
            # Add completion time if available
            if "completed_at" in batch_context:
                summary["completed_at"] = batch_context["completed_at"]
                
            # Add batch type information
            if "batch" in batch_context:
                batch_info = batch_context["batch"]
                summary["processing_method"] = batch_info.get("processing_method")
                summary["data_source_type"] = batch_info.get("data_source_type")
                summary["item_count"] = batch_info.get("item_count", 0)
                
            # Add progress information
            if "results" in batch_context and "progress" in batch_context["results"]:
                summary["progress"] = batch_context["results"]["progress"]
                
            # Add result metadata if available
            if "results" in batch_context and "metadata" in batch_context["results"]:
                summary["metadata"] = batch_context["results"]["metadata"]
                
            return summary
                
        except Exception as e:
            logger.error(f"Error getting batch context summary for {batch_id}: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def update_status(self, context_id: str, status: str) -> bool:
        """
        Update status for a context and process associated conditions.
        
        Args:
            context_id: Context ID
            status: New status value
            
        Returns:
            Success status
        """
        try:
            # Get current context
            context = await self.repository.get(context_id)
            if not context:
                logger.warning(f"Context {context_id} not found for status update")
                return False
                
            # Update status
            context["status"] = status
            context["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated context
            success = await self.repository.save(context_id, context)
            
            if success:
                # Process conditions for the new status
                await self._process_status_conditions(context_id, status, context)
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating status for context {context_id}: {str(e)}")
            return False
            
    async def _process_status_conditions(self, context_id: str, status: str, context: Dict[str, Any]) -> None:
        """
        Process conditions for a specific status.
        
        Args:
            context_id: Context ID
            status: Context status
            context: Current context data
        """
        try:
            # Check if we have conditions for this status
            if "status" not in self.conditions or status not in self.conditions["status"]:
                logger.debug(f"No conditions for status '{status}'")
                return
                
            # Get conditions for this status
            status_conditions = self.conditions["status"][status]
            
            # Process each action
            if "action" in status_conditions:
                action = status_conditions["action"]
                
                # Route to output manager if status is completed
                if action == "route_to_output" and status == "completed":
                    if self.output_manager:
                        # Pass to output manager
                        asyncio.create_task(self.output_manager.process_output(context_id, context))
                        logger.info(f"Routed completed context {context_id} to output manager")
                    else:
                        logger.warning(f"Output manager not available for completed context {context_id}")
                
                # Log error if status is failed
                elif action == "log_error" and status == "failed":
                    error_info = context.get("results", {}).get("error", "Unknown error")
                    logger.error(f"Context {context_id} failed: {error_info}")
                    
        except Exception as e:
            logger.error(f"Error processing status conditions for context {context_id}: {str(e)}")
            
    async def process_pending_contexts(self) -> int:
        """
        Process any pending contexts based on their status.
        
        Returns:
            Number of contexts processed
        """
        try:
            # Find contexts with pending status
            pending_contexts = await self.repository.find_by_status("pending", 50)
            processed_count = 0
            
            for context in pending_contexts:
                # Process each pending context based on conditions
                context_id = context.get("_id")
                if context_id:
                    await self._process_status_conditions(context_id, "pending", context)
                    processed_count += 1
                    
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing pending contexts: {str(e)}")
            return 0
    
    # Context cleanup methods
    
    async def start_cleanup_task(self):
        """Start the periodic context cleanup task."""
        if self.cleanup_running:
            logger.warning("Context cleanup task is already running")
            return
            
        self.cleanup_running = True
        self.cleanup_task = asyncio.create_task(self._run_periodic_cleanup())
        logger.info(f"Started context cleanup task (interval: {self.cleanup_interval_seconds} seconds)")
    
    async def stop_cleanup_task(self):
        """Stop the context cleanup task."""
        if not self.cleanup_running:
            return
            
        self.cleanup_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
            
        logger.info("Stopped context cleanup task")
    
    async def _run_periodic_cleanup(self):
        """Run the cleanup task periodically."""
        while self.cleanup_running:
            try:
                # Run the cleanup
                await self._cleanup_old_contexts()
                
                # Sleep until next cleanup
                await asyncio.sleep(self.cleanup_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in context cleanup task: {str(e)}")
                # Sleep for a while before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    async def _cleanup_old_contexts(self):
        """Clean up old contexts."""
        try:
            start_time = time.time()
            logger.info("Starting context cleanup")
            
            # Delete completed contexts older than the TTL
            completed_days = COMPLETED_CONTEXT_TTL // 86400  # Convert seconds to days
            completed_count = await self.repository.delete_old_contexts(completed_days)
            
            # The task repository handles the cleanup of both completed and failed tasks
            
            duration = time.time() - start_time
            logger.info(f"Completed context cleanup in {duration:.2f}s. Deleted {completed_count} contexts")
            
        except Exception as e:
            logger.error(f"Error cleaning up old contexts: {str(e)}")
    
    async def run_manual_cleanup(self, days: int = 30) -> int:
        """
        Run a manual cleanup of old contexts.
        
        Args:
            days: Number of days to keep contexts
            
        Returns:
            Number of deleted contexts
        """
        try:
            logger.info(f"Running manual cleanup of contexts older than {days} days")
            
            # Delete old contexts
            deleted_count = await self.repository.delete_old_contexts(days)
            
            logger.info(f"Manual cleanup completed. Deleted {deleted_count} contexts")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error in manual context cleanup: {str(e)}")
            return 0

    async def promote_waiting_contexts(self, max_wait_time_minutes: int = 30) -> int:
        """
        Increase priority of contexts that have been waiting too long.
        
        This prevents starvation of lower priority contexts by gradually
        increasing their priority based on wait time.
        
        Args:
            max_wait_time_minutes: Maximum wait time before reaching top priority
            
        Returns:
            Number of contexts promoted
        """
        try:
            # Calculate cutoff time for various priority promotions
            now = datetime.utcnow()
            
            # Staggered promotion times - older contexts get higher priority boosts
            time_thresholds = {
                8: now - timedelta(minutes=max_wait_time_minutes // 5),     # After 6 minutes, to priority 8
                6: now - timedelta(minutes=max_wait_time_minutes // 3),     # After 10 minutes, to priority 6
                4: now - timedelta(minutes=max_wait_time_minutes // 2),     # After 15 minutes, to priority 4
                2: now - timedelta(minutes=max_wait_time_minutes // 1.5),   # After 20 minutes, to priority 2
                1: now - timedelta(minutes=max_wait_time_minutes)           # After 30 minutes, to priority 1
            }
            
            promotion_count = 0
            
            # Since we're using TaskRepositoryAdapter, we need to:
            # 1. Find eligible contexts
            # 2. Update them one by one
            for new_priority, time_threshold in time_thresholds.items():
                # For each priority level
                time_threshold_str = time_threshold.isoformat()
                
                # Get pending contexts 
                pending_contexts = await self.repository.find_by_status("pending", 100)
                
                # Filter manually for eligible contexts
                for context in pending_contexts:
                    context_id = context.get("_id")
                    created_at = context.get("created_at")
                    current_priority = context.get("priority", 5)
                    
                    # Check if eligible for promotion
                    if (created_at and created_at < time_threshold_str and 
                            current_priority > new_priority):
                        
                        # Update priority
                        context["priority"] = new_priority
                        context["priority_promoted"] = True
                        context["priority_promoted_at"] = now.isoformat()
                        context["priority_reason"] = f"Wait time exceeded {max_wait_time_minutes // (new_priority * 2 or 1)} minutes"
                        
                        # Save updated context
                        success = await self.repository.save(context_id, context)
                        if success:
                            promotion_count += 1
            
            if promotion_count > 0:
                logger.info(f"Promoted {promotion_count} waiting contexts to prevent starvation")
                
            return promotion_count
                
        except Exception as e:
            logger.error(f"Error promoting waiting contexts: {str(e)}")
            return 0

    async def start_promotion_task(self, interval_seconds: int = 60, max_wait_time_minutes: int = 30):
        """Start the periodic task for promoting waiting contexts.
        
        Args:
            interval_seconds: How often to run the promotion task (seconds)
            max_wait_time_minutes: Maximum wait time before reaching top priority
        """
        if hasattr(self, 'promotion_running') and self.promotion_running:
            logger.warning("Context promotion task is already running")
            return
            
        self.promotion_running = True
        self.promotion_task = asyncio.create_task(
            self._run_periodic_promotion(interval_seconds, max_wait_time_minutes)
        )
        logger.info(f"Started context promotion task (interval: {interval_seconds}s)")
        
    async def stop_promotion_task(self):
        """Stop the context promotion task."""
        if not hasattr(self, 'promotion_running') or not self.promotion_running:
            return
            
        self.promotion_running = False
        if hasattr(self, 'promotion_task') and self.promotion_task:
            self.promotion_task.cancel()
            try:
                await self.promotion_task
            except asyncio.CancelledError:
                pass
            self.promotion_task = None
            
        logger.info("Stopped context promotion task")
        
    async def _run_periodic_promotion(self, interval_seconds: int, max_wait_time_minutes: int):
        """Run the promotion task periodically."""
        while self.promotion_running:
            try:
                # Promote waiting contexts
                await self.promote_waiting_contexts(max_wait_time_minutes)
                
                # Sleep until next promotion
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in context promotion task: {str(e)}")
                # Sleep for a while before retrying
                await asyncio.sleep(10)

    async def create_preference_batch_context(
            self, 
            batch_id: str, 
            feature_type: str,
            frequency: str,
            time_key: str,
            user_count: int = 0,
            metadata: Optional[Dict[str, Any]] = None
        ) -> Optional[str]:
        """
        Create a context specifically for preference-based batch processing.
        
        This method creates a specialized batch context that includes user preference metadata
        and follows the preference-based processing model.
        
        Args:
            batch_id: Unique batch identifier
            feature_type: Type of feature (e.g., "instagram_posts")
            frequency: Frequency of processing ("daily", "weekly", etc.)
            time_key: Time key for the processing schedule
            user_count: Number of users in the batch
            metadata: Additional batch metadata
            
        Returns:
            Context ID if successful, None otherwise
        """
        try:
            # Generate context ID using batch ID for traceability
            context_id = f"pref_batch_{batch_id}_{int(time.time())}"
            
            # Base request data
            request_data = {
                "id": batch_id,
                "type": "preference_batch",
                "feature_type": feature_type,
                "frequency": frequency,
                "time_key": time_key,
                "user_count": user_count,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Template data for the batch
            template_data = {
                "id": f"template_for_{feature_type}",
                "service_type": "preference_batch",
                "version": "1.0",
                "parameters": {
                    "feature_type": feature_type,
                    "frequency": frequency,
                    "time_key": time_key
                }
            }
            
            # Create context document for preference-based batch
            context = {
                "_id": context_id,
                "request": request_data,
                "template_data": template_data,
                "template_id": template_data.get("id"),
                "status": "initializing",
                "source": "preference_batch_processor",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tags": ["batch", "preference_based", f"feature:{feature_type}", f"frequency:{frequency}"],
                "batch": {
                    "id": batch_id,
                    "processing_method": ProcessingMethod.INDIVIDUAL.value,
                    "data_source_type": DataSourceType.USERS.value,
                    "feature_type": feature_type,
                    "frequency": frequency,
                    "time_key": time_key,
                    "user_count": user_count
                },
                "results": {
                    "metadata": metadata or {},
                    "items": {},
                    "progress": {
                        "processed": 0,
                        "succeeded": 0,
                        "failed": 0,
                        "total": user_count,
                        "percentage": 0
                    }
                }
            }
                
            # Save context to repository
            success = await self.repository.save(context_id, context)
            
            if success:
                logger.info(
                    f"Created preference batch context {context_id} for batch {batch_id} "
                    f"({feature_type}/{frequency}/{time_key}) with {user_count} users"
                )
                return context_id
            else:
                logger.error(f"Failed to create preference batch context for {batch_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating preference batch context: {str(e)}")
            return None

    async def create_user_preference_context(
            self,
            batch_context_id: str,
            user_id: str,
            tenant_id: Optional[str],
            feature_type: str,
            user_preferences: Dict[str, Any],
            template_id: str
        ) -> Optional[str]:
        """
        Create a context for processing a single user with preferences.
        
        This method creates a context for an individual user within a preference-based batch,
        including their specific preferences for customized processing.
        
        Args:
            batch_context_id: Parent batch context ID
            user_id: User ID to process
            tenant_id: Tenant ID for the user
            feature_type: Type of feature being processed
            user_preferences: User-specific preferences
            template_id: Template ID to use for processing
            
        Returns:
            Context ID if successful, None otherwise
        """
        try:
            # Generate context ID
            context_id = generate_request_id(source=f"pref_{feature_type}")
            
            # Create request data
            request_data = {
                "id": context_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "feature_type": feature_type,
                "preferences": user_preferences,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Get template data
            template_data = {
                "id": template_id,
                "version": "1.0",
                "parameters": {
                    # Apply any template overrides from preferences
                    **(user_preferences.get("template_overrides", {}))
                }
            }
            
            # Create context
            context = {
                "_id": context_id,
                "request": request_data,
                "template_data": template_data,
                "template_id": template_id,
                "status": "pending",
                "parent_id": batch_context_id,  # Link to parent batch
                "source": "preference_batch",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tags": ["preference", feature_type]
            }
            
            # Add tenant tag if available
            if tenant_id:
                context["tags"].append(f"tenant:{tenant_id}")
                
            # Save context to repository
            success = await self.repository.save(context_id, context)
            
            if success:
                logger.info(f"Created user preference context {context_id} for user {user_id} ({feature_type})")
                return context_id
            else:
                logger.error(f"Failed to create user preference context for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating user preference context: {str(e)}")
            return None