"""
Email Component Module

This module provides the EmailComponent class for sending emails in communication campaigns.
It integrates with email delivery services and handles templating, personalization, and tracking.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union
import structlog
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import jinja2

from src.processing.base_component import BaseComponent
from src.common.monitoring import get_metrics

logger = structlog.get_logger(__name__)

class EmailComponent(BaseComponent):
    """
    Component for sending emails as part of communication campaigns.
    
    This component handles:
    - Email template rendering with personalization
    - SMTP delivery
    - Tracking links and open pixels
    - Delivery status tracking
    """
    
    def __init__(
        self, 
        component_id: str,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        default_sender: str = "no-reply@example.com",
        template_dir: Optional[str] = None,
        tracking_domain: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the email component.
        
        Args:
            component_id: Unique identifier for this component
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: Optional SMTP authentication username
            smtp_password: Optional SMTP authentication password
            use_tls: Whether to use TLS for SMTP connection
            default_sender: Default sender email address
            template_dir: Directory containing email templates
            tracking_domain: Domain for tracking links and pixels
            **kwargs: Additional parameters for the base component
        """
        super().__init__(
            component_id=component_id,
            component_type="email_sender",
            **kwargs
        )
        
        # SMTP configuration
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.default_sender = default_sender
        
        # Templating
        self.template_dir = template_dir
        self.jinja_env = None
        if template_dir:
            self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir),
                autoescape=True
            )
        
        # Tracking
        self.tracking_domain = tracking_domain
        
        # Connection state
        self._smtp_client = None
        self._connected = False
        self._connection_attempts = 0
        self._last_connection_time = 0
        
        logger.info(
            "EmailComponent initialized",
            component_id=component_id,
            smtp_host=smtp_host,
            smtp_port=smtp_port
        )
    
    async def initialize(self) -> bool:
        """
        Initialize the email component.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Test SMTP connection
            await self._connect_smtp()
            await self._disconnect_smtp()
            
            # Initialize successful
            logger.info(
                "EmailComponent initialized successfully", 
                component_id=self.component_id
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to initialize EmailComponent", 
                error=str(e),
                component_id=self.component_id
            )
            return False
    
    async def shutdown(self) -> None:
        """
        Shutdown the email component, cleaning up resources.
        """
        await self._disconnect_smtp()
        logger.info("EmailComponent shutdown complete", component_id=self.component_id)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an email sending request.
        
        Args:
            input_data: Dictionary containing email information:
                - recipient: Email address of the recipient
                - subject: Email subject
                - body_html: HTML body content (optional)
                - body_text: Plain text body content (optional)
                - template_name: Template name to use (optional)
                - template_data: Data for template rendering (optional)
                - sender: Sender email address (optional, uses default_sender if not provided)
                - reply_to: Reply-To email address (optional)
                - cc: List of CC recipients (optional)
                - bcc: List of BCC recipients (optional)
                - campaign_id: ID of the campaign (optional, for tracking)
                - user_id: ID of the user (optional, for tracking)
                
        Returns:
            Dictionary with processing results:
                - success: Whether the email was sent successfully
                - message_id: ID of the sent message
                - error: Error message if sending failed
                - delivery_status: Delivery status information
                - tracking_info: Tracking information
        """
        start_time = time.time()
        metrics = get_metrics()
        
        if metrics:
            metrics.increment("email_requests", 1)
        
        # Validate required fields
        if "recipient" not in input_data:
            error_msg = "Missing required field: recipient"
            logger.error(error_msg, component_id=self.component_id)
            return {
                "success": False,
                "error": error_msg,
                "component_id": self.component_id
            }
        
        try:
            # Extract email parameters
            recipient = input_data["recipient"]
            sender = input_data.get("sender", self.default_sender)
            reply_to = input_data.get("reply_to")
            subject = input_data.get("subject", "(No subject)")
            cc = input_data.get("cc", [])
            bcc = input_data.get("bcc", [])
            campaign_id = input_data.get("campaign_id")
            user_id = input_data.get("user_id")
            
            # Connect to SMTP server if needed
            if not self._connected:
                await self._connect_smtp()
            
            # Prepare email content
            email_content = await self._prepare_email_content(input_data)
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["From"] = sender
            message["To"] = recipient
            message["Subject"] = subject
            
            if reply_to:
                message["Reply-To"] = reply_to
                
            if cc:
                if isinstance(cc, list):
                    message["Cc"] = ", ".join(cc)
                else:
                    message["Cc"] = cc
                    
            # Add text and HTML parts
            if "body_text" in email_content:
                message.attach(MIMEText(email_content["body_text"], "plain"))
                
            if "body_html" in email_content:
                message.attach(MIMEText(email_content["body_html"], "html"))
            
            # Add tracking info if applicable
            tracking_info = None
            if self.tracking_domain and campaign_id and user_id:
                tracking_info = self._add_tracking(
                    message, campaign_id, user_id, email_content
                )
            
            # Prepare recipient list (including CC)
            recipients = [recipient]
            if cc and isinstance(cc, list):
                recipients.extend(cc)
            elif cc:
                recipients.append(cc)
                
            if bcc and isinstance(bcc, list):
                recipients.extend(bcc)
            elif bcc:
                recipients.append(bcc)
            
            # Send the email
            send_result = await self._smtp_client.send_message(
                message, 
                sender=sender, 
                recipients=recipients
            )
            
            # Track metrics
            duration = time.time() - start_time
            if metrics:
                metrics.observe("email_send_time", duration)
                metrics.increment("emails_sent", 1)
            
            # Create response with success info
            response = {
                "success": True,
                "message_id": message.get("Message-ID", ""),
                "recipient": recipient,
                "subject": subject,
                "send_time": datetime.utcnow().isoformat(),
                "component_id": self.component_id,
                "duration": duration
            }
            
            if tracking_info:
                response["tracking_info"] = tracking_info
                
            logger.info(
                "Email sent successfully",
                recipient=recipient,
                subject=subject,
                campaign_id=campaign_id,
                user_id=user_id,
                duration=round(duration, 3)
            )
            
            return response
            
        except Exception as e:
            # Track error metrics
            if metrics:
                metrics.increment("email_errors", 1)
            
            error_msg = str(e)
            logger.error(
                "Error sending email",
                error=error_msg,
                recipient=input_data.get("recipient"),
                component_id=self.component_id
            )
            
            # Attempt to reconnect if it's a connection issue
            if "Connection" in error_msg or "Authentication" in error_msg:
                try:
                    await self._disconnect_smtp()
                    self._connected = False
                except Exception:
                    pass
            
            return {
                "success": False,
                "error": error_msg,
                "component_id": self.component_id
            }
    
    async def _connect_smtp(self) -> None:
        """
        Connect to the SMTP server.
        
        Raises:
            Exception: If connection fails
        """
        try:
            start_time = time.time()
            metrics = get_metrics()
            
            # Create SMTP client
            self._smtp_client = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.use_tls
            )
            
            # Connect and authenticate if needed
            await self._smtp_client.connect()
            
            if self.smtp_username and self.smtp_password:
                await self._smtp_client.login(self.smtp_username, self.smtp_password)
            
            self._connected = True
            self._connection_attempts += 1
            self._last_connection_time = time.time()
            
            # Track metrics
            duration = time.time() - start_time
            if metrics:
                metrics.observe("smtp_connection_time", duration)
                metrics.gauge("smtp_connected", 1)
            
            logger.debug(
                "Connected to SMTP server",
                host=self.smtp_host,
                port=self.smtp_port,
                duration=round(duration, 3)
            )
            
        except Exception as e:
            # Track error metrics
            if metrics:
                metrics.gauge("smtp_connected", 0)
                metrics.increment("smtp_connection_errors", 1)
            
            logger.error(
                "Failed to connect to SMTP server",
                error=str(e),
                host=self.smtp_host,
                port=self.smtp_port,
                attempt=self._connection_attempts + 1
            )
            raise
    
    async def _disconnect_smtp(self) -> None:
        """
        Disconnect from the SMTP server.
        """
        if self._smtp_client and self._connected:
            try:
                await self._smtp_client.quit()
                self._connected = False
                
                # Track metrics
                metrics = get_metrics()
                if metrics:
                    metrics.gauge("smtp_connected", 0)
                
                logger.debug(
                    "Disconnected from SMTP server",
                    host=self.smtp_host,
                    port=self.smtp_port
                )
                
            except Exception as e:
                logger.warning(
                    "Error disconnecting from SMTP server",
                    error=str(e),
                    host=self.smtp_host,
                    port=self.smtp_port
                )
    
    async def _prepare_email_content(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare email content, either from direct content or by rendering templates.
        
        Args:
            input_data: Input data containing email content or template information
            
        Returns:
            Dictionary with body_text and/or body_html
            
        Raises:
            ValueError: If neither direct content nor valid template information is provided
        """
        # Check if we have direct content
        if "body_html" in input_data or "body_text" in input_data:
            return {
                "body_html": input_data.get("body_html", ""),
                "body_text": input_data.get("body_text", "")
            }
        
        # Check if we have template information
        template_name = input_data.get("template_name")
        template_data = input_data.get("template_data", {})
        
        if not template_name or not self.jinja_env:
            raise ValueError(
                "Email content not provided: include body_html/body_text or template_name"
            )
        
        # Render the template
        try:
            # Try HTML template
            html_content = ""
            text_content = ""
            
            try:
                html_template = self.jinja_env.get_template(f"{template_name}.html")
                html_content = html_template.render(**template_data)
            except jinja2.exceptions.TemplateNotFound:
                pass
                
            try:
                text_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**template_data)
            except jinja2.exceptions.TemplateNotFound:
                # If no text template but we have HTML, generate text from HTML
                if html_content and not text_content:
                    # Simple HTML to text conversion (could be improved)
                    text_content = html_content.replace("<br>", "\n").replace("<br/>", "\n")
                    # Remove HTML tags
                    import re
                    text_content = re.sub(r'<[^>]*>', '', text_content)
            
            if not html_content and not text_content:
                raise ValueError(f"Template '{template_name}' not found")
                
            return {
                "body_html": html_content,
                "body_text": text_content
            }
            
        except Exception as e:
            logger.error(
                "Error rendering email template",
                error=str(e),
                template_name=template_name
            )
            raise ValueError(f"Error rendering template: {str(e)}")
    
    def _add_tracking(
        self, 
        message: MIMEMultipart,
        campaign_id: str,
        user_id: str,
        email_content: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Add tracking pixels and link tracking to the email.
        
        Args:
            message: Email message to modify
            campaign_id: Campaign ID for tracking
            user_id: User ID for tracking
            email_content: Email content dictionary
            
        Returns:
            Dictionary with tracking information
        """
        tracking_info = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "tracking_links": [],
            "has_open_pixel": False
        }
        
        # Only process if we have HTML content
        if "body_html" not in email_content or not email_content["body_html"]:
            return tracking_info
        
        html_content = email_content["body_html"]
        
        # Add open tracking pixel
        tracking_pixel_url = f"https://{self.tracking_domain}/p/{campaign_id}/{user_id}"
        pixel_html = f'<img src="{tracking_pixel_url}" width="1" height="1" alt="" />'
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{pixel_html}</body>")
        else:
            html_content = f"{html_content}{pixel_html}"
            
        tracking_info["has_open_pixel"] = True
        tracking_info["open_pixel_url"] = tracking_pixel_url
        
        # Add link tracking (basic implementation, could be improved)
        import re
        
        def replace_link(match):
            original_url = match.group(1)
            # Skip if it's already a tracking link or an anchor
            if self.tracking_domain in original_url or original_url.startswith("#"):
                return f'href="{original_url}"'
                
            # Create tracking link
            tracking_id = f"{len(tracking_info['tracking_links']) + 1}"
            tracking_url = f"https://{self.tracking_domain}/r/{campaign_id}/{user_id}/{tracking_id}"
            
            # Store tracking info
            tracking_info["tracking_links"].append({
                "tracking_id": tracking_id,
                "original_url": original_url,
                "tracking_url": tracking_url
            })
            
            return f'href="{tracking_url}"'
        
        # Replace links with tracking links
        html_content = re.sub(r'href="([^"]*)"', replace_link, html_content)
        
        # Update the message with modified content
        # First, remove existing html part
        for part in message.get_payload():
            if part.get_content_type() == "text/html":
                message.get_payload().remove(part)
                break
                
        # Add the new html part
        message.attach(MIMEText(html_content, "html"))
        
        return tracking_info
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the component parameters.
        
        Args:
            parameters: Dictionary of parameters to validate
            
        Returns:
            Dictionary of validated parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Required parameters
        required = ["smtp_host"]
        for req in required:
            if req not in parameters:
                raise ValueError(f"Missing required parameter: {req}")
        
        # Type validation
        if "smtp_port" in parameters and not isinstance(parameters["smtp_port"], int):
            raise ValueError("smtp_port must be an integer")
            
        if "use_tls" in parameters and not isinstance(parameters["use_tls"], bool):
            raise ValueError("use_tls must be a boolean")
        
        return parameters
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the component.
        
        Returns:
            Dictionary with component information
        """
        info = super().get_info()
        info.update({
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "use_tls": self.use_tls,
            "default_sender": self.default_sender,
            "template_dir": self.template_dir,
            "tracking_domain": self.tracking_domain,
            "connection_state": {
                "connected": self._connected,
                "connection_attempts": self._connection_attempts,
                "last_connection_time": self._last_connection_time
            }
        })
        return info 