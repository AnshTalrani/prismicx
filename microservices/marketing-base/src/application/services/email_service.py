"""
Email service for sending marketing emails.

This module handles email delivery, including connection to SMTP servers, 
formatting email content, and tracking delivery status.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Any, Union

from src.config import get_config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        """Initialize the email service with configuration."""
        self.config = get_config()
        
        # Set default values from config
        self.smtp_host = self.config.smtp_host
        self.smtp_port = self.config.smtp_port
        self.smtp_username = self.config.smtp_username
        self.smtp_password = self.config.smtp_password
        self.smtp_use_tls = self.config.smtp_use_tls
        self.from_email = getattr(self.config, 'email_from', None)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that required SMTP configuration is present."""
        if not self.smtp_host:
            logger.warning("SMTP host not configured")
        
        if not self.smtp_port:
            logger.warning("SMTP port not configured, using default 587")
            self.smtp_port = 587
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Optional plain text content of the email
            from_email: Sender email address (defaults to configured from_email)
            reply_to: Reply-to email address
            cc: List of CC recipients
            bcc: List of BCC recipients
            headers: Optional additional email headers
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email or self.from_email
            msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
                
            if cc:
                msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc
                
            # Add headers if provided
            if headers:
                for key, value in headers.items():
                    msg[key] = value
            
            # Always add plain text version first (as per RFC 2046)
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            elif html_content:
                # Generate simple text from HTML if no text provided
                msg.attach(MIMEText("Please view this email with an HTML-compatible email client.", 'plain'))
            
            # Add HTML version
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
            
            # Calculate all recipients for sending
            all_recipients = [to_email]
            if cc:
                all_recipients.extend(cc if isinstance(cc, list) else [cc])
            if bcc:
                all_recipients.extend(bcc if isinstance(bcc, list) else [bcc])
            
            # Connect to SMTP server
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Login if credentials are provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # Send the email
            server.sendmail(msg['From'], all_recipients, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_batch_emails(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_template: str,
        text_template: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, int]:
        """
        Send emails to multiple recipients.
        
        Args:
            recipients: List of recipient dictionaries with at least 'email' key
            subject: Email subject
            html_template: HTML template for email content
            text_template: Optional plain text template for email content
            from_email: Sender email address (defaults to configured from_email)
            reply_to: Reply-to email address
            headers: Optional additional email headers
            
        Returns:
            Dictionary with counts of success and failure
        """
        results = {
            'sent': 0,
            'failed': 0
        }
        
        for recipient in recipients:
            if 'email' not in recipient:
                logger.warning(f"Recipient missing email address: {recipient}")
                results['failed'] += 1
                continue
            
            # Personalize templates for this recipient
            personalized_html = self._personalize_template(html_template, recipient)
            personalized_text = None
            if text_template:
                personalized_text = self._personalize_template(text_template, recipient)
            
            # Send the email
            success = await self.send_email(
                to_email=recipient['email'],
                subject=subject,
                html_content=personalized_html,
                text_content=personalized_text,
                from_email=from_email,
                reply_to=reply_to,
                headers=headers
            )
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def _personalize_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        Simple template personalization using string replacement.
        
        Args:
            template: Template string
            data: Dictionary of variables to replace
            
        Returns:
            Personalized template string
        """
        result = template
        
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result 