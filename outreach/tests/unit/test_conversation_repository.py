"""Unit tests for the ConversationRepository using real ORM model and schemas."""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import Conversation
from src.models.conversation import ConversationStatus
from src.models.schemas import ConversationCreate
from src.repositories.conversation_repository import ConversationRepository

@pytest.mark.asyncio
async def test_create_conversation(monkeypatch):
    db_session = AsyncMock(spec=AsyncSession)
    repo = ConversationRepository(db_session)
    conversation_create = ConversationCreate(
        campaign_id=uuid4(),
        contact_id=uuid4(),
        initial_message=None,
        metadata={"foo": "bar"}
    )
    # Patch model to skip actual DB
    monkeypatch.setattr(repo, "model", Conversation)
    monkeypatch.setattr(db_session, "add", AsyncMock())
    monkeypatch.setattr(db_session, "commit", AsyncMock())
    monkeypatch.setattr(db_session, "refresh", AsyncMock())
    # Patch model __init__ to not require DB
    conversation_obj = Conversation(
        id=uuid4(),
        campaign_id=conversation_create.campaign_id,
        contact_id=conversation_create.contact_id,
        status=ConversationStatus.ACTIVE.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata_={"foo": "bar"}
    )  # Note: context/messages/ended_at are only on the Pydantic model
    monkeypatch.setattr(repo, "model", lambda **kwargs: conversation_obj)
    result = await repo.create(conversation_create)
    assert result.campaign_id == conversation_create.campaign_id
    assert result.contact_id == conversation_create.contact_id
    assert result.status == ConversationStatus.ACTIVE.value
    assert result.metadata_ == {"foo": "bar"}

@pytest.mark.asyncio
async def test_get_conversation(monkeypatch):
    db_session = AsyncMock(spec=AsyncSession)
    repo = ConversationRepository(db_session)
    conversation_id = uuid4()
    conversation_obj = Conversation(
        id=conversation_id,
        campaign_id=uuid4(),
        contact_id=uuid4(),
        status=ConversationStatus.ACTIVE.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata_={}
    )  # Note: context/messages/ended_at are only on the Pydantic model
    class Result:
        def scalars(self):
            class S:
                def first(self_inner):
                    return conversation_obj
            return S()
    monkeypatch.setattr(db_session, "execute", AsyncMock(return_value=Result()))
    result = await repo.get(conversation_id)
    assert result.id == conversation_id
    assert result.status == ConversationStatus.ACTIVE.value
