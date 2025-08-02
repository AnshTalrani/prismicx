"""
Dependency injection module.

This module provides functions for dependency injection in FastAPI.
"""

import logging
from typing import Callable, Dict, Any

from fastapi import Depends

from ..application.services.campaign_service import CampaignService
from ..application.services.email_service import EmailService
from ..application.services.template_service import TemplateService
from .repositories.campaign_repository import CampaignRepository
from .repositories.template_repository import TemplateRepository
from .persistence.database import Database
from .auth.dependencies import get_current_user

logger = logging.getLogger(__name__)


# Database dependency
def get_database() -> Database:
    """Get a database instance."""
    return Database()


# Repository dependencies
def get_campaign_repository(
    database: Database = Depends(get_database)
) -> CampaignRepository:
    """Get a campaign repository instance."""
    return CampaignRepository(database=database)


def get_template_repository(
    database: Database = Depends(get_database)
) -> TemplateRepository:
    """Get a template repository instance."""
    return TemplateRepository(database=database)


# Service dependencies
def get_email_service() -> EmailService:
    """Get an email service instance."""
    return EmailService()


def get_template_service(
    template_repository: TemplateRepository = Depends(get_template_repository)
) -> TemplateService:
    """Get a template service instance."""
    return TemplateService(template_repository=template_repository)


def get_campaign_service(
    campaign_repository: CampaignRepository = Depends(get_campaign_repository),
    template_repository: TemplateRepository = Depends(get_template_repository),
    email_service: EmailService = Depends(get_email_service)
) -> CampaignService:
    """Get a campaign service instance."""
    return CampaignService(
        campaign_repository=campaign_repository,
        template_repository=template_repository,
        email_service=email_service
    ) 