"""
Campaign Service

This module provides functionality for creating, sending, and monitoring campaigns.
It orchestrates interactions with email providers, CRM systems, and campaign repositories.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from ...domain.models.campaign import Campaign, CampaignStatus
from ...domain.models.email_template import EmailTemplate
from ...domain.exceptions.campaign_exceptions import (
    CampaignNotFoundException,
    CampaignValidationError,
    CampaignServiceError
)
from ...infrastructure.repositories.campaign_repository import CampaignRepository
from ...infrastructure.repositories.template_repository import TemplateRepository
from ...infrastructure.email.email_client import EmailClient
from ...infrastructure.crm.crm_client import CRMClient
from ...infrastructure.tenant.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class CampaignService:
    """
    Service for handling campaign operations.
    
    This service provides methods for creating, sending, and monitoring campaigns.
    It coordinates actions between repositories, email providers, and CRM systems.
    """
    
    def __init__(
        self,
        campaign_repository: Optional[CampaignRepository] = None,
        template_repository: Optional[TemplateRepository] = None,
        email_client: Optional[EmailClient] = None,
        crm_client: Optional[CRMClient] = None
    ):
        """
        Initialize the campaign service.
        
        Args:
            campaign_repository: Repository for campaign persistence
            template_repository: Repository for email template management
            email_client: Client for sending emails
            crm_client: Client for CRM system interactions
        """
        self.campaign_repository = campaign_repository or CampaignRepository()
        self.template_repository = template_repository or TemplateRepository()
        self.email_client = email_client or EmailClient()
        self.crm_client = crm_client or CRMClient()
        
    async def close(self):
        """Close resources used by the service."""
        try:
            # Close repository connections
            if self.campaign_repository:
                await self.campaign_repository.close()
                
            if self.template_repository:
                await self.template_repository.close()
                
            # Close client connections
            if self.email_client:
                await self.email_client.close()
                
            if self.crm_client:
                await self.crm_client.close()
                
            logger.info("Closed campaign service resources")
        except Exception as e:
            logger.error(f"Error closing campaign service resources: {str(e)}")
    
    async def create_campaign(
        self, 
        name: str, 
        template_id: str, 
        segment_id: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Campaign:
        """
        Create a new campaign.
        
        Args:
            name: Name of the campaign
            template_id: ID of the email template to use
            segment_id: ID of the recipient segment (optional)
            scheduled_time: Time to send the campaign (optional)
            custom_attributes: Additional attributes for the campaign (optional)
            
        Returns:
            The created campaign
            
        Raises:
            CampaignValidationError: If campaign data is invalid
            CampaignServiceError: If there's an error creating the campaign
        """
        logger.info(f"Creating campaign with name '{name}' using template {template_id}")
        
        try:
            # Validate inputs
            if not name:
                raise CampaignValidationError("Campaign name is required")
                
            if not template_id:
                raise CampaignValidationError("Template ID is required")
                
            # Get template to ensure it exists
            template = await self.template_repository.get_by_id(template_id)
            
            if not template:
                raise CampaignValidationError(f"Template with ID {template_id} not found")
                
            # Create campaign object
            campaign = Campaign(
                name=name,
                template_id=template_id,
                segment_id=segment_id,
                scheduled_time=scheduled_time,
                status=CampaignStatus.DRAFT,
                custom_attributes=custom_attributes or {}
            )
            
            # Add tenant ID if available
            tenant_id = TenantContext.get_tenant_id()
            if tenant_id:
                campaign.tenant_id = tenant_id
                
            # Persist to repository
            created_campaign = await self.campaign_repository.create(campaign)
            
            logger.info(f"Created campaign with ID {created_campaign.id}")
            return created_campaign
            
        except CampaignValidationError as e:
            logger.warning(f"Campaign validation error: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error creating campaign: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise CampaignServiceError(error_msg) from e
    
    async def update_campaign(
        self, 
        campaign_id: str, 
        updates: Dict[str, Any]
    ) -> Campaign:
        """
        Update an existing campaign.
        
        Args:
            campaign_id: ID of the campaign to update
            updates: Dictionary of fields to update
            
        Returns:
            The updated campaign
            
        Raises:
            CampaignNotFoundException: If campaign is not found
            CampaignValidationError: If updates are invalid
            CampaignServiceError: If there's an error updating the campaign
        """
        logger.info(f"Updating campaign {campaign_id}")
        
        try:
            # Get existing campaign
            campaign = await self.campaign_repository.get_by_id(campaign_id)
            
            if not campaign:
                raise CampaignNotFoundException(f"Campaign with ID {campaign_id} not found")
                
            # Validate updates
            if 'status' in updates and updates['status'] not in CampaignStatus.__members__.values():
                raise CampaignValidationError(f"Invalid status: {updates['status']}")
                
            if 'template_id' in updates:
                template = await self.template_repository.get_by_id(updates['template_id'])
                if not template:
                    raise CampaignValidationError(f"Template with ID {updates['template_id']} not found")
                    
            # Prevent updates if campaign is not in DRAFT status
            if campaign.status != CampaignStatus.DRAFT and not self._is_admin_update(updates):
                raise CampaignValidationError(f"Cannot update campaign in {campaign.status} status")
                
            # Apply updates
            for key, value in updates.items():
                if hasattr(campaign, key):
                    setattr(campaign, key, value)
                elif key == 'custom_attributes' and isinstance(value, dict):
                    campaign.custom_attributes.update(value)
                    
            # Update timestamp
            campaign.updated_at = datetime.utcnow()
            
            # Persist to repository
            updated_campaign = await self.campaign_repository.update(campaign)
            
            logger.info(f"Updated campaign {campaign_id}")
            return updated_campaign
            
        except (CampaignNotFoundException, CampaignValidationError) as e:
            logger.warning(f"Campaign update error: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error updating campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise CampaignServiceError(error_msg) from e
    
    def _is_admin_update(self, updates: Dict[str, Any]) -> bool:
        """
        Check if updates are administrative (allowed in any status).
        
        Args:
            updates: Dictionary of updates
            
        Returns:
            True if only admin fields are being updated
        """
        admin_fields = {'status', 'last_error', 'metrics'}
        return all(key in admin_fields for key in updates.keys())
    
    async def get_campaign(self, campaign_id: str) -> Campaign:
        """
        Get a campaign by ID.
        
        Args:
            campaign_id: ID of the campaign to retrieve
            
        Returns:
            The campaign
            
        Raises:
            CampaignNotFoundException: If campaign is not found
            CampaignServiceError: If there's an error retrieving the campaign
        """
        logger.debug(f"Getting campaign {campaign_id}")
        
        try:
            campaign = await self.campaign_repository.get_by_id(campaign_id)
            
            if not campaign:
                raise CampaignNotFoundException(f"Campaign with ID {campaign_id} not found")
                
            return campaign
            
        except CampaignNotFoundException as e:
            logger.warning(f"Campaign not found: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error retrieving campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise CampaignServiceError(error_msg) from e
    
    async def get_campaigns(
        self, 
        limit: int = 20, 
        offset: int = 0, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Campaign], int]:
        """
        Get a list of campaigns with pagination and filtering.
        
        Args:
            limit: Maximum number of campaigns to return
            offset: Number of campaigns to skip
            filters: Dictionary of filters to apply
            
        Returns:
            Tuple of (campaigns list, total count)
            
        Raises:
            CampaignServiceError: If there's an error retrieving campaigns
        """
        logger.debug(f"Getting campaigns with limit={limit}, offset={offset}, filters={filters}")
        
        try:
            # Apply tenant filter if in tenant context
            tenant_id = TenantContext.get_tenant_id()
            if tenant_id:
                filters = filters or {}
                filters['tenant_id'] = tenant_id
                
            # Get campaigns from repository
            campaigns, total = await self.campaign_repository.get_all(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            logger.debug(f"Retrieved {len(campaigns)} campaigns out of {total} total")
            return campaigns, total
            
        except Exception as e:
            error_msg = f"Error retrieving campaigns: {str(e)}"
            logger.error(error_msg)
            raise CampaignServiceError(error_msg) from e
    
    async def send_campaign(self, campaign_id: str) -> bool:
        """
        Send a campaign.
        
        Args:
            campaign_id: ID of the campaign to send
            
        Returns:
            True if the campaign was sent successfully
            
        Raises:
            CampaignNotFoundException: If campaign is not found
            CampaignValidationError: If campaign cannot be sent
            CampaignServiceError: If there's an error sending the campaign
        """
        logger.info(f"Sending campaign {campaign_id}")
        
        try:
            # Get campaign
            campaign = await self.get_campaign(campaign_id)
            
            # Validate campaign can be sent
            if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
                raise CampaignValidationError(f"Cannot send campaign in {campaign.status} status")
                
            # Get template
            template = await self.template_repository.get_by_id(campaign.template_id)
            
            if not template:
                raise CampaignValidationError(f"Template {campaign.template_id} not found")
                
            # Get recipients
            recipients = await self._get_recipients(campaign)
            
            if not recipients:
                raise CampaignValidationError("No recipients found for campaign")
                
            # Update campaign status
            await self.update_campaign(campaign_id, {'status': CampaignStatus.SENDING})
            
            # Send campaign to email provider
            success = await self.email_client.send_campaign(
                campaign_id=campaign_id,
                template=template,
                recipients=recipients,
                custom_attributes=campaign.custom_attributes
            )
            
            if success:
                # Update campaign status
                await self.update_campaign(campaign_id, {'status': CampaignStatus.SENT})
                logger.info(f"Campaign {campaign_id} sent successfully to {len(recipients)} recipients")
            else:
                # Update campaign status
                await self.update_campaign(
                    campaign_id, 
                    {
                        'status': CampaignStatus.FAILED,
                        'last_error': "Failed to send campaign"
                    }
                )
                logger.error(f"Failed to send campaign {campaign_id}")
                
            return success
            
        except (CampaignNotFoundException, CampaignValidationError) as e:
            logger.warning(f"Cannot send campaign: {str(e)}")
            
            # Update campaign status if found
            try:
                campaign = await self.campaign_repository.get_by_id(campaign_id)
                if campaign:
                    await self.update_campaign(
                        campaign_id, 
                        {
                            'status': CampaignStatus.FAILED,
                            'last_error': str(e)
                        }
                    )
            except Exception:
                pass
                
            raise
            
        except Exception as e:
            error_msg = f"Error sending campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Update campaign status
            try:
                await self.update_campaign(
                    campaign_id, 
                    {
                        'status': CampaignStatus.FAILED,
                        'last_error': str(e)
                    }
                )
            except Exception:
                pass
                
            raise CampaignServiceError(error_msg) from e
    
    async def _get_recipients(self, campaign: Campaign) -> List[Dict[str, Any]]:
        """
        Get recipients for a campaign.
        
        Args:
            campaign: The campaign
            
        Returns:
            List of recipient data dictionaries
            
        Raises:
            CampaignValidationError: If segment is not found
        """
        # If segment ID is provided, get from CRM
        if campaign.segment_id:
            return await self.crm_client.get_segment_recipients(campaign.segment_id)
            
        # If recipients are in custom attributes
        if 'recipients' in campaign.custom_attributes:
            return campaign.custom_attributes['recipients']
            
        # If recipient data is in custom attributes
        if 'recipient_data' in campaign.custom_attributes:
            return campaign.custom_attributes['recipient_data']
            
        # No recipients found
        return []
    
    async def cancel_campaign(self, campaign_id: str) -> bool:
        """
        Cancel a campaign.
        
        Args:
            campaign_id: ID of the campaign to cancel
            
        Returns:
            True if the campaign was cancelled successfully
            
        Raises:
            CampaignNotFoundException: If campaign is not found
            CampaignValidationError: If campaign cannot be cancelled
            CampaignServiceError: If there's an error cancelling the campaign
        """
        logger.info(f"Cancelling campaign {campaign_id}")
        
        try:
            # Get campaign
            campaign = await self.get_campaign(campaign_id)
            
            # Validate campaign can be cancelled
            if campaign.status in [CampaignStatus.COMPLETED, CampaignStatus.FAILED, CampaignStatus.CANCELLED]:
                raise CampaignValidationError(f"Cannot cancel campaign in {campaign.status} status")
                
            # If campaign is in SENDING status, cancel with email provider
            if campaign.status == CampaignStatus.SENDING:
                await self.email_client.cancel_campaign(campaign_id)
                
            # Update campaign status
            await self.update_campaign(
                campaign_id, 
                {
                    'status': CampaignStatus.CANCELLED,
                    'completed_at': datetime.utcnow()
                }
            )
            
            logger.info(f"Campaign {campaign_id} cancelled successfully")
            return True
            
        except (CampaignNotFoundException, CampaignValidationError) as e:
            logger.warning(f"Cannot cancel campaign: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error cancelling campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise CampaignServiceError(error_msg) from e
    
    async def get_campaign_status(self, campaign_id: str) -> CampaignStatus:
        """
        Get the current status of a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Current status of the campaign
            
        Raises:
            CampaignNotFoundException: If campaign is not found
            CampaignServiceError: If there's an error retrieving status
        """
        logger.debug(f"Getting status for campaign {campaign_id}")
        
        try:
            # Get campaign from repository
            campaign = await self.get_campaign(campaign_id)
            
            # If campaign is in SENDING or SENT status, check with email provider
            if campaign.status in [CampaignStatus.SENDING, CampaignStatus.SENT]:
                provider_status = await self.email_client.get_campaign_status(campaign_id)
                
                # Map provider status to campaign status
                if provider_status == "COMPLETED":
                    return CampaignStatus.COMPLETED
                elif provider_status == "FAILED":
                    return CampaignStatus.FAILED
                elif provider_status == "CANCELLED":
                    return CampaignStatus.CANCELLED
                elif provider_status == "SENDING":
                    return CampaignStatus.SENDING
                    
            return campaign.status
            
        except CampaignNotFoundException as e:
            logger.warning(f"Campaign not found: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error getting status for campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise CampaignServiceError(error_msg) from e
    
    async def get_campaign_statistics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get statistics for a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Dictionary of campaign statistics
            
        Raises:
            CampaignNotFoundException: If campaign is not found
            CampaignServiceError: If there's an error retrieving statistics
        """
        logger.debug(f"Getting statistics for campaign {campaign_id}")
        
        try:
            # Get campaign
            campaign = await self.get_campaign(campaign_id)
            
            # Get statistics from email provider
            stats = await self.email_client.get_campaign_statistics(campaign_id)
            
            # If campaign has existing metrics, merge with new stats
            if hasattr(campaign, 'metrics') and campaign.metrics:
                merged_stats = {**campaign.metrics, **stats}
            else:
                merged_stats = stats
                
            # Update campaign with latest metrics
            await self.update_campaign(campaign_id, {'metrics': merged_stats})
            
            return merged_stats
            
        except CampaignNotFoundException as e:
            logger.warning(f"Campaign not found: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error getting statistics for campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise CampaignServiceError(error_msg) from e
    
    async def get_campaign_preview(
        self, 
        template_id: str, 
        recipient_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a preview of a campaign email.
        
        Args:
            template_id: ID of the email template
            recipient_data: Sample recipient data for personalization
            
        Returns:
            Dictionary with preview data (subject, body)
            
        Raises:
            CampaignValidationError: If template is not found
            CampaignServiceError: If there's an error generating preview
        """
        logger.debug(f"Generating preview for template {template_id}")
        
        try:
            # Get template
            template = await self.template_repository.get_by_id(template_id)
            
            if not template:
                raise CampaignValidationError(f"Template {template_id} not found")
                
            # Generate preview with email client
            preview = await self.email_client.generate_preview(template, recipient_data or {})
            
            return preview
            
        except CampaignValidationError as e:
            logger.warning(f"Template validation error: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error generating preview for template {template_id}: {str(e)}"
            logger.error(error_msg)
            raise CampaignServiceError(error_msg) from e
    
    async def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.
        
        Args:
            campaign_id: ID of the campaign to delete
            
        Returns:
            True if the campaign was deleted successfully
            
        Raises:
            CampaignNotFoundException: If campaign is not found
            CampaignValidationError: If campaign cannot be deleted
            CampaignServiceError: If there's an error deleting the campaign
        """
        logger.info(f"Deleting campaign {campaign_id}")
        
        try:
            # Get campaign
            campaign = await self.get_campaign(campaign_id)
            
            # Only allow deletion of DRAFT, COMPLETED, FAILED, or CANCELLED campaigns
            if campaign.status not in [
                CampaignStatus.DRAFT, 
                CampaignStatus.COMPLETED, 
                CampaignStatus.FAILED, 
                CampaignStatus.CANCELLED
            ]:
                raise CampaignValidationError(f"Cannot delete campaign in {campaign.status} status")
                
            # Delete from repository
            success = await self.campaign_repository.delete(campaign_id)
            
            if success:
                logger.info(f"Campaign {campaign_id} deleted successfully")
            else:
                logger.warning(f"Failed to delete campaign {campaign_id}")
                
            return success
            
        except (CampaignNotFoundException, CampaignValidationError) as e:
            logger.warning(f"Cannot delete campaign: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Error deleting campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise CampaignServiceError(error_msg) from e 