"""
Worker Service Module

This module provides the worker service for processing campaign conversations.
Workers handle the execution of conversation flows, managing progression through
stages, and performing necessary actions for each conversation.
"""

import asyncio
import time
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set

from src.config.config_manager import get_settings
from src.repository.conversation_state_repository import ConversationStateRepository
from src.service.campaign_manager import CampaignManager
from src.config.monitoring import get_metrics

# Configure logger
logger = structlog.get_logger(__name__)


class WorkerService:
    """
    Worker Service for processing campaign conversations.
    
    This service manages a pool of workers that process conversations from
    campaigns. Workers handle the execution of conversation flows, manage
    progression through stages, and perform necessary actions for each conversation.
    """
    
    def __init__(
        self,
        campaign_manager: CampaignManager,
        conversation_repository: ConversationStateRepository
    ):
        """
        Initialize the worker service.
        
        Args:
            campaign_manager: Campaign manager for conversation processing
            conversation_repository: Repository for conversation state access
        """
        self.campaign_manager = campaign_manager
        self.conversation_repository = conversation_repository
        self.settings = get_settings()
        self.poll_interval_seconds = 5
        self.batch_size = self.settings.batch_size
        self.max_workers = self.settings.worker_count
        self.running = False
        self.active_workers = 0
        self.processing_conversations: Set[str] = set()
        
        # Get metrics client
        self.metrics = get_metrics()
        
        logger.info(
            "Worker service initialized", 
            max_workers=self.max_workers,
            batch_size=self.batch_size,
            poll_interval_seconds=self.poll_interval_seconds
        )
    
    async def initialize(self) -> bool:
        """
        Initialize the worker service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        logger.info("Initializing worker service")
        return True
    
    async def run(self):
        """
        Run the worker service in a continuous loop.
        
        This method polls for pending conversations and processes them using workers.
        """
        logger.info("Starting worker service")
        self.running = True
        
        while self.running:
            try:
                # Get pending conversations
                pending_conversations = await self.get_pending_conversations()
                
                if pending_conversations:
                    logger.info(
                        "Found pending conversations", 
                        count=len(pending_conversations)
                    )
                    
                    # Process conversations with available workers
                    tasks = []
                    for conversation in pending_conversations:
                        # Check if we have available workers
                        if self.active_workers >= self.max_workers:
                            break
                        
                        # Check if conversation is already being processed
                        conversation_id = conversation.get("id")
                        if conversation_id in self.processing_conversations:
                    continue
                
                        # Mark conversation as being processed
                        self.processing_conversations.add(conversation_id)
                        
                        # Increment active workers count
                        self.active_workers += 1
                        
                        # Create task for processing conversation
                        task = asyncio.create_task(
                            self.process_conversation(conversation)
                        )
                        
                        # Add callback to handle task completion
                        task.add_done_callback(
                            lambda t, cid=conversation_id: self.conversation_processed(cid, t)
                        )
                        
                        tasks.append(task)
                
                # Sleep for the poll interval
                await asyncio.sleep(self.poll_interval_seconds)
                
            except Exception as e:
                logger.error(
                    "Error in worker service", 
                    error=str(e)
                )
                
                # Sleep for the poll interval
                await asyncio.sleep(self.poll_interval_seconds)
    
    def conversation_processed(self, conversation_id: str, task: asyncio.Task):
        """
        Handle the completion of a conversation processing task.
        
        Args:
            conversation_id: ID of the processed conversation
            task: The completed task
        """
        # Remove conversation from processing set
        self.processing_conversations.discard(conversation_id)
        
        # Decrement active workers count
        self.active_workers -= 1
        
        # Check for exception in the task
        if task.exception():
            logger.error(
                "Error processing conversation", 
                conversation_id=conversation_id,
                error=str(task.exception())
            )
    
    async def stop(self):
        """Stop the worker service."""
        logger.info("Stopping worker service")
        self.running = False
        
        # Wait for all active workers to complete
        while self.active_workers > 0:
            logger.info(
                "Waiting for active workers to complete", 
                active_workers=self.active_workers
            )
            
            await asyncio.sleep(1)
    
    async def get_pending_conversations(self) -> List[Dict[str, Any]]:
        """
        Get pending conversations for processing.
        
        Returns:
            List of pending conversation states
        """
        try:
            current_time = datetime.utcnow()
            
            # Get conversations that are ready for processing
            # This includes conversations with status 'pending' or 'processing'
            # that have a next_processing_time before the current time
            pending_conversations = await self.conversation_repository.get_pending_conversations(
                limit=self.batch_size,
                current_time=current_time
            )
            
            return pending_conversations
            
        except Exception as e:
            logger.error(
                "Error getting pending conversations", 
                error=str(e)
            )
            
            return []
    
    async def process_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single conversation.
        
        This method performs the actual processing of a conversation, including:
        - Checking if the conversation should progress to the next stage
        - Executing any actions required for the current stage
        - Updating the conversation state
        
        Args:
            conversation: Conversation state to process
            
        Returns:
            Dictionary with processing result
        """
        conversation_id = conversation.get("id")
        campaign_id = conversation.get("campaign_id")
        current_stage = conversation.get("current_stage")
        
        # Record start time for metrics
        start_time = time.time()
        processing_result = None
        
        try:
            logger.info(
                "Processing conversation", 
                conversation_id=conversation_id,
                campaign_id=campaign_id,
                current_stage=current_stage
            )
            
            # Update conversation status to 'processing'
            await self.conversation_repository.update_conversation_status(
                conversation_id, 
                "processing",
                {"processing_started_at": datetime.utcnow().isoformat()}
            )
            
            # Determine what to do with the conversation based on its current stage
            # This will depend on the specific campaign type and stage requirements
            
            # For demonstration purposes, let's check if the conversation should
            # progress to the next stage
            result = await self.campaign_manager.evaluate_stage_progression(
                conversation_id
            )
            
            if result.get("success"):
                # If the conversation progressed to the next stage, get the updated state
                updated_conversation = await self.conversation_repository.get_conversation_state(conversation_id)
                new_stage = updated_conversation.get("current_stage")
                
                logger.info(
                    "Conversation progressed to next stage", 
                    conversation_id=conversation_id,
                    previous_stage=current_stage,
                    new_stage=new_stage
                )
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment(
                        "conversation_progression_total",
                        1,
                        {
                            "from_stage": current_stage,
                            "to_stage": new_stage,
                            "campaign_type": updated_conversation.get("campaign_type", "unknown")
                        }
                    )
                
                # Schedule next processing time based on the new stage
                next_processing_time = datetime.utcnow() + timedelta(minutes=5)  # Default delay
                
                # Update conversation with next processing time
                await self.conversation_repository.update_next_processing_time(
                    conversation_id, 
                    next_processing_time
                )
                
                processing_result = {
                    "success": True,
                    "progressed": True,
                    "previous_stage": current_stage,
                    "current_stage": new_stage,
                    "next_processing_time": next_processing_time.isoformat()
                }
                
            else:
                # If the conversation did not progress, check why
                if result.get("completed", False):
                    # Conversation has completed its flow
                    await self.conversation_repository.update_conversation_status(
                        conversation_id, 
                        "completed",
                        {
                            "completed_at": datetime.utcnow().isoformat(),
                            "final_stage": current_stage
                    }
                )
                
                logger.info(
                        "Conversation completed", 
                        conversation_id=conversation_id,
                        final_stage=current_stage
                    )
                    
                    processing_result = {
                        "success": True,
                        "completed": True,
                        "final_stage": current_stage
                    }
                    
                elif result.get("failed", False):
                    # Conversation has failed
                    await self.conversation_repository.update_conversation_status(
                        conversation_id, 
                        "failed",
                        {
                            "failed_at": datetime.utcnow().isoformat(),
                            "error": result.get("error", "Unknown error")
                        }
                    )
                    
                    logger.error(
                        "Conversation failed", 
                        conversation_id=conversation_id,
                        stage=current_stage,
                        error=result.get("error", "Unknown error")
                    )
                    
                    processing_result = {
                        "success": False,
                        "failed": True,
                        "error": result.get("error", "Unknown error")
                    }
                    
                else:
                    # Conversation needs more time before progressing
                    # Schedule next processing time
                    next_processing_time = datetime.utcnow() + timedelta(minutes=30)  # Longer delay
                    
                    # Update conversation with next processing time
                    await self.conversation_repository.update_next_processing_time(
                        conversation_id, 
                        next_processing_time
                    )
                    
                    # Update conversation status back to 'pending'
                    await self.conversation_repository.update_conversation_status(
                        conversation_id, 
                        "pending"
                    )
        
        logger.info(
                        "Conversation not ready to progress", 
                        conversation_id=conversation_id,
                        stage=current_stage,
                        next_processing_time=next_processing_time.isoformat()
                    )
                    
                    processing_result = {
                        "success": True,
                        "progressed": False,
                        "stage": current_stage,
                        "next_processing_time": next_processing_time.isoformat()
                    }
            
            # Record processing duration for metrics
            processing_duration = time.time() - start_time
            
            if self.metrics:
                self.metrics.observe(
                    "worker_task_duration_seconds",
                    processing_duration,
                    {"task_type": "conversation_processing"}
                )
                
                self.metrics.increment(
                    "worker_tasks_processed_total",
                    1,
                    {
                        "task_type": "conversation_processing",
                        "status": "success"
                    }
                )
            
            return processing_result
            
        except Exception as e:
            # Record error for metrics
            if self.metrics:
                self.metrics.increment(
                    "worker_tasks_processed_total",
                    1,
                    {
                        "task_type": "conversation_processing",
                        "status": "error"
                    }
                )
            
            logger.error(
                "Error processing conversation", 
                conversation_id=conversation_id,
                stage=current_stage,
                error=str(e)
            )
            
            # Update conversation status to reflect the error
            try:
                # Set a longer delay before retrying
                next_processing_time = datetime.utcnow() + timedelta(minutes=60)
                
                # Update conversation with error information
                await self.conversation_repository.update_conversation_state(
                    conversation_id,
                    {
                        "status": "pending",  # Reset to pending for retry
                        "next_processing_time": next_processing_time,
                        "metadata": {
                            "last_error": str(e),
                            "last_error_time": datetime.utcnow().isoformat()
                        }
                    }
                )
                
            except Exception as update_error:
                logger.error(
                    "Error updating conversation after processing error", 
                    conversation_id=conversation_id,
                    error=str(update_error)
                )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_specific_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Process a specific conversation by ID.
        
        This method can be used to manually trigger processing for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to process
        
        Returns:
            Dictionary with processing result
        """
        try:
            # Check if conversation exists
            conversation = await self.conversation_repository.get_conversation_state(conversation_id)
            
            if not conversation:
                return {
                    "success": False,
                    "error": f"Conversation with ID {conversation_id} not found"
                }
            
            # Check if conversation is already being processed
            if conversation_id in self.processing_conversations:
                return {
                    "success": False,
                    "error": f"Conversation {conversation_id} is already being processed"
                }
            
            # Process the conversation
            return await self.process_conversation(conversation)
            
        except Exception as e:
            logger.error(
                "Error processing specific conversation", 
                conversation_id=conversation_id,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e)
            } 