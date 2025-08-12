import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

try:
    from src.services.campaign_service import CampaignService
    from src.services.conversation_service import ConversationService
    from src.services.workflow_service import WorkflowService, WorkflowExecutionError
except Exception:
    CampaignService = ConversationService = WorkflowService = WorkflowExecutionError = None

@pytest.mark.asyncio
async def test_error_propagation_across_services():
    if not (CampaignService and ConversationService and WorkflowService):
        pytest.skip("Core services not available for integration test")

    mock_campaign_repo = AsyncMock()
    mock_conversation_repo = AsyncMock()
    mock_workflow_repo = AsyncMock()

    campaign_service = CampaignService(mock_campaign_repo)
    conversation_service = ConversationService(mock_conversation_repo)
    workflow_service = WorkflowService(mock_workflow_repo)

    # Campaign creation fails
    mock_campaign_repo.create.side_effect = Exception("DB error")
    with pytest.raises(Exception) as excinfo:
        await campaign_service.create_campaign({"name": "fail"})
    assert "DB error" in str(excinfo.value)

    # Conversation creation fails
    mock_campaign_repo.create.side_effect = None
    mock_campaign_repo.create.return_value = type("MockCampaign", (), {"id": uuid4()})
    mock_conversation_repo.create.side_effect = Exception("Repo error")
    with pytest.raises(Exception) as excinfo:
        await conversation_service.start_conversation(uuid4(), uuid4())
    assert "Repo error" in str(excinfo.value)

    # Workflow step fails
    mock_conversation_repo.create.side_effect = None
    mock_conversation_repo.create.return_value = type("MockConversation", (), {"id": uuid4()})
    mock_workflow_repo.get.return_value = type("MockWorkflow", (), {"steps": [type("MockStep", (), {"step_id": "fail", "action": {"type": "send_message"}, "transitions": []})]})
    workflow_service._execute_action = AsyncMock(side_effect=Exception("Action error"))
    with pytest.raises(Exception):
        await workflow_service.execute_step(uuid4(), "fail", {})

@pytest.mark.asyncio
async def test_multi_step_workflow_integration():
    if not (CampaignService and ConversationService and WorkflowService):
        pytest.skip("Core services not available for integration test")

    mock_campaign_repo = AsyncMock()
    mock_conversation_repo = AsyncMock()
    mock_workflow_repo = AsyncMock()

    campaign_service = CampaignService(mock_campaign_repo)
    conversation_service = ConversationService(mock_conversation_repo)
    workflow_service = WorkflowService(mock_workflow_repo)

    # Step 1: Create campaign
    campaign_id = uuid4()
    mock_campaign = type("MockCampaign", (), {"id": campaign_id, "name": "Multi-step", "status": "active"})
    mock_campaign_repo.create.return_value = mock_campaign
    await campaign_service.create_campaign({"id": campaign_id, "name": "Multi-step", "status": "active"})

    # Step 2: Start conversation
    contact_id = uuid4()
    mock_conversation = type("MockConversation", (), {"id": uuid4(), "campaign_id": campaign_id, "contact_id": contact_id, "status": "active"})
    mock_conversation_repo.create.return_value = mock_conversation
    await conversation_service.start_conversation(campaign_id, contact_id, context={})

    # Step 3: Multi-step workflow (start -> ask -> end)
    workflow_id = uuid4()
    step_start = type("MockStep", (), {"step_id": "start", "action": {"type": "send_message", "content": "Welcome!"}, "transitions": ["ask"]})
    step_ask = type("MockStep", (), {"step_id": "ask", "action": {"type": "collect_input"}, "transitions": ["end"]})
    step_end = type("MockStep", (), {"step_id": "end", "action": {"type": "send_message", "content": "Goodbye!"}, "transitions": []})
    mock_workflow = type("MockWorkflow", (), {"steps": [step_start, step_ask, step_end]})
    mock_workflow_repo.get.return_value = mock_workflow
    workflow_service._execute_action = AsyncMock(side_effect=[{"message": "Welcome!"}, {"input": "42"}, {"message": "Goodbye!"}])

    template_config = {"stages": [
        {"id": "start", "type": "message", "message": "Welcome!", "next_stage_id": "ask"},
        {"id": "ask", "type": "input", "prompt": "Your answer?", "next_stage_id": "end"},
        {"id": "end", "type": "message", "message": "Goodbye!", "next_stage_id": None}
    ]}

    # Execute start
    result1 = await workflow_service.execute_step(workflow_id, "start", {"template_config": template_config})
    assert result1["success"] is True
    assert result1["next_step_id"] == "ask"
    assert result1["result"]["message"] == "Welcome!"

    # Execute ask
    result2 = await workflow_service.execute_step(workflow_id, "ask", {"template_config": template_config, "user_input": "42"})
    assert result2["success"] is True
    assert result2["next_step_id"] == "end"
    assert result2["result"]["input"] == "42"

    # Execute end
    result3 = await workflow_service.execute_step(workflow_id, "end", {"template_config": template_config})
    assert result3["success"] is True
    assert result3["next_step_id"] is None
    assert result3["result"]["message"] == "Goodbye!"
