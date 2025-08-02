"""
Campaign Poller Module

This module provides functionality for polling and processing campaigns
that are inserted directly into MongoDB by the agent microservice. It discovers
new requests with servicetype="communication" and processes them.
"""

import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.config.config_manager import get_settings
from src.repository.conversation_state_repository import ConversationStateRepository
from src.service.campaign_manager import CampaignManager

# Configure logger
logger = structlog.get_logger(__name__)


class CampaignPoller:
    """
    Campaign Poller Service
    
    This service polls the database for communication batch requests inserted
    by the agent microservice and initiates campaign processing.
    """
    
    def __init__(
        self,
        campaign_repository: ConversationStateRepository,
        campaign_manager: CampaignManager
    ):
        """
        Initialize the campaign poller.
        
        Args:
            campaign_repository: Campaign repository for database access
            campaign_manager: Campaign manager for campaign processing
        """
        self.campaign_repository = campaign_repository
        self.campaign_manager = campaign_manager
        self.settings = get_settings()
        self.poll_interval_seconds = self.settings.campaign_poll_interval_seconds
        self.batch_collection = "agent_batch_requests"
        self.running = False
        self.last_poll_time = None
        
        logger.info(
            "Campaign poller initialized", 
            poll_interval_seconds=self.poll_interval_seconds
        )
    
    async def initialize(self) -> bool:
        """
        Initialize the campaign poller.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        logger.info("Initializing campaign poller")
        return True
    
    async def run(self):
        """
        Run the campaign poller in a continuous loop.
        
        This method polls for communication batch requests and processes them.
        It sleeps for the configured poll interval between iterations.
        """
        logger.info("Starting campaign poller")
        self.running = True
        
        while self.running:
            try:
                self.last_poll_time = datetime.utcnow()
                
                # Process new batch requests from agent
                await self.process_new_batch_requests()
                
                # Process campaigns that are scheduled to start
                await self.process_scheduled_campaigns()
                
                # Check for campaigns that need status updates
                await self.process_campaign_status_updates()
                
                # Log polling statistics
                logger.debug(
                    "Campaign polling iteration completed",
                    last_poll_time=self.last_poll_time.isoformat()
                )
                
            except Exception as e:
                logger.error(
                    "Error in campaign poller iteration",
                    error=str(e),
                    last_poll_time=self.last_poll_time.isoformat() if self.last_poll_time else None
                )
            
            # Sleep for the configured interval
            await asyncio.sleep(self.poll_interval_seconds)
    
    async def stop(self):
        """Stop the campaign poller."""
        logger.info("Stopping campaign poller")
        self.running = False
    
    async def process_new_batch_requests(self):
        """
        Process new batch requests from the agent microservice.
        
        This method looks for documents in the agent_batch_requests collection
        with servicetype="communication" and status="new", then creates campaigns
        from them.
        """
        try:
            # Query for new communication batch requests
            query = {
                "servicetype": "communication",
                "status": "new"
            }
            
            # Get new batch requests
            new_requests = await self.campaign_repository.find_many(
                self.batch_collection,
                query,
                limit=10
            )
            
            if not new_requests:
                logger.debug("No new communication batch requests found")
                return
            
            logger.info(
                "Found new communication batch requests", 
                count=len(new_requests)
            )
            
            # Process each batch request
            for request in new_requests:
                request_id = request.get("_id")
                
                try:
                    logger.info(
                        "Processing new communication batch request", 
                        request_id=request_id,
                        request_name=request.get("name", "Unnamed request")
                    )
                    
                    # Update request status to "processing"
                    await self.campaign_repository.update_one(
                        self.batch_collection,
                        {"_id": request_id},
                        {"$set": {
                            "status": "processing",
                            "processing_started_at": datetime.utcnow().isoformat()
                        }}
                    )
                    
                    # Create a campaign from the batch request
                    campaign_id = await self._create_campaign_from_request(request)
                    
                    if campaign_id:
                        # Update request status to "completed"
                        await self.campaign_repository.update_one(
                            self.batch_collection,
                            {"_id": request_id},
                            {"$set": {
                                "status": "completed",
                                "completed_at": datetime.utcnow().isoformat(),
                                "campaign_id": campaign_id
                            }}
                        )
                        
                        logger.info(
                            "Batch request processed and campaign created", 
                            request_id=request_id,
                            campaign_id=campaign_id
                        )
                    else:
                        # Update request status to "failed"
                        await self.campaign_repository.update_one(
                            self.batch_collection,
                            {"_id": request_id},
                            {"$set": {
                                "status": "failed",
                                "failed_at": datetime.utcnow().isoformat(),
                                "error": "Failed to create campaign"
                            }}
                        )
                        
                        logger.error(
                            "Failed to create campaign from batch request", 
                            request_id=request_id
                        )
                
                except Exception as e:
                    logger.error(
                        "Error processing batch request", 
                        request_id=request_id,
                        error=str(e)
                    )
                    
                    # Update request status to "failed"
                    await self.campaign_repository.update_one(
                        self.batch_collection,
                        {"_id": request_id},
                        {"$set": {
                            "status": "failed",
                            "failed_at": datetime.utcnow().isoformat(),
                            "error": str(e)
                        }}
                    )
        
        except Exception as e:
            logger.error(
                "Error getting new batch requests", 
                error=str(e)
            )
    
    async def _create_campaign_from_request(self, request: Dict[str, Any]) -> Optional[str]:
        """
        Create a campaign from a batch request.
        
        Args:
            request: Batch request document from agent
            
        Returns:
            Campaign ID if created successfully, None otherwise
        """
        try:
            # Extract template information
            template = request.get("template", {})
            if not template:
                logger.error("No template found in batch request")
                return None
            
            # Generate a unique ID for the campaign
            campaign_id = str(request.get("_id"))
            
            # Extract campaign details from the request
            name = request.get("name", f"Campaign from request {campaign_id}")
            recipients = request.get("recipients", [])
            scheduled_at = request.get("scheduled_at")
            
            # Convert template stages to campaign-specific format
            stages = self._convert_template_stages(template.get("stages", []))
            
            # Create campaign document
            campaign = {
                "_id": campaign_id,
                "name": name,
                "type": "communication",
                "subtype": template.get("template_type", "campaign"),
                "status": "pending",
                "recipients": recipients,
                "template": template,
                "scheduled_at": scheduled_at,
                "stages": stages,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": request.get("created_by", "agent"),
                "metadata": {
                    "source": "agent_batch_request",
                    "original_request_id": request.get("_id"),
                    "batch_id": request.get("batch_id")
                }
            }
            
            # Insert the campaign
            result = await self.campaign_repository.insert_one("campaigns", campaign)
            
            if result:
                logger.info(
                    "Created campaign from batch request", 
                    campaign_id=campaign_id,
                    request_id=request.get("_id")
                )
                return campaign_id
            else:
                logger.error(
                    "Failed to insert campaign", 
                    campaign_id=campaign_id
                )
                return None
        
        except Exception as e:
            logger.error(
                "Error creating campaign from batch request", 
                error=str(e)
            )
            return None
    
    def _convert_template_stages(self, template_stages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert template stages to campaign stages format.
        
        Args:
            template_stages: Stages from the template
            
        Returns:
            List of campaign stages
        """
        campaign_stages = []
        
        for i, stage in enumerate(template_stages):
            campaign_stage = {
                "name": stage.get("stage"),
                "order": i,
                "content": stage.get("content_structure", {}),
                "variables": stage.get("variables", {}),
                "completion_criteria": stage.get("completion_criteria", {}),
                "follow_up_timing": stage.get("follow_up_timing", {}),
                "conversation_guidance": stage.get("conversation_guidance", {})
            }
            
            campaign_stages.append(campaign_stage)
        
        return campaign_stages
    
    async def process_scheduled_campaigns(self):
        """
        Process campaigns that are scheduled to start.
        
        This method finds campaigns with 'scheduled' status that are
        due to start and updates their status to 'pending' for processing.
        """
        try:
            # Get current time
            current_time = datetime.utcnow()
            
            # Get scheduled campaigns that are due to start
            scheduled_campaigns = await self.campaign_repository.get_scheduled_campaigns(current_time)
            
            if not scheduled_campaigns:
                logger.debug("No scheduled campaigns due to start")
                return
            
            logger.info(
                "Found scheduled campaigns due to start", 
                count=len(scheduled_campaigns)
            )
            
            # Process each scheduled campaign
            for campaign in scheduled_campaigns:
                campaign_id = campaign.get("id")
                
                try:
                    # Update campaign status to 'pending'
                    await self.campaign_repository.update_campaign_status(
                        campaign_id, 
                        "pending",
                        {"pending_at": current_time.isoformat()}
                    )
                    
                    logger.info(
                        "Scheduled campaign is now pending", 
                        campaign_id=campaign_id,
                        campaign_name=campaign.get("name"),
                        scheduled_time=campaign.get("scheduled_at")
                    )
                
                except Exception as e:
                    logger.error(
                        "Error processing scheduled campaign", 
                        campaign_id=campaign_id,
                        error=str(e)
                    )
        
        except Exception as e:
            logger.error(
                "Error getting scheduled campaigns", 
                error=str(e)
            )
    
    async def process_campaign_status_updates(self):
        """
        Check for campaigns that need status updates.
        
        This method checks active campaigns to see if they should be
        marked as completed or have other status updates.
        """
        try:
            # Get active campaigns
            active_campaigns = await self.campaign_repository.get_campaigns_by_status("active")
            
            if not active_campaigns:
                logger.debug("No active campaigns found")
                return
            
            # Process each active campaign
            for campaign in active_campaigns:
                campaign_id = campaign.get("id")
                
                try:
                    # Check if campaign is completed
                    metrics = await self.campaign_manager.get_campaign_metrics(campaign_id)
                    
                    # If all conversations are in a final state (completed, failed, canceled)
                    # and there are no pending conversations, mark the campaign as completed
                    if metrics and metrics.get("is_complete", False):
                        await self.campaign_repository.update_campaign_status(
                            campaign_id, 
                            "completed",
                            {
                                "completed_at": datetime.utcnow().isoformat(),
                                "final_metrics": metrics
                            }
                        )
                        
                        logger.info(
                            "Campaign marked as completed", 
                            campaign_id=campaign_id,
                            campaign_name=campaign.get("name")
                        )
                
                except Exception as e:
                    logger.error(
                        "Error checking campaign status", 
                        campaign_id=campaign_id,
                        error=str(e)
                    )
        
        except Exception as e:
            logger.error(
                "Error getting active campaigns", 
                error=str(e)
            )
    
    async def trigger_campaign_processing(self, campaign_id: str) -> Dict[str, Any]:
        """
        Manually trigger processing for a specific campaign.
        
        Args:
            campaign_id: ID of the campaign to process
            
        Returns:
            Dictionary with processing result
        """
        try:
            # Check if campaign exists
            campaign = await self.campaign_repository.get_campaign(campaign_id)
            
            if not campaign:
                return {
                    "success": False,
                    "error": f"Campaign with ID {campaign_id} not found"
                }
            
            # Check campaign status
            status = campaign.get("status")
            
            if status == "pending":
                # Process the campaign immediately by initializing conversations
                result = await self.campaign_manager.initialize_campaign_conversations(campaign_id)
                
                if result.get("success"):
                    # Update campaign status to 'active'
                    await self.campaign_repository.update_campaign_status(
                        campaign_id, 
                        "active",
                        {
                            "initialized_at": datetime.utcnow().isoformat(),
                            "total_conversations": result.get("conversation_count", 0)
                        }
                    )
                    
                    return {
                        "success": True,
                        "message": f"Campaign {campaign_id} initialized successfully",
                        "conversation_count": result.get("conversation_count", 0)
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown error initializing campaign")
                    }
                
            elif status == "scheduled":
                # Update status to pending to trigger processing
                await self.campaign_repository.update_campaign_status(
                    campaign_id, 
                    "pending",
                    {"pending_at": datetime.utcnow().isoformat()}
                )
                
                return {
                    "success": True,
                    "message": f"Scheduled campaign {campaign_id} set to pending for immediate processing"
                }
            else:
                return {
                    "success": False,
                    "error": f"Cannot process campaign with status '{status}'"
                }
        
        except Exception as e:
            logger.error(
                "Error triggering campaign processing", 
                campaign_id=campaign_id,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e)
            } 