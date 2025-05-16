"""
Campaign template converter service.

Converts campaign_marketing.json templates to internal campaign models.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from ...models.campaign import Campaign, CampaignStatus, Recipient, RecipientStatus

logger = logging.getLogger(__name__)


class CampaignTemplateConverter:
    """Service for converting external campaign templates to internal models."""
    
    def convert_template_to_campaign(
        self, 
        template: Dict[str, Any], 
        recipients: List[Dict[str, Any]],
        batch_id: str = None
    ) -> Campaign:
        """
        Convert a campaign_marketing.json template to an internal Campaign model.
        
        Args:
            template: Campaign template in marketing format
            recipients: List of recipient data
            batch_id: Optional batch identifier
            
        Returns:
            Converted Campaign object
        """
        # Extract campaign data
        campaign_data = template.get("campaign", {})
        templates_data = template.get("templates", {})
        ab_testing = template.get("ab_testing", {})
        analytics = template.get("analytics", {})
        workflow = template.get("workflow", {})
        
        # Create recipient objects
        recipient_objects = []
        for recipient_data in recipients:
            recipient = Recipient(
                email=recipient_data.get("email"),
                first_name=recipient_data.get("first_name"),
                last_name=recipient_data.get("last_name"),
                custom_attributes=recipient_data.get("custom_attributes", {}),
                tracking_id=str(uuid.uuid4()),
                status=RecipientStatus.PENDING
            )
            recipient_objects.append(recipient)
        
        # Get email subject and from_email
        subject = ""
        from_email = ""
        reply_to = None
        
        # Attempt to extract email details from the first template
        for template_key, template_data in templates_data.items():
            if isinstance(template_data, dict):
                if "subject" in template_data:
                    subject = template_data["subject"]
                if "from_email" in template_data:
                    from_email = template_data["from_email"]
                elif "from_name" in template_data:
                    from_email = f"{template_data['from_name']} <noreply@example.com>"
                if "reply_to" in template_data:
                    reply_to = template_data["reply_to"]
                    
                # If we found subject and from_email, we can break
                if subject and from_email:
                    break
        
        # If no from_email found, use default
        if not from_email:
            from_email = "Marketing <noreply@example.com>"
            
        # If no subject found, use campaign name
        if not subject and "name" in campaign_data:
            subject = campaign_data["name"]
        
        # Get template content
        template_html = None
        template_text = None
        template_id = None
        
        # Try to find the first email template
        for template_key, template_data in templates_data.items():
            if isinstance(template_data, dict) and template_data.get("content_type") == "email":
                if "body" in template_data:
                    if template_data.get("format", "html") == "html":
                        template_html = template_data["body"]
                    else:
                        template_text = template_data["body"]
                if "template_id" in template_data:
                    template_id = template_data["template_id"]
                    
                # If we found HTML or template ID, we can break
                if template_html or template_id:
                    break
        
        # Generate campaign ID and timestamps
        campaign_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Generate a batch ID if not provided
        if not batch_id:
            batch_id = str(uuid.uuid4())
        
        # Create custom attributes with batch information
        custom_attributes = {
            "batch_id": batch_id,
            "batch_size": len(recipient_objects),
            "campaign_template_type": "marketing_json"
        }
        
        # Add any product data
        if "product_data" in campaign_data:
            custom_attributes["product_data"] = campaign_data["product_data"]
        
        # Create campaign
        campaign = Campaign(
            id=campaign_id,
            name=campaign_data.get("name", "Campaign from Template"),
            description=campaign_data.get("description", ""),
            subject=subject,
            from_email=from_email,
            reply_to=reply_to,
            template_id=template_id,
            template_html=template_html,
            template_text=template_text,
            recipients=recipient_objects,
            tags=campaign_data.get("tags", []),
            track_opens=analytics.get("track_opens", True) if analytics else True,
            track_clicks=analytics.get("track_clicks", True) if analytics else True,
            custom_attributes=custom_attributes,
            status=CampaignStatus.DRAFT,
            created_at=now,
            updated_at=now
        )
        
        # Set scheduled time if provided
        if "scheduled_time" in campaign_data:
            try:
                scheduled_time = campaign_data["scheduled_time"]
                # Convert string to datetime
                if isinstance(scheduled_time, str):
                    # Handle ISO format with Z
                    if scheduled_time.endswith('Z'):
                        scheduled_time = scheduled_time[:-1] + '+00:00'
                    campaign.scheduled_at = datetime.fromisoformat(scheduled_time)
                elif isinstance(scheduled_time, datetime):
                    campaign.scheduled_at = scheduled_time
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid scheduled_time format: {e}")
        
        return campaign 