"""
Email Client

This module provides integration with email service providers.
It handles campaign sending, tracking, and email delivery.
"""

import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ...domain.models.email_template import EmailTemplate
from ...domain.exceptions.email_exceptions import (
    EmailClientError,
    EmailSendError,
    EmailTemplateError,
    EmailProviderError
)
from ..config.settings import get_settings
from ..tenant.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class EmailClient:
    """
    Client for interacting with email service providers.
    
    This client handles sending emails, managing campaigns, and retrieving
    email delivery statistics from the configured email provider.
    """
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize the email client.
        
        Args:
            provider_name: Name of the email provider to use (optional)
                If not provided, the default provider from settings will be used
        """
        self.settings = get_settings()
        self.provider_name = provider_name or self.settings.email.default_provider
        self.provider = self._initialize_provider(self.provider_name)
        self.connection = None
        self.is_connected = False
        logger.debug(f"Initialized EmailClient with provider: {self.provider_name}")
        
    def _initialize_provider(self, provider_name: str) -> Any:
        """
        Initialize the email provider client.
        
        Args:
            provider_name: Name of the provider to initialize
            
        Returns:
            Initialized provider instance
            
        Raises:
            EmailClientError: If provider initialization fails
        """
        try:
            if provider_name == "sendgrid":
                from .providers.sendgrid_provider import SendGridProvider
                return SendGridProvider(self.settings.email.sendgrid)
            elif provider_name == "mailchimp":
                from .providers.mailchimp_provider import MailchimpProvider
                return MailchimpProvider(self.settings.email.mailchimp)
            elif provider_name == "aws_ses":
                from .providers.aws_ses_provider import AWSESProvider
                return AWSESProvider(self.settings.email.aws_ses)
            elif provider_name == "smtp":
                from .providers.smtp_provider import SMTPProvider
                return SMTPProvider(self.settings.email.smtp)
            elif provider_name == "test":
                from .providers.test_provider import TestProvider
                return TestProvider()
            else:
                raise EmailClientError(f"Unsupported email provider: {provider_name}")
        except ImportError as e:
            logger.error(f"Failed to import provider module for {provider_name}: {str(e)}")
            raise EmailClientError(f"Email provider module not available: {provider_name}") from e
        except Exception as e:
            logger.error(f"Failed to initialize email provider {provider_name}: {str(e)}")
            raise EmailClientError(f"Email provider initialization failed: {str(e)}") from e
            
    async def connect(self) -> bool:
        """
        Establish connection to the email provider.
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            EmailProviderError: If connection fails
        """
        if self.is_connected:
            return True
            
        try:
            logger.debug(f"Connecting to email provider: {self.provider_name}")
            self.connection = await self.provider.connect()
            self.is_connected = True
            logger.info(f"Connected to email provider: {self.provider_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email provider {self.provider_name}: {str(e)}")
            self.is_connected = False
            raise EmailProviderError(f"Failed to connect to email provider: {str(e)}") from e
            
    async def close(self) -> None:
        """
        Close connection to the email provider.
        """
        if not self.is_connected or not self.connection:
            return
            
        try:
            logger.debug(f"Closing connection to email provider: {self.provider_name}")
            await self.provider.close()
            self.is_connected = False
            self.connection = None
            logger.info(f"Closed connection to email provider: {self.provider_name}")
        except Exception as e:
            logger.error(f"Error closing email provider connection: {str(e)}")
            
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        tracking_id: Optional[str] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a single email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            from_email: Sender email address (optional)
            text_content: Plain text content of the email (optional)
            reply_to: Reply-to email address (optional)
            cc: List of CC recipients (optional)
            bcc: List of BCC recipients (optional)
            attachments: List of attachment objects (optional)
            custom_headers: Dictionary of custom headers (optional)
            tracking_id: ID for tracking this email (optional)
            track_opens: Whether to track email opens (optional)
            track_clicks: Whether to track link clicks (optional)
            custom_attributes: Additional attributes for the email (optional)
            
        Returns:
            True if email sent successfully, False otherwise
            
        Raises:
            EmailSendError: If sending fails
        """
        # Validate input parameters
        if not to_email:
            raise EmailSendError("Recipient email address is required")
            
        if not subject:
            raise EmailSendError("Email subject is required")
            
        if not html_content:
            raise EmailSendError("Email content is required")
            
        # Ensure we have a connection
        if not self.is_connected:
            await self.connect()
            
        # Use default from_email if not provided
        from_email = from_email or self.settings.email.default_from_email
        
        # Add tenant identifier if available
        tenant_id = TenantContext.get_tenant_id()
        message_id = f"{tracking_id or ''}:{tenant_id or ''}"
        
        try:
            logger.debug(f"Sending email to {to_email} with subject '{subject}'")
            
            # Prepare email data
            email_data = {
                "to_email": to_email,
                "from_email": from_email,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content,
                "reply_to": reply_to,
                "cc": cc,
                "bcc": bcc,
                "attachments": attachments,
                "custom_headers": custom_headers or {},
                "tracking_id": message_id if message_id else tracking_id,
                "track_opens": track_opens,
                "track_clicks": track_clicks,
                "custom_attributes": custom_attributes or {}
            }
            
            # Send email through provider
            result = await self.provider.send_email(**email_data)
            
            if result:
                logger.info(f"Email sent successfully to {to_email}")
            else:
                logger.warning(f"Failed to send email to {to_email}")
                
            return result
            
        except Exception as e:
            error_msg = f"Error sending email to {to_email}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise EmailSendError(error_msg) from e
            
    async def send_campaign(
        self,
        campaign_id: str,
        template: EmailTemplate,
        recipients: List[Dict[str, Any]],
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a campaign to multiple recipients.
        
        Args:
            campaign_id: ID of the campaign
            template: Email template to use
            recipients: List of recipient data
            custom_attributes: Additional attributes for the campaign (optional)
            
        Returns:
            True if campaign sent successfully, False otherwise
            
        Raises:
            EmailTemplateError: If template is invalid
            EmailSendError: If sending fails
        """
        if not campaign_id:
            raise EmailSendError("Campaign ID is required")
            
        if not template:
            raise EmailTemplateError("Email template is required")
            
        if not recipients:
            raise EmailSendError("Recipients list is required")
            
        # Ensure we have a connection
        if not self.is_connected:
            await self.connect()
            
        try:
            logger.info(f"Sending campaign {campaign_id} to {len(recipients)} recipients")
            
            # Check if provider supports batch sending
            if hasattr(self.provider, 'send_campaign') and callable(getattr(self.provider, 'send_campaign')):
                # Send campaign through provider's campaign API
                result = await self.provider.send_campaign(
                    campaign_id=campaign_id,
                    template=template,
                    recipients=recipients,
                    custom_attributes=custom_attributes or {}
                )
            else:
                # Fall back to sending individual emails
                logger.debug(f"Provider does not support batch sending, sending individual emails")
                
                success_count = 0
                for recipient in recipients:
                    try:
                        # Personalize template for recipient
                        personalized_subject = self._personalize_content(template.subject, recipient)
                        personalized_html = self._personalize_content(template.html_content, recipient)
                        personalized_text = self._personalize_content(template.text_content, recipient) if template.text_content else None
                        
                        # Send email
                        success = await self.send_email(
                            to_email=recipient.get('email'),
                            subject=personalized_subject,
                            html_content=personalized_html,
                            text_content=personalized_text,
                            from_email=template.from_email,
                            reply_to=template.reply_to,
                            tracking_id=f"{campaign_id}:{recipient.get('id')}",
                            track_opens=template.track_opens,
                            track_clicks=template.track_clicks,
                            custom_attributes={
                                **custom_attributes or {},
                                **recipient
                            }
                        )
                        
                        if success:
                            success_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error sending campaign email to {recipient.get('email')}: {str(e)}")
                        
                # Calculate overall success
                result = success_count > 0 and success_count == len(recipients)
                logger.info(f"Campaign {campaign_id} sent with {success_count}/{len(recipients)} successful deliveries")
                
            return result
            
        except Exception as e:
            error_msg = f"Error sending campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise EmailSendError(error_msg) from e
            
    def _personalize_content(self, content: str, recipient_data: Dict[str, Any]) -> str:
        """
        Personalize content for a specific recipient.
        
        Args:
            content: Template content with placeholders
            recipient_data: Data for personalizing the template
            
        Returns:
            Personalized content
        """
        if not content:
            return ""
            
        personalized = content
        
        # Replace simple placeholders
        for key, value in recipient_data.items():
            if isinstance(value, (str, int, float, bool)):
                personalized = personalized.replace(f"{{{{{key}}}}}", str(value))
                
        # Handle nested attributes
        for key, value in recipient_data.items():
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, (str, int, float, bool)):
                        personalized = personalized.replace(f"{{{{{key}.{nested_key}}}}}", str(nested_value))
                        
        return personalized
        
    async def cancel_campaign(self, campaign_id: str) -> bool:
        """
        Cancel an ongoing campaign.
        
        Args:
            campaign_id: ID of the campaign to cancel
            
        Returns:
            True if campaign cancelled successfully, False otherwise
            
        Raises:
            EmailProviderError: If cancellation fails
        """
        if not campaign_id:
            raise EmailProviderError("Campaign ID is required")
            
        # Ensure we have a connection
        if not self.is_connected:
            await self.connect()
            
        try:
            logger.info(f"Cancelling campaign {campaign_id}")
            
            # Check if provider supports campaign cancellation
            if hasattr(self.provider, 'cancel_campaign') and callable(getattr(self.provider, 'cancel_campaign')):
                result = await self.provider.cancel_campaign(campaign_id)
                
                if result:
                    logger.info(f"Campaign {campaign_id} cancelled successfully")
                else:
                    logger.warning(f"Failed to cancel campaign {campaign_id}")
                    
                return result
            else:
                logger.warning(f"Provider does not support campaign cancellation")
                return False
                
        except Exception as e:
            error_msg = f"Error cancelling campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise EmailProviderError(error_msg) from e
            
    async def get_campaign_status(self, campaign_id: str) -> str:
        """
        Get the current status of a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Status string (DRAFT, SENDING, SENT, CANCELLED, COMPLETED, FAILED)
            
        Raises:
            EmailProviderError: If status retrieval fails
        """
        if not campaign_id:
            raise EmailProviderError("Campaign ID is required")
            
        # Ensure we have a connection
        if not self.is_connected:
            await self.connect()
            
        try:
            logger.debug(f"Getting status for campaign {campaign_id}")
            
            # Check if provider supports status retrieval
            if hasattr(self.provider, 'get_campaign_status') and callable(getattr(self.provider, 'get_campaign_status')):
                status = await self.provider.get_campaign_status(campaign_id)
                logger.debug(f"Campaign {campaign_id} status: {status}")
                return status
            else:
                logger.warning(f"Provider does not support campaign status retrieval")
                return "UNKNOWN"
                
        except Exception as e:
            error_msg = f"Error getting status for campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise EmailProviderError(error_msg) from e
            
    async def get_campaign_statistics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get statistics for a campaign.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Dictionary of campaign statistics
            
        Raises:
            EmailProviderError: If statistics retrieval fails
        """
        if not campaign_id:
            raise EmailProviderError("Campaign ID is required")
            
        # Ensure we have a connection
        if not self.is_connected:
            await self.connect()
            
        try:
            logger.debug(f"Getting statistics for campaign {campaign_id}")
            
            # Check if provider supports statistics retrieval
            if hasattr(self.provider, 'get_campaign_statistics') and callable(getattr(self.provider, 'get_campaign_statistics')):
                stats = await self.provider.get_campaign_statistics(campaign_id)
                return stats
            else:
                logger.warning(f"Provider does not support campaign statistics retrieval")
                return {
                    "sent": 0,
                    "delivered": 0,
                    "opened": 0,
                    "clicked": 0,
                    "bounced": 0,
                    "complained": 0,
                    "unsubscribed": 0
                }
                
        except Exception as e:
            error_msg = f"Error getting statistics for campaign {campaign_id}: {str(e)}"
            logger.error(error_msg)
            raise EmailProviderError(error_msg) from e
            
    async def generate_preview(
        self, 
        template: EmailTemplate, 
        sample_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a preview of an email from a template.
        
        Args:
            template: Email template
            sample_data: Sample data for personalization
            
        Returns:
            Dictionary with preview data (subject, html_content, text_content)
            
        Raises:
            EmailTemplateError: If template is invalid
        """
        if not template:
            raise EmailTemplateError("Email template is required")
            
        try:
            logger.debug(f"Generating preview for template ID: {template.id}")
            
            # Personalize template with sample data
            subject = self._personalize_content(template.subject, sample_data)
            html_content = self._personalize_content(template.html_content, sample_data)
            text_content = self._personalize_content(template.text_content, sample_data) if template.text_content else None
            
            # Check if provider has special preview functionality
            if hasattr(self.provider, 'generate_preview') and callable(getattr(self.provider, 'generate_preview')):
                preview = await self.provider.generate_preview(template, sample_data)
                return preview
            else:
                # Return basic preview
                return {
                    "subject": subject,
                    "html_content": html_content,
                    "text_content": text_content,
                    "from_email": template.from_email,
                    "preview_text": template.preview_text
                }
                
        except Exception as e:
            error_msg = f"Error generating preview for template {template.id}: {str(e)}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg) from e
            
    async def validate_template(self, template: EmailTemplate) -> Dict[str, Any]:
        """
        Validate an email template.
        
        Args:
            template: Email template to validate
            
        Returns:
            Validation results with any errors or warnings
            
        Raises:
            EmailTemplateError: If validation fails
        """
        if not template:
            raise EmailTemplateError("Email template is required")
            
        try:
            logger.debug(f"Validating template ID: {template.id}")
            
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Basic validation
            if not template.subject:
                validation_results["is_valid"] = False
                validation_results["errors"].append("Subject is required")
                
            if not template.html_content:
                validation_results["is_valid"] = False
                validation_results["errors"].append("HTML content is required")
                
            if not template.from_email:
                validation_results["is_valid"] = False
                validation_results["errors"].append("From email is required")
                
            # Check for common placeholder syntax issues
            for field in [template.subject, template.html_content, template.text_content]:
                if field and "{{" in field:
                    open_count = field.count("{{")
                    close_count = field.count("}}")
                    
                    if open_count != close_count:
                        validation_results["is_valid"] = False
                        validation_results["errors"].append(f"Mismatched placeholder delimiters: {open_count} opening vs {close_count} closing")
                        
            # Check if provider has additional validation
            if hasattr(self.provider, 'validate_template') and callable(getattr(self.provider, 'validate_template')):
                provider_validation = await self.provider.validate_template(template)
                
                # Merge provider validation results
                if not provider_validation["is_valid"]:
                    validation_results["is_valid"] = False
                
                validation_results["errors"].extend(provider_validation.get("errors", []))
                validation_results["warnings"].extend(provider_validation.get("warnings", []))
                
            return validation_results
            
        except Exception as e:
            error_msg = f"Error validating template {template.id}: {str(e)}"
            logger.error(error_msg)
            raise EmailTemplateError(error_msg) from e 