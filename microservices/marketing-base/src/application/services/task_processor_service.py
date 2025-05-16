"""
Task processor service for processing campaign tasks.

This module provides a service for processing campaign tasks from the central task repository.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import copy
import asyncio

from ...models.campaign import Campaign, CampaignStatus, Recipient, RecipientStatus
from ...infrastructure.repositories.campaign_repository import CampaignRepository
from ...application.services.campaign_service import CampaignService
from ...application.services.multi_tenant_batch_processor import MultiTenantBatchProcessor

logger = logging.getLogger(__name__)


class TaskProcessorService:
    """Service for processing campaign tasks from the central repository."""

    def __init__(
        self,
        campaign_service: Optional[CampaignService] = None,
        campaign_repository: Optional[CampaignRepository] = None,
        multi_tenant_processor: Optional[MultiTenantBatchProcessor] = None
    ):
        """
        Initialize the task processor service.
        
        Args:
            campaign_service: Service for processing campaigns
            campaign_repository: Repository for campaign storage
            multi_tenant_processor: Processor for multi-tenant campaigns
        """
        self.campaign_service = campaign_service or CampaignService()
        self.campaign_repository = campaign_repository or CampaignRepository()
        self.multi_tenant_processor = multi_tenant_processor or MultiTenantBatchProcessor()
    
    async def process_campaign_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a campaign task from the central repository.
        
        Args:
            task: Task data
            
        Returns:
            Dictionary with processing results
            
        Raises:
            ValueError: If task data is invalid
        """
        # Get task type
        task_type = task.get('task_type', 'campaign')
        
        # Process based on task type
        if task_type == 'multi_tenant_campaign':
            # Process multi-tenant campaign
            logger.info("Processing multi-tenant campaign task")
            return await self._process_multi_tenant_campaign(task)
        elif task_type == 'campaign':
            # Process standard campaign
            # Validate task
            if not task.get('campaign_template'):
                raise ValueError("Missing campaign template in task")
            
            if not task.get('recipients', []):
                raise ValueError("No recipients specified in task")
            
            # Check for complex campaign structure
            campaign_template = task.get('campaign_template')
            if self._is_complex_campaign(campaign_template):
                logger.info("Processing complex campaign structure")
                return await self._process_complex_campaign(campaign_template, task.get('recipients', []), task)
                
            # Process standard campaign
            return await self._process_standard_campaign(campaign_template, task.get('recipients', []), task)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _process_multi_tenant_campaign(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a multi-tenant campaign task.
        
        Args:
            task: Task data
            
        Returns:
            Dictionary with processing results
        """
        # Validate task
        campaign_template = task.get('campaign_template')
        tenant_ids = task.get('tenant_ids', [])
        
        if not campaign_template:
            raise ValueError("Missing campaign template in multi-tenant task")
        
        if not tenant_ids:
            raise ValueError("No tenant IDs specified in multi-tenant task")
        
        # Create batch data
        batch_data = {
            "name": task.get('name', 'Multi-tenant Campaign Batch'),
            "description": task.get('description', 'Created from task'),
            "campaign_template": campaign_template,
            "tenant_ids": tenant_ids,
            "tags": task.get('tags', []),
            "custom_attributes": {
                "task_id": task.get('task_id', str(uuid.uuid4())),
                "source": "task_processor"
            }
        }
        
        # Add batch processing settings if provided
        if 'batch_processing' in task:
            batch_processing = task['batch_processing']
            if 'max_retries' in batch_processing:
                batch_data['max_retries'] = batch_processing['max_retries']
        
        # Create the multi-tenant batch
        batch_id = await self.multi_tenant_processor.create_multi_tenant_batch(batch_data)
        
        # Process the batch
        try:
            # Start processing the batch (but don't wait for completion)
            # This allows processing to continue asynchronously
            asyncio.create_task(self.multi_tenant_processor.process_batch(await self.multi_tenant_processor.batch_repository.get_by_id(batch_id)))
            
            # Return result
            return {
                'status': 'processing',
                'multi_tenant_batch_id': batch_id,
                'tenant_count': len(tenant_ids),
                'processed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing multi-tenant batch {batch_id}: {str(e)}")
            return {
                'status': 'failed',
                'multi_tenant_batch_id': batch_id,
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
    
    def _is_complex_campaign(self, campaign_template: Dict[str, Any]) -> bool:
        """
        Check if a campaign has a complex structure requiring special processing.
        
        Args:
            campaign_template: The campaign template
            
        Returns:
            True if the campaign is complex, False otherwise
        """
        # Check for multi-stage workflow
        if "campaign" in campaign_template and "stages" in campaign_template["campaign"]:
            stages = campaign_template["campaign"]["stages"]
            if isinstance(stages, list) and len(stages) > 1:
                return True
        
        return False
    
    async def _process_complex_campaign(
        self, 
        campaign_template: Dict[str, Any], 
        recipients_data: List[Dict[str, Any]],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a complex campaign with multiple stages.
        
        Args:
            campaign_template: Campaign template data
            recipients_data: List of recipient data
            task: Original task data
            
        Returns:
            Dictionary with processing results
        """
        # Extract stages from campaign template
        stages = campaign_template.get('campaign', {}).get('stages', [])
        
        if not stages:
            logger.warning("No stages found in campaign, falling back to standard processing")
            return await self._process_standard_campaign(campaign_template, recipients_data, task)
        
        # Create a multi-stage campaign
        results = {
            'status': 'processing',
            'processed_at': datetime.utcnow().isoformat(),
            'campaigns': [],
            'multi_stage': {
                'stages': stages,
                'stage_campaigns': []
            }
        }
        
        # Get scheduled time if specified
        scheduled_time_str = campaign_template.get('campaign', {}).get('scheduled_at')
        base_scheduled_time = None
        
        if scheduled_time_str:
            try:
                base_scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                logger.warning(f"Invalid scheduled_at time format: {scheduled_time_str}")
        
        if not base_scheduled_time:
            base_scheduled_time = datetime.utcnow() + timedelta(minutes=5)  # Default: start in 5 minutes
            
        # Process each stage
        template_map = campaign_template.get('campaign', {}).get('templates', {})
        wait_periods = campaign_template.get('workflow', {}).get('wait_periods', {})
        
        for i, stage in enumerate(stages):
            # Get template ID for this stage
            template_id = template_map.get(stage)
            if not template_id:
                logger.warning(f"No template ID defined for stage {stage}, skipping")
                continue
                
            # Create stage-specific campaign template
            stage_template = copy.deepcopy(campaign_template)
            
            # Set stage-specific details
            stage_template['id'] = f"{campaign_template.get('id', task.get('campaign_id', 'campaign'))}-{stage}"
            stage_template['name'] = f"{campaign_template.get('name', 'Campaign')} - {stage.replace('_', ' ').title()}"
            
            # Calculate scheduled time for this stage
            scheduled_time = base_scheduled_time
            
            if i > 0:
                # Apply wait period if this isn't the first stage
                previous_stage = stages[i-1]
                wait_key = f"{previous_stage}_to_{stage}"
                
                # Check for wait period in workflow configuration
                if wait_key in wait_periods:
                    days = wait_periods[wait_key].get('days', 0)
                    hours = wait_periods[wait_key].get('hours', 0)
                    minutes = wait_periods[wait_key].get('minutes', 0)
                    
                    # Apply wait period
                    scheduled_time = base_scheduled_time + timedelta(days=days, hours=hours, minutes=minutes)
            
            stage_template['scheduled_at'] = scheduled_time.isoformat()
            
            # Apply template for this stage
            self._apply_template_from_id(stage_template, template_id)
            
            # Add stage tracking info
            if 'custom_attributes' not in stage_template:
                stage_template['custom_attributes'] = {}
            stage_template['custom_attributes']['campaign_stage'] = stage
            stage_template['custom_attributes']['campaign_stage_index'] = i
            
            # For stages after the first, we'll need to process them later when it's time
            if i == 0:
                # Process the first stage immediately
                stage_result = await self._process_standard_campaign(stage_template, recipients_data, task)
                results['campaigns'].append(stage_result)
            else:
                # For later stages, just schedule it (create it and schedule it)
                stage_template['status'] = 'SCHEDULED'
                stage_campaign = await self._create_campaign(stage_template, recipients_data)
                
                # Add minimal result info for later stages
                stage_result = {
                    'campaign_id': stage_campaign.id,
                    'stage': stage,
                    'scheduled_at': scheduled_time.isoformat(),
                    'status': 'SCHEDULED'
                }
            
            # Add to results
            results['multi_stage']['stage_campaigns'].append({
                'stage': stage,
                'campaign_id': stage_result.get('campaign_id'),
                'scheduled_at': scheduled_time.isoformat()
            })
        
        return results
    
    def _apply_template_from_id(self, campaign_template: Dict[str, Any], template_id: str) -> None:
        """
        Apply a specific template to the campaign template.
        
        Args:
            campaign_template: Campaign template to modify
            template_id: Template ID to apply
        """
        # Get templates from the campaign template
        templates = campaign_template.get('templates', {})
        
        # Find the template with the matching ID
        for template_key, template_data in templates.items():
            if isinstance(template_data, dict) and template_data.get('template_id') == template_id:
                # Apply template properties to the campaign template
                if 'subject' in template_data:
                    campaign_template['subject'] = template_data['subject']
                
                if 'body' in template_data:
                    # For simplicity, treating all templates as HTML
                    campaign_template['template_html'] = template_data['body']
                    campaign_template['template_text'] = template_data['body']
                
                if 'from_name' in template_data:
                    campaign_template['from_name'] = template_data['from_name']
                
                if 'reply_to' in template_data:
                    campaign_template['reply_to'] = template_data['reply_to']
                
                logger.debug(f"Applied template {template_id} from {template_key}")
                return
        
        logger.warning(f"Template ID {template_id} not found in campaign templates")
    
    async def _process_standard_campaign(
        self, 
        campaign_template: Dict[str, Any], 
        recipients_data: List[Dict[str, Any]],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a standard campaign.
        
        Args:
            campaign_template: Campaign template data
            recipients_data: List of recipient data
            task: Original task data
            
        Returns:
            Dictionary with processing results
        """
        # Create campaign
        campaign = await self._create_campaign(campaign_template, recipients_data)
        
        # Process campaign
        success = await self.campaign_service.send_campaign(campaign.id)
        
        # Get campaign statistics after processing
        campaign = await self.campaign_repository.get_by_id(campaign.id)
        stats = await self.campaign_service.get_campaign_statistics(campaign.id)
        
        # Prepare result
        result = {
            'campaign_id': campaign.id,
            'status': campaign.status.name,
            'processed_at': datetime.utcnow().isoformat(),
            'statistics': stats,
            'success': success
        }
        
        return result
    
    async def _create_campaign(self, campaign_data: Dict[str, Any], recipients_data: List[Dict[str, Any]]) -> Campaign:
        """
        Create a campaign from template and recipients data.
        
        Args:
            campaign_data: Campaign template data
            recipients_data: List of recipient data
            
        Returns:
            Created campaign
        """
        # Create campaign from template
        create_data = {
            'id': campaign_data.get('id') or str(uuid.uuid4()),
            'name': campaign_data.get('name', 'Unnamed Campaign'),
            'description': campaign_data.get('description', ''),
            'subject': campaign_data.get('subject', ''),
            'from_email': campaign_data.get('from_email', ''),
            'reply_to': campaign_data.get('reply_to', ''),
            'template_html': campaign_data.get('template_html', ''),
            'template_text': campaign_data.get('template_text', ''),
            'tags': campaign_data.get('tags', []),
            'track_opens': campaign_data.get('track_opens', True),
            'track_clicks': campaign_data.get('track_clicks', True),
            'custom_attributes': campaign_data.get('custom_attributes', {})
        }
        
        # Add scheduled time if present
        if 'scheduled_at' in campaign_data:
            try:
                scheduled_at = datetime.fromisoformat(campaign_data['scheduled_at'].replace('Z', '+00:00'))
                create_data['scheduled_at'] = scheduled_at
                # Set status to SCHEDULED if in the future
                if scheduled_at > datetime.utcnow():
                    create_data['status'] = CampaignStatus.SCHEDULED.name
            except (ValueError, TypeError):
                logger.warning(f"Invalid scheduled_at time format: {campaign_data['scheduled_at']}")
        
        # Create recipients
        recipients = []
        for recipient_data in recipients_data:
            recipient = Recipient(
                email=recipient_data.get('email'),
                first_name=recipient_data.get('first_name', ''),
                last_name=recipient_data.get('last_name', ''),
                custom_attributes=recipient_data.get('custom_attributes', {}),
                status=RecipientStatus.PENDING,
                tracking_id=recipient_data.get('tracking_id') or str(uuid.uuid4())
            )
            recipients.append(recipient)
        
        create_data['recipients'] = recipients
        
        # Create campaign
        campaign = await self.campaign_service.create_campaign(create_data)
        return campaign
    
    async def process_scheduled_campaigns(self) -> Dict[str, int]:
        """
        Process all campaigns scheduled to run now.
        
        Returns:
            Dictionary with counts of campaigns processed
        """
        return await self.campaign_service.process_scheduled_campaigns() 