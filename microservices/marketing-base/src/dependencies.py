"""
Dependency injection module.

This module provides functions for dependency injection in FastAPI routes,
creating and managing service instances.
"""

import logging
from typing import Optional

from fastapi import Depends

from .repositories.campaign_repository import CampaignRepository
from .services.campaign_service import CampaignService
from .services.email_service import EmailService
from .services.template_service import TemplateService

logger = logging.getLogger(__name__)

# Global service instances for reuse
_campaign_repository: Optional[CampaignRepository] = None
_campaign_service: Optional[CampaignService] = None
_email_service: Optional[EmailService] = None
_template_service: Optional[TemplateService] = None


def get_campaign_repository() -> CampaignRepository:
    """
    Get or create a CampaignRepository instance.
    
    Returns:
        A CampaignRepository instance.
    """
    global _campaign_repository
    if _campaign_repository is None:
        logger.debug("Creating new CampaignRepository instance")
        _campaign_repository = CampaignRepository()
    return _campaign_repository


def get_email_service() -> EmailService:
    """
    Get or create an EmailService instance.
    
    Returns:
        An EmailService instance.
    """
    global _email_service
    if _email_service is None:
        logger.debug("Creating new EmailService instance")
        _email_service = EmailService()
    return _email_service


def get_template_service() -> TemplateService:
    """
    Get or create a TemplateService instance.
    
    Returns:
        A TemplateService instance.
    """
    global _template_service
    if _template_service is None:
        logger.debug("Creating new TemplateService instance")
        _template_service = TemplateService()
    return _template_service


def get_campaign_service(
    campaign_repository: CampaignRepository = Depends(get_campaign_repository),
    email_service: EmailService = Depends(get_email_service),
    template_service: TemplateService = Depends(get_template_service)
) -> CampaignService:
    """
    Get or create a CampaignService instance.
    
    Args:
        campaign_repository: A CampaignRepository instance.
        email_service: An EmailService instance.
        template_service: A TemplateService instance.
        
    Returns:
        A CampaignService instance.
    """
    global _campaign_service
    if _campaign_service is None:
        logger.debug("Creating new CampaignService instance")
        _campaign_service = CampaignService(
            campaign_repository=campaign_repository,
            email_service=email_service,
            template_service=template_service
        )
    return _campaign_service 