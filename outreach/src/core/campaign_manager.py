"""
Campaign Manager Service

This module handles the business logic for campaign management,
including creation, execution, and monitoring of outreach campaigns.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Any
from uuid import UUID
import asyncio
from enum import Enum
import logging

from ..models.campaign import Campaign, CampaignStatus, CampaignType
from ..config.template_loader import load_campaign_template
from ..models.contact import ContactList
from ..services.campaign_service import CampaignService
from ..services.conversation_service import ConversationService
from ..services.workflow_service import WorkflowService
from ..services.notification_service import NotificationService, NotificationType

logger = logging.getLogger(__name__)

class CampaignManager:
    """
    Manages the complete lifecycle of outreach campaigns.
    
    Handles scheduling, execution, monitoring, and analytics for campaigns.
    """
    
    def __init__(
        self,
        campaign_service: CampaignService,
        conversation_service: ConversationService,
        workflow_service: WorkflowService,
        notification_service: NotificationService
    ):
        """Initialize with required services."""
        self.campaign_service = campaign_service
        self.conversation_service = conversation_service
        self.workflow_service = workflow_service
        self.notification_service = notification_service
        self._active_tasks: Dict[UUID, asyncio.Task] = {}
    
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Campaign:
        """
        Create a new campaign with the provided data.
        
        Args:
            campaign_data: Dictionary containing campaign details
            
        Returns:
            The created Campaign object
        """
        return await self.campaign_service.create_campaign(campaign_data)
    
    async def start_campaign(self, campaign_id: UUID, template_name: str = "campaign_template_example.json") -> bool:
        """
        Start a scheduled campaign, loading its template config.
        Args:
            campaign_id: ID of the campaign to start
            template_name: Filename of the template config to use
        Returns:
            bool: True if the campaign was started successfully
        """
        campaign = await self.campaign_service.get_campaign(campaign_id)
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return False
        if campaign.status != CampaignStatus.DRAFT:
            logger.warning(f"Cannot start campaign {campaign_id} with status {campaign.status}")
            return False
        # Load campaign template config
        try:
            campaign.template_config = load_campaign_template(template_name)
        except Exception as e:
            logger.error(f"Failed to load campaign template: {e}")
            return False
        # Update campaign status to ACTIVE
        await self.campaign_service.update_campaign(
            campaign_id, 
            {"status": CampaignStatus.ACTIVE}
        )
        # Start the campaign execution in the background, passing template
        self._active_tasks[campaign_id] = asyncio.create_task(
            self._execute_campaign(campaign_id, campaign.template_config)
        )
        # Notify admins
        await self.notification_service.send_campaign_notification(
            campaign_id=campaign_id,
            notification_type=NotificationType.EMAIL,
            recipient="admin@example.com",
            subject="Campaign Started",
            message=f"Campaign {campaign.name} has started.",
            campaign_metadata={"action_required": False}
        )
        return True
    
    async def pause_campaign(self, campaign_id: UUID) -> bool:
        """
        Pause a running campaign.
        
        Args:
            campaign_id: ID of the campaign to pause
            
        Returns:
            bool: True if the campaign was paused successfully
        """
        # Implementation for pausing a campaign
        pass
    
    async def _execute_campaign(self, campaign_id: UUID, template_config: dict) -> None:
        """
        Execute the campaign by processing its contact list, using the given template config.
        Args:
            campaign_id: ID of the campaign to execute
            template_config: Loaded campaign template config dict
        """
        try:
            campaign = await self.campaign_service.get_campaign(campaign_id)
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found during execution")
                return
            # Process each contact in the campaign's contact list
            for contact in campaign.contact_list.contacts:
                await self._process_contact(campaign, contact, template_config)
                # Respect rate limiting from template config if present
                delay = template_config.get('global_settings', {}).get('rate_limit_delay', 1.0)
                await asyncio.sleep(delay)
            # Mark campaign as completed
            await self.campaign_service.update_campaign(
                campaign_id,
                {"status": CampaignStatus.COMPLETED}
            )
            logger.info(f"Completed execution of campaign {campaign_id}")
        except Exception as e:
            logger.error(f"Error executing campaign {campaign_id}: {str(e)}", exc_info=True)
            await self.campaign_service.update_campaign(
                campaign_id,
                {"status": CampaignStatus.FAILED, "error_message": str(e)}
            )
    
    async def _process_contact(self, campaign: Campaign, contact: Dict[str, Any], template_config: dict) -> None:
        """
        Process a single contact in the campaign, using the template config.
        Args:
            campaign: The campaign being executed
            contact: The contact to process
            template_config: Loaded campaign template config dict
        """
        try:
            # Start a new conversation for this contact
            conversation = await self.conversation_service.start_conversation(
                campaign_id=campaign.id,
                contact_id=contact['id'],
                context={
                    'campaign_id': str(campaign.id),
                    'contact': contact,
                    'campaign_type': campaign.type.value,
                    'template_config': template_config
                }
            )
            # Start at the first stage from the template
            first_stage = template_config.get('stages', [{}])[0].get('id', 'start')
            # Execute the first step in the workflow, passing template config
            await self.workflow_service.execute_step(
                workflow_id=campaign.workflow_id,
                step_id=first_stage,
                context={
                    'conversation_id': str(conversation.id),
                    'contact': contact,
                    'campaign': campaign.dict(),
                    'template_config': template_config
                }
            )
        except Exception as e:
            logger.error(
                f"Error processing contact {contact.get('id', 'unknown')} "
                f"in campaign {campaign.id}: {str(e)}",
                exc_info=True
            )
    
    async def get_campaign_metrics(self, campaign_id: UUID) -> Dict[str, Any]:
        """
        Get metrics for a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Dictionary containing campaign metrics
        """
        # In a real implementation, this would aggregate metrics from various services
        return {
            'campaign_id': campaign_id,
            'status': 'active',
            'metrics': {
                'total_contacts': 100,
                'messages_sent': 75,
                'responses_received': 25,
                'conversion_rate': 25.0
            }
        }
    
    async def stop(self) -> None:
        """Stop all active campaign tasks."""
        for task in self._active_tasks.values():
            task.cancel()
        await asyncio.gather(*self._active_tasks.values(), return_exceptions=True)
        self._active_tasks.clear()
