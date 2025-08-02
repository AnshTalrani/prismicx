"""
Campaign Manager Module

This module is responsible for managing campaign-related conversation flows,
stage progression, and conversation state management.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

import structlog

from src.repository.conversation_state_repository import ConversationStateRepository
from src.config.config_manager import ConfigManager
from src.common.monitoring import Metrics, get_metrics

logger = structlog.get_logger(__name__)

class CampaignManager:
    """
    Campaign Manager for managing campaign conversations and state.
    
    This class is responsible for:
    - Initializing and managing campaign conversations
    - Tracking conversation state through campaign stages
    - Evaluating stage progression criteria
    - Collecting campaign metrics
    """
    
    def __init__(
        self, 
        conversation_state_repository: ConversationStateRepository,
        config_manager: Optional[ConfigManager] = None,
        metrics: Optional[Metrics] = None
    ):
        """
        Initialize the campaign manager.
        
        Args:
            conversation_state_repository: Repository for conversation state
            config_manager: Configuration manager
            metrics: Metrics collector
        """
        self.conversation_state_repository = conversation_state_repository
        self.config_manager = config_manager or ConfigManager()
        self.metrics = metrics or get_metrics()
        
        # Register metrics
        self.metrics.register_counter("conversations_initialized", "Number of conversations initialized")
        self.metrics.register_counter("stages_advanced", "Number of conversation stages advanced")
        self.metrics.register_counter("conversations_completed", "Number of conversations completed")
        
        logger.info("Campaign manager initialized")
    
    async def initialize_campaign_conversations(self, campaign_id: str) -> int:
        """
        Initialize conversation states for all recipients in a campaign.
        
        This should be called once when a campaign is first started.
        It creates conversation state records for each recipient.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Number of conversation states initialized
        """
        # Get campaign data
        campaign = await self.conversation_state_repository._db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")
            
        # Get recipients
        recipients = campaign.get("recipients", [])
        if not recipients:
            logger.warning("Campaign has no recipients", campaign_id=campaign_id)
            return 0
        
        # Get campaign type and initial stage
        campaign_type = campaign.get("type", "sales")
        initial_stage = campaign.get("initial_stage", "awareness")
        
        # Get template
        template_id = campaign.get("template_id")
        if not template_id:
            raise ValueError(f"Campaign has no template_id: {campaign_id}")
            
        template = await self.conversation_state_repository._db.templates.find_one({"_id": template_id})
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Get stages for this campaign type
        stages = self._get_stages_for_campaign_type(template, campaign_type)
        
        # Initialize conversation states
        current_time = datetime.utcnow()
        conversations_initialized = 0
        
        for user_id in recipients:
            # Check if conversation state already exists
            existing = await self.conversation_state_repository.get_conversation_state(
                user_id=user_id,
                campaign_id=campaign_id
            )
            
            if existing:
                logger.debug(
                    "Conversation state already exists", 
                    user_id=user_id, 
                    campaign_id=campaign_id
                )
                continue
            
            # Create conversation state
            try:
                conversation_data = {
                    "user_id": user_id,
                    "campaign_id": campaign_id,
                    "campaign_type": campaign_type,
                    "current_stage": initial_stage,
                    "stages": [
                        {
                            "name": initial_stage,
                            "entered_at": current_time,
                            "exited_at": None,
                            "completed": False
                        }
                    ],
                    "message_history": [],
                    "context": {
                        "template_id": template_id,
                        "available_stages": stages
                    },
                    "metrics": {
                        "messages_sent": 0,
                        "messages_received": 0,
                        "stage_progressions": 0
                    },
                    "status": "active",
                    "created_at": current_time,
                    "last_active": current_time
                }
                
                await self.conversation_state_repository.create_conversation_state(conversation_data)
                conversations_initialized += 1
                
            except Exception as e:
                logger.error(
                    "Error initializing conversation state",
                    user_id=user_id,
                    campaign_id=campaign_id,
                    error=str(e)
                )
        
        # Update campaign to mark conversation states as initialized
        await self.conversation_state_repository._db.campaigns.update_one(
            {"_id": campaign_id},
            {"$set": {"conversation_states_initialized": True}}
        )
        
        self.metrics.increment("conversations_initialized", conversations_initialized)
        logger.info(
            "Initialized conversation states for campaign", 
            campaign_id=campaign_id,
            recipient_count=len(recipients),
            initialized_count=conversations_initialized
        )
        
        return conversations_initialized
    
    async def get_pending_conversations(
        self, 
        campaign_id: str,
        stage: Optional[str] = None,
        limit: int = 100,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        Get conversations that are pending processing for a campaign.
        
        This retrieves conversations that are:
        - In the specified stage
        - Active (not completed or failed)
        - Ready for follow-up
        
        Args:
            campaign_id: ID of the campaign
            stage: Optional stage filter
            limit: Maximum number of conversations to retrieve
            status: Status filter (active, completed, failed)
            
        Returns:
            List of conversation state documents
        """
        query = {
            "campaign_id": campaign_id,
            "status": status
        }
        
        if stage:
            query["current_stage"] = stage
        
        # Get conversations
        conversations = await self.conversation_state_repository.find_conversation_states(
            query,
            limit=limit,
            sort=[("last_active", 1)]
        )
            
        logger.info(
            "Retrieved pending conversations",
            campaign_id=campaign_id,
            stage=stage, 
            count=len(conversations)
        )
        
        return conversations
    
    async def evaluate_stage_progression(
        self, 
        conversation_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate whether a conversation should progress to the next stage.
        
        Args:
            conversation_id: ID of the conversation state
            
        Returns:
            Tuple of (should_progress, next_stage)
        """
        # Get conversation state
        conversation = await self.conversation_state_repository.get_conversation_state_by_id(conversation_id)
        if not conversation:
            logger.warning("Conversation not found", conversation_id=conversation_id)
            return False, None
        
        # Get campaign
        campaign_id = conversation.get("campaign_id")
        campaign = await self.conversation_state_repository._db.campaigns.find_one({"_id": campaign_id})
        if not campaign:
            logger.warning("Campaign not found", campaign_id=campaign_id)
            return False, None
        
        # Get template
        template_id = campaign.get("template_id") or conversation.get("context", {}).get("template_id")
        if not template_id:
            logger.warning("Template ID not found for conversation", conversation_id=conversation_id)
            return False, None
            
        template = await self.conversation_state_repository._db.templates.find_one({"_id": template_id})
        if not template:
            logger.warning("Template not found", template_id=template_id)
            return False, None
        
        # Get current stage and available stages
        current_stage = conversation.get("current_stage")
        available_stages = conversation.get("context", {}).get("available_stages", [])
        
        if not current_stage or not available_stages:
            logger.warning(
                "Missing stage information", 
                conversation_id=conversation_id,
                current_stage=current_stage,
                available_stages=available_stages
            )
            return False, None
        
        # Check if this is the final stage
        if current_stage == available_stages[-1]:
            logger.debug(
                "Conversation already in final stage", 
                conversation_id=conversation_id,
                current_stage=current_stage
            )
            return False, None
        
        # Get current stage data
        stage_data = self._get_stage_data(conversation, current_stage)
        if not stage_data:
            logger.warning(
                "Stage data not found", 
                conversation_id=conversation_id,
                current_stage=current_stage
            )
            return False, None
        
        # Get timing configuration
        timing_config = self.config_manager.get_timing_config(template, current_stage)
        
        # Check stage progression criteria
        stage_entered_at = stage_data.get("entered_at")
        current_time = datetime.utcnow()
        
        # Get completion metrics
        completion_metrics = conversation.get("metrics", {}).get(current_stage, {})
        
        # Get completion criteria for this stage
        completion_criteria = None
        for stage_def in template.get("stages", []):
            if stage_def.get("stage") == current_stage:
                completion_criteria = stage_def.get("completion_criteria")
                break
        
        # Evaluate progression
        should_advance = self.config_manager.should_advance_stage(
            timing_config,
            stage_entered_at,
            current_time,
            completion_metrics,
            completion_criteria
        )
        
        if should_advance:
            # Get next stage
            current_index = available_stages.index(current_stage)
            next_stage = available_stages[current_index + 1]
            
            logger.info(
                "Conversation should advance to next stage", 
                conversation_id=conversation_id,
                current_stage=current_stage,
                next_stage=next_stage
            )
            
            return True, next_stage
        else:
            return False, None
    
    async def advance_conversation_stage(
        self,
        conversation_id: str,
        next_stage: str
    ) -> bool:
        """
        Advance a conversation to the next stage.
        
        Args:
            conversation_id: ID of the conversation state
            next_stage: Name of the next stage
            
        Returns:
            True if successful, False otherwise
        """
        # Get conversation state
        conversation = await self.conversation_state_repository.get_conversation_state_by_id(conversation_id)
        if not conversation:
            logger.warning("Conversation not found", conversation_id=conversation_id)
            return False
        
        # Get current stage
        current_stage = conversation.get("current_stage")
        if not current_stage:
            logger.warning("Current stage not found", conversation_id=conversation_id)
            return False
        
        # Update stage information
        current_time = datetime.utcnow()
        stages = conversation.get("stages", [])
        
        # Mark current stage as exited
        for stage in stages:
            if stage.get("name") == current_stage and not stage.get("exited_at"):
                stage["exited_at"] = current_time
                stage["completed"] = True
        
        # Add new stage
        stages.append({
            "name": next_stage,
            "entered_at": current_time,
            "exited_at": None,
            "completed": False
        })
        
        # Update metrics
        metrics = conversation.get("metrics", {})
        metrics["stage_progressions"] = metrics.get("stage_progressions", 0) + 1
        
        # Update conversation state
        update_data = {
            "current_stage": next_stage,
            "stages": stages,
            "metrics": metrics,
            "last_active": current_time
        }
        
        success = await self.conversation_state_repository.update_conversation_state(
            conversation_id,
            update_data
        )
        
        if success:
            self.metrics.increment("stages_advanced")
            logger.info(
                "Advanced conversation stage", 
                conversation_id=conversation_id,
                from_stage=current_stage,
                to_stage=next_stage
            )
        else:
            logger.error(
                "Failed to advance conversation stage", 
                conversation_id=conversation_id,
                from_stage=current_stage,
                to_stage=next_stage
            )
        
        return success
    
    async def update_conversation_with_message(
        self,
        conversation_id: str,
        message_data: Dict[str, Any],
        is_inbound: bool = False
    ) -> bool:
        """
        Update a conversation with a new message.
        
        Args:
            conversation_id: ID of the conversation state
            message_data: Message data to add
            is_inbound: Whether this is an inbound message
            
        Returns:
            True if successful, False otherwise
        """
        # Get conversation state
        conversation = await self.conversation_state_repository.get_conversation_state_by_id(conversation_id)
        if not conversation:
            logger.warning("Conversation not found", conversation_id=conversation_id)
            return False
        
        # Add timestamp if not provided
        if "timestamp" not in message_data:
            message_data["timestamp"] = datetime.utcnow()
            
        # Set message type
        message_data["type"] = "inbound" if is_inbound else "outbound"
        
        # Update message history
        message_history = conversation.get("message_history", [])
        message_history.append(message_data)
        
        # Update metrics
        metrics = conversation.get("metrics", {})
        if is_inbound:
            metrics["messages_received"] = metrics.get("messages_received", 0) + 1
        else:
            metrics["messages_sent"] = metrics.get("messages_sent", 0) + 1
        
        # Update conversation state
        update_data = {
            "message_history": message_history,
            "metrics": metrics,
            "last_active": datetime.utcnow()
        }
        
        success = await self.conversation_state_repository.update_conversation_state(
            conversation_id,
            update_data
        )
        
        if success:
            logger.info(
                "Updated conversation with message", 
                conversation_id=conversation_id,
                is_inbound=is_inbound
            )
        else:
            logger.error(
                "Failed to update conversation with message", 
                conversation_id=conversation_id,
                is_inbound=is_inbound
            )
        
        return success
    
    async def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Dictionary of campaign metrics
        """
        # Get all conversations for this campaign
        conversations = await self.conversation_state_repository.find_conversation_states(
            {"campaign_id": campaign_id}
        )
        
        # Base metrics structure
        metrics = {
            "total_recipients": len(conversations),
            "stages": {},
            "engagement": {
                "total_messages_sent": 0,
                "total_messages_received": 0,
                "response_rate": 0,
                "average_messages_per_conversation": 0
            },
            "stage_progression": {
                "completed_all_stages": 0,
                "average_stages_completed": 0,
                "stage_completion_rates": {}
            },
            "status": {
                "active": 0,
                "completed": 0,
                "failed": 0
            }
        }
        
        total_stages_completed = 0
        stage_counts = {}
        
        for conversation in conversations:
            # Count by status
            status = conversation.get("status", "active")
            metrics["status"][status] = metrics["status"].get(status, 0) + 1
            
            # Count messages
            conv_metrics = conversation.get("metrics", {})
            metrics["engagement"]["total_messages_sent"] += conv_metrics.get("messages_sent", 0)
            metrics["engagement"]["total_messages_received"] += conv_metrics.get("messages_received", 0)
            
            # Count stages
            current_stage = conversation.get("current_stage")
            if current_stage:
                stage_counts[current_stage] = stage_counts.get(current_stage, 0) + 1
            
            # Count completed stages
            stages = conversation.get("stages", [])
            completed_stages = [s for s in stages if s.get("completed", False)]
            total_stages_completed += len(completed_stages)
            
            # Check if all stages completed
            available_stages = conversation.get("context", {}).get("available_stages", [])
            if available_stages and current_stage == available_stages[-1]:
                metrics["stage_progression"]["completed_all_stages"] += 1
        
        # Calculate averages and rates
        if metrics["total_recipients"] > 0:
            # Response rate
            if metrics["engagement"]["total_messages_sent"] > 0:
                metrics["engagement"]["response_rate"] = (
                    metrics["engagement"]["total_messages_received"] / 
                    metrics["engagement"]["total_messages_sent"]
                )
            
            # Average messages per conversation
            metrics["engagement"]["average_messages_per_conversation"] = (
                (metrics["engagement"]["total_messages_sent"] + 
                metrics["engagement"]["total_messages_received"]) / 
                metrics["total_recipients"]
            )
            
            # Average stages completed
            metrics["stage_progression"]["average_stages_completed"] = (
                total_stages_completed / metrics["total_recipients"]
            )
        
        # Stage distribution
        metrics["stages"] = stage_counts
        
        # Stage completion rates
        for conversation in conversations:
            available_stages = conversation.get("context", {}).get("available_stages", [])
            if not available_stages:
                continue
                
            stages = conversation.get("stages", [])
            for stage_name in available_stages:
                if stage_name not in metrics["stage_progression"]["stage_completion_rates"]:
                    metrics["stage_progression"]["stage_completion_rates"][stage_name] = {
                        "entered": 0,
                        "completed": 0,
                        "completion_rate": 0
                    }
                
                # Check if entered
                for stage in stages:
                    if stage.get("name") == stage_name:
                        metrics["stage_progression"]["stage_completion_rates"][stage_name]["entered"] += 1
                        if stage.get("completed", False):
                            metrics["stage_progression"]["stage_completion_rates"][stage_name]["completed"] += 1
        
        # Calculate completion rates
        for stage, data in metrics["stage_progression"]["stage_completion_rates"].items():
            if data["entered"] > 0:
                data["completion_rate"] = data["completed"] / data["entered"]
        
        logger.info(
            "Retrieved campaign metrics", 
            campaign_id=campaign_id,
            total_recipients=metrics["total_recipients"]
        )
        
        return metrics
    
    def _get_stage_data(self, conversation: Dict[str, Any], stage: str) -> Optional[Dict[str, Any]]:
        """
        Get data about a specific stage from the conversation.
        
        Args:
            conversation: Conversation state document
            stage: Stage name
        
        Returns:
            Stage data or None if not found
        """
        stages = conversation.get("stages", [])
        for stage_data in stages:
            if stage_data.get("name") == stage:
                return stage_data
        return None
    
    def _get_stages_for_campaign_type(self, template: Dict[str, Any], campaign_type: str) -> List[str]:
        """
        Get the list of stages for a specific campaign type.
        
        Args:
            template: Template document
            campaign_type: Campaign type
        
        Returns:
            List of stage names
        """
        # Check if template has type-specific stages
        type_specific_stages = template.get("campaign_types", {}).get(campaign_type, {}).get("stages")
        if type_specific_stages:
            return type_specific_stages
        
        # Otherwise, get all stages from the template
        stages = []
        for stage_def in template.get("stages", []):
            stage_name = stage_def.get("stage")
            if stage_name:
                stages.append(stage_name)
        
        return stages 