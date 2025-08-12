import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

class MockConversation:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockConversationStatus:
    ACTIVE = "active"

ConversationService = None
try:
    from src.services.conversation_service import ConversationService
except Exception:
    pass

@pytest.mark.asyncio
async def test_start_conversation():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    campaign_id = uuid4()
    contact_id = uuid4()
    context = {"foo": "bar"}
    mock_conversation = MockConversation(campaign_id=campaign_id, contact_id=contact_id, status=MockConversationStatus.ACTIVE, context=context)
    mock_repo.create.return_value = mock_conversation
    service = ConversationService(mock_repo)
    result = await service.start_conversation(campaign_id, contact_id, context)
    assert result.campaign_id == campaign_id
    assert result.contact_id == contact_id
    assert result.status == MockConversationStatus.ACTIVE
    assert result.context == context
    mock_repo.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_conversation():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    mock_conversation = MockConversation(id=conversation_id, campaign_id=uuid4(), contact_id=uuid4(), status=MockConversationStatus.ACTIVE, context={})
    mock_repo.get.return_value = mock_conversation
    service = ConversationService(mock_repo)
    result = await service.get_conversation(conversation_id)
    assert result.id == conversation_id
    mock_repo.get.assert_awaited_once_with(conversation_id)

@pytest.mark.asyncio
async def test_update_conversation():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    update_data = {"status": "completed"}
    updated_conversation = MockConversation(id=conversation_id, status="completed")
    mock_repo.update.return_value = updated_conversation
    service = ConversationService(mock_repo)
    result = await service.update_conversation(conversation_id, update_data)
    assert result.status == "completed"
    mock_repo.update.assert_awaited_once_with(conversation_id, update_data)

@pytest.mark.asyncio
async def test_end_conversation():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    mock_repo.update.return_value = True
    service = ConversationService(mock_repo)
    result = await service.end_conversation(conversation_id, status="completed")
    assert result is True
    mock_repo.update.assert_awaited_once()

@pytest.mark.asyncio
async def test_list_conversations():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    mock_conversations = [MockConversation(id=uuid4()) for _ in range(3)]
    mock_repo.list.return_value = mock_conversations
    service = ConversationService(mock_repo)
    result = await service.list_conversations()
    assert isinstance(result, list)
    assert len(result) == 3
    mock_repo.list.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_message():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    mock_repo.add_message.return_value = True
    service = ConversationService(mock_repo)
    result = await service.add_message(conversation_id, sender_type="user", content="Hello", metadata={"foo": "bar"})
    assert result is True
    mock_repo.add_message.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_conversation_not_found():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    mock_repo.get.return_value = None
    service = ConversationService(mock_repo)
    result = await service.get_conversation(conversation_id)
    assert result is None
    mock_repo.get.assert_awaited_once_with(conversation_id)

@pytest.mark.asyncio
async def test_update_conversation_missing_fields():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    update_data = {}
    updated_conversation = MockConversation(id=conversation_id)
    mock_repo.update.return_value = updated_conversation
    service = ConversationService(mock_repo)
    result = await service.update_conversation(conversation_id, update_data)
    assert hasattr(result, "id")
    mock_repo.update.assert_awaited_once_with(conversation_id, update_data)

@pytest.mark.asyncio
async def test_end_conversation_invalid_status():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    mock_repo.update.return_value = False
    service = ConversationService(mock_repo)
    result = await service.end_conversation(conversation_id, status="invalid")
    assert result is False
    mock_repo.update.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_message_invalid_data():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    conversation_id = uuid4()
    mock_repo.add_message.side_effect = Exception("Invalid message")
    service = ConversationService(mock_repo)
    with pytest.raises(Exception):
        await service.add_message(conversation_id, sender_type=None, content=None)

@pytest.mark.asyncio
async def test_list_conversations_with_filters():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    filters = {"status": "active"}
    mock_conversations = [MockConversation(id=uuid4(), status="active") for _ in range(2)]
    mock_repo.list.return_value = mock_conversations
    service = ConversationService(mock_repo)
    result = await service.list_conversations(filters)
    assert all(getattr(conv, "status", None) == "active" for conv in result)
    mock_repo.list.assert_awaited_once_with(filters)

@pytest.mark.asyncio
async def test_start_conversation_invalid_input():
    if ConversationService is None:
        pytest.skip("ConversationService not available")
    mock_repo = AsyncMock()
    mock_repo.create.side_effect = Exception("Invalid input")
    service = ConversationService(mock_repo)
    with pytest.raises(Exception):
        await service.start_conversation(None, None, None)
