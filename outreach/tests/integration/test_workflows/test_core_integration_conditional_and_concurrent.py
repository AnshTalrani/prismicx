import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

try:
    from src.services.campaign_service import CampaignService
    from src.services.conversation_service import ConversationService
    from src.services.workflow_service import WorkflowService
except Exception:
    CampaignService = ConversationService = WorkflowService = None

@pytest.mark.asyncio
async def test_conditional_workflow_transition():
    if not (CampaignService and ConversationService and WorkflowService):
        pytest.skip("Core services not available for integration test")

    mock_campaign_repo = AsyncMock()
    mock_conversation_repo = AsyncMock()
    mock_workflow_repo = AsyncMock()

    campaign_service = CampaignService(mock_campaign_repo)
    conversation_service = ConversationService(mock_conversation_repo)
    workflow_service = WorkflowService(mock_workflow_repo)

    # Setup campaign and conversation
    campaign_id = uuid4()
    contact_id = uuid4()
    mock_campaign = type("MockCampaign", (), {"id": campaign_id, "name": "Test Campaign"})
    mock_conversation = type("MockConversation", (), {"id": uuid4(), "campaign_id": campaign_id, "contact_id": contact_id})
    mock_campaign_repo.create.return_value = mock_campaign
    mock_conversation_repo.create.return_value = mock_conversation
    await campaign_service.create_campaign({"id": campaign_id, "name": "Test Campaign"})
    await conversation_service.start_conversation(campaign_id, contact_id, context={})

    # Conditional workflow: start -> [if foo==1 then branch1 else branch2]
    workflow_id = uuid4()
    step_start = type("MockStep", (), {"step_id": "start", "action": {"type": "noop"}, "transitions": [
        {"next_step_id": "branch1", "condition": "foo==1"},
        {"next_step_id": "branch2", "condition": "foo!=1"}
    ]})
    step_branch1 = type("MockStep", (), {"step_id": "branch1", "action": {"type": "send_message", "content": "Path 1"}, "transitions": []})
    step_branch2 = type("MockStep", (), {"step_id": "branch2", "action": {"type": "send_message", "content": "Path 2"}, "transitions": []})
    mock_workflow = type("MockWorkflow", (), {"steps": [step_start, step_branch1, step_branch2]})
    mock_workflow_repo.get.return_value = mock_workflow
    # Provide enough side effects for all calls: start (foo==1), branch1, start (foo!=1), branch2
    workflow_service._execute_action = AsyncMock(side_effect=[{}, {"message": "Path 1"}, {}, {"message": "Path 2"}])

    # Test foo==1 (should go to branch1)
    template_config = {"stages": [
        {"id": "start", "type": "decision", "decision": {"condition": "foo==1"}, "branches": [
            {"condition": "foo==1", "next_stage_id": "branch1"},
            {"condition": "foo!=1", "next_stage_id": "branch2"}
        ]},
        {"id": "branch1", "type": "message", "message": "Path 1"},
        {"id": "branch2", "type": "message", "message": "Path 2"}
    ]}
    result1 = await workflow_service.execute_step(workflow_id, "start", {"foo": 1, "template_config": template_config})
    assert result1["next_step_id"] == "branch1"
    result_branch1 = await workflow_service.execute_step(workflow_id, "branch1", {"foo": 1, "template_config": template_config})
    assert result_branch1["result"]["message"] == "Path 1"

    # Test foo!=1 (should go to branch2)
    result2 = await workflow_service.execute_step(workflow_id, "start", {"foo": 2, "template_config": template_config})
    assert result2["next_step_id"] == "branch2"
    result_branch2 = await workflow_service.execute_step(workflow_id, "branch2", {"foo": 2, "template_config": template_config})
    assert result_branch2["result"]["message"] == "Path 2"

@pytest.mark.asyncio
async def test_concurrent_campaigns_and_conversations():
    if not (CampaignService and ConversationService and WorkflowService):
        pytest.skip("Core services not available for integration test")

    mock_campaign_repo = AsyncMock()
    mock_conversation_repo = AsyncMock()
    mock_workflow_repo = AsyncMock()

    campaign_service = CampaignService(mock_campaign_repo)
    conversation_service = ConversationService(mock_conversation_repo)
    workflow_service = WorkflowService(mock_workflow_repo)

    # Simulate two campaigns and conversations
    campaign_ids = [uuid4(), uuid4()]
    contact_ids = [uuid4(), uuid4()]
    mock_campaigns = [type("MockCampaign", (), {"id": cid}) for cid in campaign_ids]
    mock_conversations = [type("MockConversation", (), {"id": uuid4(), "campaign_id": cid, "contact_id": coid}) for cid, coid in zip(campaign_ids, contact_ids)]
    mock_campaign_repo.create.side_effect = mock_campaigns
    mock_conversation_repo.create.side_effect = mock_conversations

    # Create both campaigns and conversations
    for i in range(2):
        c = await campaign_service.create_campaign({"id": campaign_ids[i], "name": "Test Campaign"})
        conv = await conversation_service.start_conversation(campaign_ids[i], contact_ids[i], context={})
        assert c.id == campaign_ids[i]
        assert conv.campaign_id == campaign_ids[i]
        assert conv.contact_id == contact_ids[i]

    # Setup workflow for both
    workflow_id = uuid4()
    step = type("MockStep", (), {"step_id": "start", "action": {"type": "send_message", "content": "Hi"}, "transitions": []})
    mock_workflow = type("MockWorkflow", (), {"steps": [step]})
    mock_workflow_repo.get.return_value = mock_workflow
    workflow_service._execute_action = AsyncMock(return_value={"message": "Hi"})

    # Execute for both conversations
    for i in range(2):
        template_config = {"stages": [
            {"id": "start", "type": "message", "message": "Hi"}
        ]}
        result = await workflow_service.execute_step(workflow_id, "start", {"template_config": template_config})
        assert result["result"]["message"] == "Hi"
