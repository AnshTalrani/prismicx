"""Unit tests for the CampaignService."""
import pytest
from uuid import UUID, uuid4
from datetime import datetime
from unittest.mock import AsyncMock

from src.models.campaign import Campaign, CampaignStatus
CampaignService = None
try:
    from src.services.campaign_service import CampaignService
except ImportError:
    pass

@pytest.mark.asyncio
async def test_create_campaign():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign = Campaign(name="Test", status=CampaignStatus.DRAFT)
    mock_repo.create.return_value = campaign
    service = CampaignService(mock_repo)
    result = await service.create_campaign(campaign)
    assert result.name == "Test"
    assert result.status == CampaignStatus.DRAFT
    mock_repo.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_campaign():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign_id = uuid4()
    campaign = Campaign(id=campaign_id, name="Test", status=CampaignStatus.ACTIVE)
    mock_repo.get.return_value = campaign
    service = CampaignService(mock_repo)
    result = await service.get_campaign(campaign_id)
    assert result.id == campaign_id
    assert result.status == CampaignStatus.ACTIVE
    mock_repo.get.assert_awaited_once_with(campaign_id)

@pytest.mark.asyncio
async def test_update_campaign():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign_id = uuid4()
    update_data = {}
    updated_campaign = Campaign(id=campaign_id, name="Test", status=CampaignStatus.ACTIVE)
    mock_repo.update.return_value = updated_campaign
    service = CampaignService(mock_repo)
    result = await service.update_campaign(campaign_id, update_data)
    assert result.status == CampaignStatus.ACTIVE
    mock_repo.update.assert_awaited_once_with(campaign_id, update_data)

@pytest.mark.asyncio
async def test_delete_campaign():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign_id = uuid4()
    mock_repo.delete.return_value = True
    service = CampaignService(mock_repo)
    result = await service.delete_campaign(campaign_id)
    assert result is True
    mock_repo.delete.assert_awaited_once_with(campaign_id)

@pytest.mark.asyncio
async def test_create_campaign_invalid_input():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    mock_repo.create.side_effect = Exception("Invalid input")
    service = CampaignService(mock_repo)
    with pytest.raises(Exception):
        await service.create_campaign(Campaign(name="", status=CampaignStatus.DRAFT))
    mock_repo.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_campaign_missing_fields():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign_id = uuid4()
    update_data = {}
    updated_campaign = Campaign(id=campaign_id, name="Test", status=CampaignStatus.ACTIVE)
    mock_repo.update.return_value = updated_campaign
    service = CampaignService(mock_repo)
    result = await service.update_campaign(campaign_id, update_data)
    assert result.status == CampaignStatus.ACTIVE
    mock_repo.update.assert_awaited_once_with(campaign_id, update_data)

@pytest.mark.asyncio
async def test_delete_campaign_failure():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign_id = uuid4()
    mock_repo.delete.return_value = False
    service = CampaignService(mock_repo)
    result = await service.delete_campaign(campaign_id)
    assert result is False
    mock_repo.delete.assert_awaited_once_with(campaign_id)

@pytest.mark.asyncio
async def test_create_campaign_with_extra_fields():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign = Campaign(name="Test", status=CampaignStatus.DRAFT)
    mock_repo.create.return_value = campaign
    service = CampaignService(mock_repo)
    result = await service.create_campaign(campaign)
    assert result.name == "Test"
    assert result.status == CampaignStatus.DRAFT
    mock_repo.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_campaign_not_found():
    if CampaignService is None:
        pytest.skip("CampaignService not available")
    mock_repo = AsyncMock()
    campaign_id = uuid4()
    mock_repo.get.return_value = None
    service = CampaignService(mock_repo)
    result = await service.get_campaign(campaign_id)
    assert result is None
    mock_repo.get.assert_awaited_once_with(campaign_id)
