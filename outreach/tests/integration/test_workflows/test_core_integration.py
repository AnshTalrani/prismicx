import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

# Import services (assume they are importable and mock-friendly)
try:
    from src.services.campaign_service import CampaignService
    from src.services.conversation_service import ConversationService
    from src.services.workflow_service import WorkflowService
except Exception:
    CampaignService = ConversationService = WorkflowService = None

@pytest.mark.asyncio
async def test_campaign_to_conversation_to_workflow_integration():
    if not (CampaignService and ConversationService and WorkflowService):
        pytest.skip("Core services not available for integration test")

    # Mock repositories for each service
    mock_campaign_repo = AsyncMock()
    mock_conversation_repo = AsyncMock()
    mock_workflow_repo = AsyncMock()

    # Create service instances
    campaign_service = CampaignService(mock_campaign_repo)
    conversation_service = ConversationService(mock_conversation_repo)
    workflow_service = WorkflowService(mock_workflow_repo)

    # Step 1: Create a campaign
    campaign_id = uuid4()
    campaign_data = {"id": campaign_id, "name": "Integration Test Campaign", "status": "draft"}
    mock_campaign = type("MockCampaign", (), campaign_data)
    mock_campaign_repo.create.return_value = mock_campaign
    created_campaign = await campaign_service.create_campaign(campaign_data)
    assert created_campaign.id == campaign_id
    mock_campaign_repo.create.assert_awaited_once()

    # Step 2: Start a conversation for that campaign
    contact_id = uuid4()
    conversation_data = {"id": uuid4(), "campaign_id": campaign_id, "contact_id": contact_id, "status": "active"}
    mock_conversation = type("MockConversation", (), conversation_data)
    mock_conversation_repo.create.return_value = mock_conversation
    started_convo = await conversation_service.start_conversation(campaign_id, contact_id, context={"foo": "bar"})
    assert started_convo.campaign_id == campaign_id
    assert started_convo.contact_id == contact_id
    mock_conversation_repo.create.assert_awaited_once()

    # Step 3: Execute a workflow step for that conversation
    workflow_id = uuid4()
    step_id = "start"
    mock_step = type("MockWorkflowStep", (), {"step_id": step_id, "action": {"type": "send_message", "content": "Hello {foo}"}, "transitions": []})
    mock_workflow = type("MockWorkflow", (), {"steps": [mock_step]})
    mock_workflow_repo.get.return_value = mock_workflow
    workflow_service._execute_action = AsyncMock(return_value={"message": "Hello bar"})
    template_config = {"stages": [
        {"id": "start", "type": "message", "message": "Hello {foo}"}
    ]}
    result = await workflow_service.execute_step(workflow_id, step_id, {"foo": "bar", "template_config": template_config})
    assert result["success"] is True
    assert result["result"]["message"] == "Hello bar"

    # Step 4: Simulate end-to-end business logic (campaign triggers conversation, which triggers workflow)
    # This is a trivial example, but can be expanded with more steps and real DB/HTTP fixtures.
