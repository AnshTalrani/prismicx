"""
Entity repository manager for storing and retrieving extracted entities.
Determines which repository to use based on entity type and configuration.
"""

import logging
from typing import Dict, List, Any, Optional

from src.config.config_inheritance import ConfigInheritance
from src.clients.system_users_repository_client import SystemUsersRepositoryClient
from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient

class EntityRepositoryManager:
    """
    Entity repository manager for storing and retrieving extracted entities.
    Coordinates storage between system and campaign repositories.
    """
    
    def __init__(self):
        """Initialize the entity repository manager."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        self.system_repo_client = SystemUsersRepositoryClient()
        self.campaign_repo_client = CampaignUsersRepositoryClient()
    
    # ... rest of the file remains the same 