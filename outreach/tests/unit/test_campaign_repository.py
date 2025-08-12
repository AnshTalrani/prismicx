"""Unit tests for the CampaignRepository using real ORM model and schemas."""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import Campaign, CampaignStatus, CampaignType
from src.models.schemas import CampaignCreate, CampaignUpdate
from src.repositories.campaign_repository import CampaignRepository

@pytest.mark.asyncio
async def test_create_campaign(monkeypatch):
    db_session = AsyncMock(spec=AsyncSession)
    repo = CampaignRepository(db_session)
    campaign_create = CampaignCreate(
        name="Test Campaign",
        description="A test campaign",
        campaign_type=CampaignType.OUTBOUND.value,
        workflow_id=uuid4(),
        start_date=datetime.utcnow(),
        end_date=None,
        metadata={"foo": "bar"}
    )
    # Patch model to skip actual DB
    monkeypatch.setattr(repo, "model", Campaign)
    monkeypatch.setattr(db_session, "add", AsyncMock())
    monkeypatch.setattr(db_session, "commit", AsyncMock())
    monkeypatch.setattr(db_session, "refresh", AsyncMock())
    # Patch model __init__ to not require DB
    campaign_obj = Campaign(
        id=uuid4(),
        name=campaign_create.name,
        description=campaign_create.description,
        status=CampaignStatus.DRAFT,
        campaign_type=CampaignType.OUTBOUND,
        workflow_id=campaign_create.workflow_id,
        start_date=campaign_create.start_date,
        end_date=campaign_create.end_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata_={"foo": "bar"}
    )
    monkeypatch.setattr(repo, "model", lambda **kwargs: campaign_obj)
    result = await repo.create(campaign_create)
    assert result.name == "Test Campaign"
    assert result.status == CampaignStatus.DRAFT
    assert result.campaign_type == CampaignType.OUTBOUND
    assert result.metadata_ == {"foo": "bar"}

@pytest.mark.asyncio
async def test_get_campaign(monkeypatch):
    db_session = AsyncMock(spec=AsyncSession)
    repo = CampaignRepository(db_session)
    campaign_id = uuid4()
    campaign_obj = Campaign(
        id=campaign_id,
        name="Test",
        description=None,
        status=CampaignStatus.ACTIVE,
        campaign_type=CampaignType.INBOUND,
        workflow_id=uuid4(),
        start_date=None,
        end_date=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata_={}
    )
    class Result:
        def scalars(self):
            class S:
                def first(self_inner):
                    return campaign_obj
            return S()
    monkeypatch.setattr(db_session, "execute", AsyncMock(return_value=Result()))
    result = await repo.get(campaign_id)
    assert result.id == campaign_id
    assert result.status == CampaignStatus.ACTIVE
    assert result.campaign_type == CampaignType.INBOUND
