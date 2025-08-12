"""Test configuration and fixtures for unit tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

@pytest.fixture
def mock_campaign_repo():
    """Mock campaign repository."""
    repo = AsyncMock()
    repo.get.return_value = None
    return repo

@pytest.fixture
def mock_conversation_repo():
    """Mock conversation repository."""
    return AsyncMock()

@pytest.fixture
def mock_workflow_repo():
    """Mock workflow repository."""
    return AsyncMock()

@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        "id": str(uuid4()),
        "name": "Test Campaign",
        "description": "A test campaign",
        "status": "draft",
        "workflow_id": str(uuid4()),
        "contact_list_id": str(uuid4()),
        "settings": {"rate_limit_delay": 1.0},
    }
